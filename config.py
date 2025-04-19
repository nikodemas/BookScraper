import os
from pathlib import Path
from datetime import date
import logging

BASE_URL = os.getenv("BASE_URL", "https://books.toscrape.com/")
OUTPUT_DIR = Path(os.getenv("OUTPUT_DIR", "data"))
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
CONCURRENCY = int(os.getenv("CONCURRENCY", "5"))

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

TODAY = date.today().isoformat()
OUTPUT_FILE = OUTPUT_DIR / f"books_{TODAY}.json"

logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
