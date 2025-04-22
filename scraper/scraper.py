#!/usr/bin/env python3
"""
Implements the web scraping logic to extract book data from the target website
and sends in a structured format for further processing.
"""
import os
import asyncio
from urllib.parse import urljoin

import aiohttp
from bs4 import BeautifulSoup
import grpc

from scraper.config import BASE_URL, CONCURRENCY, PARSER_HOST
import bookparser_pb2 as pb
import bookparser_pb2_grpc as rpc
import logging

logger = logging.getLogger(__name__)
sem = asyncio.Semaphore(CONCURRENCY)


async def fetch(session: aiohttp.ClientSession, url: str) -> str:
    """Fetches the HTML content of a given URL."""
    async with sem:
        async with session.get(url) as resp:
            resp.raise_for_status()
            return await resp.text()


async def parse_and_send(
    session: aiohttp.ClientSession, stub: rpc.ParserStub, url: str
) -> None:
    """Parses book data from a page and sends it to the parser service."""
    html = await fetch(session, url)
    soup = BeautifulSoup(html, "html.parser")
    name = soup.select_one("div.product_main h1").text.strip()
    rows = {
        tr.th.text: tr.td.text.strip()
        for tr in soup.select("table.table.table-striped tr")
    }

    raw = pb.RawBook(
        name=name,
        upc=rows.get("UPC", "").strip(),
        price_excl_tax=rows.get("Price (excl. tax)", "").lstrip("£").strip(),
        tax=rows.get("Tax", "").lstrip("£").strip(),
        availability=rows.get("Availability", "").strip(),
        url=url,
    )

    try:
        parsed = await stub.ParseBook(raw)
        logger.info(f"Parser stored UPC={parsed.upc} Name={parsed.name}")
    except grpc.aio.AioRpcError as e:
        code = e.code()
        msg = e.details()
        # Validation errors are already logged by the parser, use debug logging here
        if code == grpc.StatusCode.INVALID_ARGUMENT:
            logger.debug(f"Invalid data at {url}: {msg}")
            return
        elif code == grpc.StatusCode.ALREADY_EXISTS:
            logger.debug(f"Duplicate UPC at {url}: {msg}")
            return
        else:
            logger.error(f"gRPC error at {url}: {code} {msg}")
            raise


async def process_page(
    session: aiohttp.ClientSession, stub: rpc.ParserStub, page_url: str
) -> None:
    """Processes a single page of book listings."""
    page_link = urljoin(BASE_URL, page_url)
    html = await fetch(session, page_link)
    soup = BeautifulSoup(html, "html.parser")
    links = [a["href"] for a in soup.select("article.product_pod h3 a")]
    tasks = [parse_and_send(session, stub, urljoin(page_link, link)) for link in links]
    await asyncio.gather(*tasks)


async def scrape() -> None:
    """Scrapes book data from the target website."""
    logger.info(f"Starting scrape of {BASE_URL} with concurrency {CONCURRENCY}.")
    async with grpc.aio.insecure_channel(PARSER_HOST) as channel:
        stub = rpc.ParserStub(channel)
        async with aiohttp.ClientSession() as session:
            html = await fetch(session, urljoin(BASE_URL, "index.html"))
            soup = BeautifulSoup(html, "html.parser")
            pager = soup.select_one("li.current")
            total_pages = int(pager.text.strip().split()[-1]) if pager else 1
            tasks = [
                process_page(
                    session,
                    stub,
                    "index.html" if i == 1 else f"catalogue/page-{i}.html",
                )
                for i in range(1, total_pages + 1)
            ]
            await asyncio.gather(*tasks)
    logger.info("Scrape complete; all data handled by parser service.")


if __name__ == "__main__":
    logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO").upper())
    asyncio.run(scrape())
