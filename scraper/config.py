"""
Reads configuration settings for the scraper from the environment
variables, including base URL and logging setup.
"""

import logging
import os

BASE_URL = os.getenv("BASE_URL", "https://books.toscrape.com/")
PARSER_HOST = os.getenv("PARSER_HOST", "localhost:50051")
CONCURRENCY = int(os.getenv("CONCURRENCY", "5"))

LOG_LEVEL = os.getenv("SCRAPER_LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
