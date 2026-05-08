import scrapy

class GPUItem(scrapy.Item):
    nombre        = scrapy.Field()
    sku           = scrapy.Field()
    marca         = scrapy.Field()
    modelo        = scrapy.Field()
    precio_actual = scrapy.Field()
    precio_antes  = scrapy.Field()
    descuento_pct = scrapy.Field()
    en_stock      = scrapy.Field()
    unidades      = scrapy.Field()
    tienda        = scrapy.Field()
    url           = scrapy.Field()
    imagen_url    = scrapy.Field()
    timestamp     = scrapy.Field()
    fecha_str     = scrapy.Field()
