import logging
import os
from pathlib import Path

BASE_URL = os.getenv("BASE_URL", "https://books.toscrape.com/")
GRPC_PORT = int(os.getenv("GRPC_PORT", "50051"))

OUTPUT_DIR = Path(os.getenv("OUTPUT_DIR", "data"))
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_FILE = OUTPUT_DIR / f"books.json"

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
