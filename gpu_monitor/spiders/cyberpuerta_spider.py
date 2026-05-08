import re
import scrapy
from gpu_monitor.items import GPUItem

class CyberPuertaSpider(scrapy.Spider):
    name = 'cyberpuerta'
    allowed_domains = ['cyberpuerta.mx']
    start_urls = ['https://www.cyberpuerta.mx/Computo-Hardware/Componentes/Tarjetas-de-Video/']
    custom_settings = {'DOWNLOAD_DELAY': 3}

    GPU_MODELS = [
        'rtx 5090','rtx 5080','rtx 5070 ti','rtx 5070','rtx 5060',
        'rtx 4090','rtx 4080','rtx 4070 ti','rtx 4070 super','rtx 4070',
        'rtx 4060 ti','rtx 4060','rtx 3090','rtx 3080','rtx 3070','rtx 3060',
        'rx 9070 xt','rx 9070','rx 9060 xt',
        'rx 7900 xtx','rx 7900 xt','rx 7800 xt','rx 7700 xt','rx 7600',
        'arc b580','arc a770','arc a750',
    ]

    def parse(self, response):
        self.logger.info(f'Scraping: {response.url}')
        links = response.css('div[class*="cpd-product-card-catalog"] a[href*=".html"]::attr(href)').getall()
        vistos = set()
        count = 0
        for url in links:
            if url not in vistos and '/Por-Marca/' not in url:
                vistos.add(url)
                count += 1
                yield response.follow(url, callback=self.parse_producto)
        self.logger.info(f'Productos encontrados: {count}')
        nxt = response.css('a[class*=next]::attr(href)').get()
        if nxt:
            yield response.follow(nxt, callback=self.parse)

    def parse_producto(self, response):
        nombre = response.css('h1::text').get('').strip()
        if not nombre:
            return
        nl = nombre.lower()
        if not any(k in nl for k in ['tarjeta de video','geforce','radeon','arc','rtx','gtx','rx ']):
            return
        precios = [x.strip() for x in response.css('[class*="price"]::text').getall() if x.strip()]
        precio_actual = self._precio(precios[0] if precios else '')
        
        
        if not precio_actual:
            return
        precio_antes = self._precio(
            response.css('[class*=old-price]::text, [class*=price-old]::text').get('')
        )
        sku = response.css('[class*=sku]::text, [itemprop=sku]::text').get() or response.url.split('/')[-1][:30]
        stock_txt = response.css('[class*=stock]::text').get('').lower()
        en_stock = 'sin stock' not in stock_txt and 'agotado' not in stock_txt
        imagen = response.css('[class*=product-image] img::attr(src), [class*=main-image]::attr(src)').get()
        precio_fmt = f'{precio_actual:,.0f}'
        self.logger.info(f'OK: {nombre[:60]} | {precio_fmt} MXN')
        yield GPUItem(
            nombre=nombre, sku=sku.strip(),
            marca=self._marca(nl), modelo=self._modelo(nl),
            precio_actual=precio_actual, precio_antes=precio_antes,
            descuento_pct=None, en_stock=en_stock, unidades=None,
            tienda='cyberpuerta', url=response.url, imagen_url=imagen,
        )

    def _precio(self, t):
        limpio = re.sub(r'[^\d.]', '', t.replace(',', ''))
        try:
            v = float(limpio)
            return v if v > 0 else None
        except:
            return None

    def _marca(self, n):
        if any(k in n for k in ['nvidia','geforce','rtx','gtx']): return 'NVIDIA'
        if any(k in n for k in ['amd','radeon','rx ']): return 'AMD'
        if any(k in n for k in ['intel','arc']): return 'Intel'
        return 'Otra'

    def _modelo(self, n):
        for m in self.GPU_MODELS:
            if m in n: return m.upper()
        match = re.search(r'(rtx|gtx|rx|arc)\s*\d{3,4}(\s*(xt|ti|super|xtx))?', n)
        return match.group(0).upper().strip() if match else 'Desconocido'
