# 🖥️ GPU Price Monitor

Sistema automatizado de monitoreo de precios de tarjetas de video (GPUs) construido en Python. Extrae precios de CyberPuerta.mx cada 6 horas, los almacena en MongoDB con historial completo, y genera alertas automáticas cuando detecta caídas de precio mayores al 5%.

> Proyecto de portafolio orientado a demostrar habilidades de backend, scraping de nivel productivo y conversión de datos crudos en inteligencia accionable.

---

## ✨ Características

- **Scraping automatizado** — Spider de Scrapy con rotación de User-Agents, reintentos configurables y delay aleatorio para comportarse como un navegador real
- **Historial completo de precios** — Cada registro se almacena con timestamp en MongoDB, construyendo una serie de tiempo por producto
- **Alertas inteligentes** — Pipeline secundario analiza cada precio nuevo contra el último registrado y genera una alerta cuando la caída supera el 5%
- **Scheduler integrado** — APScheduler ejecuta el ciclo de scraping cada 6 horas de forma autónoma, sin intervención manual
- **CLI de consulta** — Herramienta de línea de comandos para inspeccionar el historial, ver alertas pendientes y obtener rankings de precios

---

## 🛠️ Stack técnico

| Componente | Tecnología |
|---|---|
| Web scraping | Scrapy 2.15 |
| Base de datos | MongoDB + PyMongo |
| Scheduler | APScheduler |
| Configuración | Python-dotenv |
| Orquestación | subprocess |
| Lenguaje | Python 3.10+ |

---

## 🏗️ Arquitectura

```
CyberPuerta.mx
      │
      ▼
┌─────────────────┐
│  Scrapy Spider  │  ← Rotación UA, reintentos, delay aleatorio
└────────┬────────┘
         │ GPUItem
         ▼
┌─────────────────────────────────────┐
│           Item Pipelines            │
│                                     │
│  1. AlertaPreciosPipeline (prioridad 200)  │
│     └─ Compara precio vs último en DB      │
│     └─ Inserta alerta si caída ≥ 5%        │
│                                     │
│  2. MongoPipeline (prioridad 300)   │
│     └─ Inserta documento con timestamp     │
└─────────────────────────────────────┘
         │
         ▼
┌─────────────────┐
│    MongoDB      │
│  ┌───────────┐  │
│  │  precios  │  │  ← Historial completo con timestamps
│  └───────────┘  │
│  ┌───────────┐  │
│  │  alertas  │  │  ← Bajadas de precio detectadas
│  └───────────┘  │
└─────────────────┘
         ▲
         │
┌─────────────────┐
│   APScheduler   │  ← Ejecuta el ciclo cada 6 horas
└─────────────────┘
```

---

## 📁 Estructura del proyecto

```
gpu_monitor/
├── gpu_monitor/
│   ├── spiders/
│   │   └── cyberpuerta_spider.py   # Spider principal
│   ├── items.py                     # Definición del modelo GPUItem
│   ├── middlewares.py               # Rotación de User-Agents
│   ├── pipelines.py                 # MongoPipeline + AlertaPreciosPipeline
│   └── settings.py                  # Configuración de Scrapy
├── scraping.py                      # Scheduler (APScheduler)
├── scrapy.cfg
├── .env                             # Variables de entorno (no incluido en repo)
├── .gitignore
└── README.md
```

---

## ⚙️ Instalación

### Prerrequisitos

- Python 3.10 o superior
- MongoDB 6.0 o superior corriendo en `localhost:27017`

### 1. Clonar el repositorio

```bash
git clone https://github.com/victordirciogallardo/gpu-price-monitor.git
cd gpu-price-monitor
```

### 2. Instalar dependencias

```bash
pip install scrapy pymongo python-dotenv apscheduler
```

### 3. Configurar variables de entorno

Crea un archivo `.env` en la raíz del proyecto:

```env
MONGO_URI=mongodb://localhost:27017
MONGO_DB=gpu_monitor
SCRAPER_DELAY=2
SCRAPER_CONCURRENT=4
SCHEDULE_INTERVAL_HOURS=6
```

### 4. Verificar que MongoDB esté corriendo

```bash
# Windows
Get-Service -Name MongoDB

# Linux / macOS
sudo systemctl status mongod
```

---

## 🚀 Uso

### Ejecutar el spider una vez

```bash
scrapy crawl cyberpuerta
```

### Iniciar el scheduler automático

```bash
python scraping.py
```

El scheduler ejecutará el spider inmediatamente y luego cada 6 horas de forma automática. Para detenerlo: `Ctrl+C`.

---

## 📊 Modelo de datos

### Colección `precios`

```json
{
  "_id": "ObjectId(...)",
  "nombre": "Tarjeta de Video MSI NVIDIA GeForce RTX 5090 Lightning Z, 32GB...",
  "sku": "MSI-RTX5090-LZ",
  "marca": "NVIDIA",
  "modelo": "RTX 5090",
  "precio_actual": 112839.0,
  "precio_antes": null,
  "descuento_pct": 0.0,
  "en_stock": true,
  "tienda": "cyberpuerta",
  "url": "https://www.cyberpuerta.mx/...",
  "imagen_url": "https://...",
  "timestamp": "2026-05-07T02:43:04Z",
  "fecha_str": "2026-05-07 02:43 UTC"
}
```

### Colección `alertas`

```json
{
  "_id": "ObjectId(...)",
  "tipo": "BAJA_PRECIO",
  "sku": "MSI-RTX5070-V3X",
  "nombre": "Tarjeta de Video MSI NVIDIA GeForce RTX 5070...",
  "tienda": "cyberpuerta",
  "precio_anterior": 115000.0,
  "precio_nuevo": 14659.0,
  "cambio_pct": -87.2,
  "url": "https://www.cyberpuerta.mx/...",
  "timestamp": "2026-05-07T02:43:08Z",
  "revisada": false
}
```

---

## 🔧 Configuración avanzada

Todas las variables de comportamiento del scraper se controlan desde `.env`:

| Variable | Default | Descripción |
|---|---|---|
| `MONGO_URI` | `mongodb://localhost:27017` | URI de conexión a MongoDB |
| `MONGO_DB` | `gpu_monitor` | Nombre de la base de datos |
| `SCRAPER_DELAY` | `2` | Delay en segundos entre requests |
| `SCRAPER_CONCURRENT` | `4` | Requests concurrentes máximos |
| `SCHEDULE_INTERVAL_HOURS` | `6` | Intervalo del scheduler en horas |

---

## 🧱 Decisiones de diseño

**¿Por qué Scrapy y no requests/BeautifulSoup?**
Scrapy provee middlewares, reintentos, manejo de cookies, throttling y logging de forma nativa. Para un sistema productivo que corre desatendido, esta infraestructura es esencial.

**¿Por qué MongoDB y no SQL?**
El esquema de un producto puede cambiar (nuevos campos, campos opcionales) y el historial de precios es naturalmente una colección de documentos con timestamp. MongoDB encaja mejor que una tabla relacional rígida.

**¿Por qué dos pipelines separados?**
Separación de responsabilidades: `AlertaPreciosPipeline` detecta movimientos de precio antes de que el nuevo precio se persista, garantizando que la comparación sea siempre contra el último precio real almacenado.

---

## 📄 Licencia

MIT License — libre para uso personal y comercial.
