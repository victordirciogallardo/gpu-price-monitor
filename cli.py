"""
GPU Monitor CLI
"""
import os, sys, argparse
from datetime import datetime, timezone
from pymongo import MongoClient, DESCENDING
from dotenv import load_dotenv

load_dotenv()

def get_db():
    uri = os.getenv('MONGO_URI', 'mongodb://localhost:27017')
    db_name = os.getenv('MONGO_DB', 'gpu_monitor')
    client = MongoClient(uri, serverSelectionTimeoutMS=5000)
    return client[db_name]

def fmt_precio(p):
    return f'${p:,.0f} MXN' if p else 'N/D'

def fmt_fecha(ts):
    if not ts: return 'N/D'
    if isinstance(ts, datetime):
        return ts.replace(tzinfo=timezone.utc).astimezone().strftime('%Y-%m-%d %H:%M')
    return str(ts)

def sep():
    print('─' * 70)

def cmd_stats(db):
    p = db['precios']
    a = db['alertas']
    total = p.count_documents({})
    skus = len(p.distinct('sku'))
    en_stock = len(p.distinct('sku', {'en_stock': True}))
    alertas = a.count_documents({})
    pendientes = a.count_documents({'revisada': False})
    ultimo = p.find_one(sort=[('timestamp', DESCENDING)])
    pmin = p.find_one({'en_stock': True}, sort=[('precio_actual', 1)])
    pmax = p.find_one({'en_stock': True}, sort=[('precio_actual', DESCENDING)])
    print('\n  Estadísticas del sistema')
    sep()
    print(f'  Registros totales:    {total:,}')
    print(f'  Productos unicos:     {skus:,}')
    print(f'  En stock:             {en_stock:,}')
    print(f'  Alertas totales:      {alertas:,}')
    print(f'  Alertas pendientes:   {pendientes:,}')
    print(f'  Ultimo scraping:      {fmt_fecha(ultimo.get("timestamp")) if ultimo else "N/D"}')
    if pmin: print(f'  GPU mas barata:       {fmt_precio(pmin.get("precio_actual"))} - {(pmin.get("nombre") or "")[:40]}')
    if pmax: print(f'  GPU mas cara:         {fmt_precio(pmax.get("precio_actual"))} - {(pmax.get("nombre") or "")[:40]}')
    sep()
    print()

def cmd_ranking(db, marca=None):
    p = db['precios']
    pipeline = [
        {'$sort': {'timestamp': DESCENDING}},
        {'$group': {'_id': '$sku', 'nombre': {'$first': '$nombre'}, 'marca': {'$first': '$marca'},
                    'modelo': {'$first': '$modelo'}, 'precio_actual': {'$first': '$precio_actual'},
                    'en_stock': {'$first': '$en_stock'}}},
        {'$match': {'en_stock': True, 'precio_actual': {'$gt': 0}}},
        {'$sort': {'precio_actual': 1}},
        {'$limit': 20},
    ]
    if marca:
        pipeline.insert(1, {'$match': {'marca': {'$regex': marca, '$options': 'i'}}})
    docs = list(p.aggregate(pipeline))
    if not docs:
        print('\n  Sin productos en stock.\n')
        return
    print(f'\n  Ranking de precios{"  - " + marca if marca else ""}')
    sep()
    print(f'  {"#":<4} {"Precio":>14}  {"Marca":<8} {"Modelo":<16} Nombre')
    sep()
    for i, d in enumerate(docs, 1):
        print(f'  {i:<4} {fmt_precio(d.get("precio_actual")):>14}  {d.get("marca","?"):<8} {d.get("modelo","?"):<16} {(d.get("nombre") or "")[:35]}')
    sep()
    print(f'  {len(docs)} producto(s)\n')

def cmd_historial(db, query):
    col = db['precios']
    r = {'$regex': query, '$options': 'i'}
    docs = list(col.find({'$or': [{'nombre': r}, {'modelo': r}]}, sort=[('timestamp', DESCENDING)], limit=20))
    if not docs:
        print(f'\n  Sin resultados para: "{query}"\n')
        return
    print(f'\n  Historial - "{query}"')
    sep()
    print(f'  {"Fecha":<18} {"Precio":>14}  Nombre')
    sep()
    for d in docs:
        print(f'  {fmt_fecha(d.get("timestamp")):<18} {fmt_precio(d.get("precio_actual")):>14}  {(d.get("nombre") or "")[:40]}')
    sep()
    print(f'  {len(docs)} registro(s)\n')

def cmd_alertas(db, solo_pendientes=True):
    col = db['alertas']
    filtro = {'revisada': False} if solo_pendientes else {}
    docs = list(col.find(filtro, sort=[('timestamp', DESCENDING)], limit=50))
    if not docs:
        print('\n  No hay alertas pendientes.\n')
        return
    print(f'\n  Alertas de bajada de precio')
    sep()
    for d in docs:
        print(f'\n  {fmt_fecha(d.get("timestamp"))}  {d.get("cambio_pct", 0):.1f}%')
        print(f'  {(d.get("nombre") or "")[:60]}')
        print(f'  {fmt_precio(d.get("precio_anterior"))}  ->  {fmt_precio(d.get("precio_nuevo"))}')
    sep()
    print(f'  {len(docs)} alerta(s)\n')
    if solo_pendientes:
        col.update_many({'_id': {'$in': [d["_id"] for d in docs]}}, {'$set': {'revisada': True}})

def main():
    parser = argparse.ArgumentParser(prog='cli.py', description='GPU Monitor CLI')
    sub = parser.add_subparsers(dest='cmd')
    sub.add_parser('stats', help='Estadisticas generales')
    r = sub.add_parser('ranking', help='Ranking de precios')
    r.add_argument('--marca', help='NVIDIA, AMD o Intel')
    h = sub.add_parser('historial', help='Historial de un producto')
    h.add_argument('query', help='Nombre o modelo a buscar')
    a = sub.add_parser('alertas', help='Alertas de bajada de precio')
    a.add_argument('--todas', action='store_true')
    args = parser.parse_args()
    if not args.cmd:
        parser.print_help()
        return
    try:
        db = get_db()
    except Exception as e:
        print(f'\n  Error conectando a MongoDB: {e}\n')
        sys.exit(1)
    if args.cmd == 'stats': cmd_stats(db)
    elif args.cmd == 'ranking': cmd_ranking(db, getattr(args, 'marca', None))
    elif args.cmd == 'historial': cmd_historial(db, args.query)
    elif args.cmd == 'alertas': cmd_alertas(db, solo_pendientes=not args.todas)

if __name__ == '__main__':
    main()