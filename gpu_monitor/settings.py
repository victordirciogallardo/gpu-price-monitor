import os
from dotenv import load_dotenv
load_dotenv()

BOT_NAME = 'gpu_monitor'
SPIDER_MODULES = ['gpu_monitor.spiders']
NEWSPIDER_MODULE = 'gpu_monitor.spiders'
ROBOTSTXT_OBEY = False
COOKIES_ENABLED = True
DOWNLOAD_TIMEOUT = 30
RETRY_TIMES = 3
RETRY_HTTP_CODES = [500, 502, 503, 504, 408, 429]
DOWNLOAD_DELAY = float(os.getenv('SCRAPER_DELAY', 2))
RANDOMIZE_DOWNLOAD_DELAY = True
CONCURRENT_REQUESTS = int(os.getenv('SCRAPER_CONCURRENT', 4))
CONCURRENT_REQUESTS_PER_DOMAIN = 2
DEFAULT_REQUEST_HEADERS = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'es-MX,es;q=0.9,en-US;q=0.8',
}
DOWNLOADER_MIDDLEWARES = {
    'gpu_monitor.middlewares.RotatingUserAgentMiddleware': 400,
    'scrapy.downloadermiddlewares.useragent.UserAgentMiddleware': None,
}
ITEM_PIPELINES = {
    'gpu_monitor.pipelines.AlertaPreciosPipeline': 200,
    'gpu_monitor.pipelines.MongoPipeline': 300,
}
LOG_LEVEL = 'INFO'
REQUEST_FINGERPRINTER_IMPLEMENTATION = '2.7'
TWISTED_REACTOR = 'twisted.internet.asyncioreactor.AsyncioSelectorReactor'
FEED_EXPORT_ENCODING = 'utf-8'
