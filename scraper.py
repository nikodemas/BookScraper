#!/usr/bin/env python3

import asyncio
import json
import re
from urllib.parse import urljoin

import aiohttp
from bs4 import BeautifulSoup
import logging

from config import BASE_URL, OUTPUT_FILE, CONCURRENCY, TODAY

logger = logging.getLogger(__name__)

sem = asyncio.Semaphore(CONCURRENCY)

# Patterns
AVAIL_PATTERN = re.compile(r"\((\d+) available\)")
UPC_PATTERN = re.compile(
    r"^[A-Za-z0-9]{16}$"
)  # UPC must be exactly 16 alphanumeric characters


def validate_name(name: str) -> bool:
    if not name:
        logger.warning("Invalid Name: empty string.")
        return False
    if len(name) > 256:
        logger.warning(f"Invalid Name: too long ({len(name)} chars).")
        return False
    return True


def validate_upc(upc: str) -> bool:
    if not upc:
        logger.warning("Invalid UPC: missing.")
        return False
    if not UPC_PATTERN.match(upc):
        logger.warning(
            f"Invalid UPC format or length: '{upc}' (must be 16 alphanumeric characters)."
        )
        return False
    return True


def validate_price_tax(value: float, field: str) -> bool:
    if value < 0:
        logger.warning(f"Invalid {field}: negative value {value}.")
        return False
    return True


def validate_availability(amount: int) -> bool:
    if amount < 0:
        logger.warning(f"Invalid Availability: negative amount {amount}.")
        return False
    return True


def validate_url(url: str) -> bool:
    if not url.startswith(BASE_URL):
        logger.warning(f"Invalid URL: outside base domain '{url}'.")
        return False
    return True


def validate_record(record: dict, existing_upcs: set) -> bool:
    if not (
        validate_name(record["Name"])
        and validate_upc(record["UPC"])
        and validate_price_tax(record["Price_excl_tax"], "Price_excl_tax")
        and validate_price_tax(record["Tax"], "Tax")
        and validate_availability(record["Availability"])
        and validate_url(record["URL"])
    ):
        return False
    if record["UPC"] in existing_upcs:
        logger.info(f"Duplicate UPC {record['UPC']}, skipping.")
        return False
    return True


async def fetch(session: aiohttp.ClientSession, url: str) -> str:
    async with sem:
        async with session.get(url) as resp:
            resp.raise_for_status()
            return await resp.text()


async def parse_book(
    session: aiohttp.ClientSession, url: str, existing_upcs: set
) -> dict | None:
    html = await fetch(session, url)
    soup = BeautifulSoup(html, "html.parser")
    name = soup.select_one("div.product_main h1").text.strip()
    rows = {
        tr.th.text: tr.td.text for tr in soup.select("table.table.table-striped tr")
    }

    upc = rows.get("UPC", "").strip()
    price_text = rows.get("Price (excl. tax)", "").lstrip("£").strip()
    tax_text = rows.get("Tax", "").lstrip("£").strip()
    availability_text = rows.get("Availability", "").strip()

    try:
        price_excl = float(price_text)
        tax = float(tax_text)
    except ValueError:
        logger.warning(f"Invalid price/tax values: '{price_text}', '{tax_text}'.")
        return None

    avail_match = AVAIL_PATTERN.search(availability_text)
    if not avail_match:
        logger.warning(f"Could not parse availability from '{availability_text}'.")
        return None
    availability = int(avail_match.group(1))

    record = {
        "Name": name,
        "UPC": upc,
        "Price_excl_tax": price_excl,
        "Tax": tax,
        "Availability": availability,
        "URL": url,
    }

    if not validate_record(record, existing_upcs):
        return None
    return record


async def parse_book_and_store(
    session: aiohttp.ClientSession, url: str, existing_upcs: set, data: list
) -> None:
    item = await parse_book(session, url, existing_upcs)
    if item:
        data.append(item)
        existing_upcs.add(item["UPC"])
        logger.info(f"Added {item['Name']}")


async def process_page(
    session: aiohttp.ClientSession, page_url: str, existing_upcs: set, data: list
) -> None:
    page_link = urljoin(BASE_URL, page_url)
    html = await fetch(session, page_link)
    soup = BeautifulSoup(html, "html.parser")
    links = [a["href"] for a in soup.select("article.product_pod h3 a")]
    tasks = [
        parse_book_and_store(session, urljoin(page_link, link), existing_upcs, data)
        for link in links
    ]
    await asyncio.gather(*tasks)


async def scrape() -> None:
    data: list = []
    existing_upcs: set = set()
    async with aiohttp.ClientSession() as session:
        html = await fetch(session, urljoin(BASE_URL, "index.html"))
        soup = BeautifulSoup(html, "html.parser")
        pager = soup.select_one("li.current")
        total_pages = int(pager.text.strip().split()[-1]) if pager else 1
        tasks = [
            process_page(
                session,
                "index.html" if i == 1 else f"catalogue/page-{i}.html",
                existing_upcs,
                data,
            )
            for i in range(1, total_pages + 1)
        ]
        await asyncio.gather(*tasks)

    with OUTPUT_FILE.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    logger.info(f"Scrape complete for {TODAY}: {len(data)} items saved.")


def main() -> None:
    asyncio.run(scrape())


if __name__ == "__main__":
    main()
