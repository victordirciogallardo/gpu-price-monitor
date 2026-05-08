from datetime import datetime, timezone
from pymongo import MongoClient, ASCENDING, DESCENDING
import logging, os
from dotenv import load_dotenv
load_dotenv()

logger = logging.getLogger(__name__)

class MongoPipeline:
    collection_name = 'precios'

    def open_spider(self, spider):
        uri = os.getenv('MONGO_URI', 'mongodb://localhost:27017')
        db_name = os.getenv('MONGO_DB', 'gpu_monitor')
        self.client = MongoClient(uri, serverSelectionTimeoutMS=5000)
        self.client.admin.command('ping')
        self.db = self.client[db_name]
        self.col = self.db[self.collection_name]
        self.col.create_index([('modelo', ASCENDING), ('tienda', ASCENDING)])
        self.col.create_index([('timestamp', DESCENDING)])
        logger.info(f'MongoDB conectado: {db_name}')

    def close_spider(self, spider):
        self.client.close()

    def process_item(self, item, spider):
        now = datetime.now(timezone.utc)
        doc = dict(item)
        doc['timestamp'] = now
        doc['fecha_str'] = now.strftime('%Y-%m-%d %H:%M UTC')
        if item.get('precio_antes') and item.get('precio_actual'):
            antes = float(item['precio_antes'])
            actual = float(item['precio_actual'])
            doc['descuento_pct'] = round((1 - actual/antes)*100, 1) if antes > actual > 0 else 0.0
        else:
            doc['descuento_pct'] = 0.0
        self.col.insert_one(doc)
        logger.info(f"Guardado: {item.get('nombre','?')} | {item.get('precio_actual','?')}")
        return item

class AlertaPreciosPipeline:
    UMBRAL_ALERTA = 5.0

    def open_spider(self, spider):
        uri = os.getenv('MONGO_URI', 'mongodb://localhost:27017')
        self.client = MongoClient(uri)
        db = self.client[os.getenv('MONGO_DB', 'gpu_monitor')]
        self.precios_col = db['precios']
        self.alertas_col = db['alertas']

    def close_spider(self, spider):
        self.client.close()

    def process_item(self, item, spider):
        if not item.get('sku') or not item.get('precio_actual'):
            return item
        ultimo = self.precios_col.find_one(
            {'sku': item['sku'], 'tienda': item['tienda']},
            sort=[('timestamp', -1)]
        )
        if ultimo and ultimo.get('precio_actual'):
            ant = float(ultimo['precio_actual'])
            nvo = float(item['precio_actual'])
            if ant > 0:
                cambio = ((nvo - ant) / ant) * 100
                if cambio <= -self.UMBRAL_ALERTA:
                    self.alertas_col.insert_one({
                        'tipo': 'BAJA_PRECIO',
                        'sku': item['sku'],
                        'nombre': item.get('nombre'),
                        'tienda': item.get('tienda'),
                        'precio_anterior': ant,
                        'precio_nuevo': nvo,
                        'cambio_pct': round(cambio, 1),
                        'url': item.get('url'),
                        'timestamp': datetime.now(timezone.utc),
                        'revisada': False,
                    })
                    logger.warning(f"ALERTA: {item.get('nombre','?')} bajo {cambio:.1f}%")
        return item
