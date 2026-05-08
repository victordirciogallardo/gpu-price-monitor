"""
Scheduler para el GPU Price Monitor.
Corre los spiders automáticamente cada N horas (default: 6).

Uso:
    python scheduler.py              # Corre ahora + cada 6h
    python scheduler.py --now        # Solo corre una vez y termina
    python scheduler.py --horas 12   # Intervalo personalizado
"""
import os
import sys
import logging
import argparse
from datetime import datetime, timezone
from subprocess import run as sp_run
from pathlib import Path

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.interval import IntervalTrigger
from dotenv import load_dotenv

load_dotenv()


def encontrar_proyecto_scrapy() -> Path:
    """
    Busca automáticamente la carpeta que contiene scrapy.cfg.
    Prueba el mismo directorio del script, subcarpetas comunes y el cwd.
    """
    candidatos = [
        Path(__file__).parent,                    # Mismo lugar que scheduler.py
        Path(__file__).parent / "gpu_monitor",    # Subcarpeta gpu_monitor/
        Path.cwd(),                               # Directorio de trabajo actual
        Path.cwd() / "gpu_monitor",               # Subcarpeta desde cwd
    ]
    for ruta in candidatos:
        if (ruta / "scrapy.cfg").exists():
            return ruta

    rutas_str = "\n  ".join(str(r) for r in candidatos)
    raise FileNotFoundError(
        f"\n❌ No se encontró scrapy.cfg en ninguna de estas rutas:\n  {rutas_str}\n"
        f"Asegúrate de que scrapy.cfg esté en la misma carpeta que scheduler.py."
    ) 


# ── Detectar proyecto ANTES de configurar logging (para la ruta del log) ──────
BASE_DIR = encontrar_proyecto_scrapy()
LOGS_DIR = BASE_DIR / "logs"
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)

# ── Configuración de logging ───────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [SCHEDULER] %(levelname)s: %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(str(LOGS_DIR / "scheduler.log"), encoding="utf-8"),
    ],
)
logger = logging.getLogger(__name__)
logger.info(f"📁 Proyecto Scrapy detectado en: {BASE_DIR}")

# Spiders a ejecutar en cada ciclo
SPIDERS = [
    "cyberpuerta",
    # "newegg",     # Descomenta cuando agregues ese spider
]


def ejecutar_spiders():
    """Lanza todos los spiders de Scrapy secuencialmente."""
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    logger.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    logger.info(f"🚀 Iniciando ciclo de scraping — {ts}")

    resultados = {}

    for spider in SPIDERS:
        logger.info(f"  🕷  Ejecutando spider: {spider}")
        logfile = str(LOGS_DIR / f"scrapy_{spider}_{ts}.log")

        resultado = sp_run(
            [sys.executable, "-m", "scrapy", "crawl", spider, "--logfile", logfile],
            cwd=str(BASE_DIR),
            capture_output=True,
            text=True,
        )

        if resultado.returncode == 0:
            logger.info(f"  ✅ {spider} completado exitosamente")
            resultados[spider] = "OK"
        else:
            logger.error(f"  ❌ {spider} falló (código {resultado.returncode})")
            # Mostrar stdout Y stderr para diagnóstico claro
            if resultado.stdout and resultado.stdout.strip():
                logger.error(f"     STDOUT: {resultado.stdout.strip()[:400]}")
            if resultado.stderr and resultado.stderr.strip():
                logger.error(f"     STDERR: {resultado.stderr.strip()[:400]}")
            resultados[spider] = "ERROR"

    logger.info(f"📊 Resumen: {resultados}")
    logger.info("⏰ Próxima ejecución programada automáticamente")
    logger.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")


def main():
    parser = argparse.ArgumentParser(description="GPU Price Monitor Scheduler")
    parser.add_argument("--now", action="store_true", help="Ejecutar una vez y salir")
    parser.add_argument("--horas", type=float, default=None, help="Intervalo en horas")
    args = parser.parse_args()

    intervalo = args.horas or float(os.getenv("SCHEDULE_INTERVAL_HOURS", 6))

    if args.now:
        logger.info("Modo --now: ejecutando una vez y terminando.")
        ejecutar_spiders()
        return

    logger.info(f"🕐 Scheduler iniciado — intervalo: {intervalo}h")
    logger.info(f"   Primera ejecución: inmediata")
    logger.info(f"   Subsiguientes: cada {intervalo} horas")
    logger.info(f"   Para detener: Ctrl+C")

    scheduler = BlockingScheduler(timezone="America/Mexico_City")
    scheduler.add_job(
        ejecutar_spiders,
        trigger=IntervalTrigger(hours=intervalo),
        id="gpu_scraper",
        name="GPU Price Monitor",
        next_run_time=datetime.now(),
    )

    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("⛔ Scheduler detenido por el usuario.")
        scheduler.shutdown()


if __name__ == "__main__":
    main()