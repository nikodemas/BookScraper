#!/usr/bin/env python3
"""
Implements the gRPC parser service, which validates and processes book data
received from the scraper and stores it in a JSONL file.
"""
import asyncio
import json
import logging
import re

import grpc

import bookparser_pb2 as pb
import bookparser_pb2_grpc as rpc
from parser_service.config import GRPC_PORT, OUTPUT_FILE
from parser_service.validators import validate_record, record_is_duplicate

logger = logging.getLogger(__name__)

AVAIL_PATTERN = re.compile(r"\((\d+) available\)")

UPC_SEEN = set()

if OUTPUT_FILE.exists():
    try:
        with OUTPUT_FILE.open("r", encoding="utf-8") as f:
            for line in f:
                try:
                    rec = json.loads(line)
                    UPC_SEEN.add(rec["UPC"])
                except json.JSONDecodeError:
                    continue
    except Exception as e:
        logger.warning(f"Failed to load existing JSONL: {e}")


def store_record(raw: dict) -> None:
    """Stores a validated record in the output file."""
    with OUTPUT_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(raw, ensure_ascii=False) + "\n")
    UPC_SEEN.add(raw["UPC"])


class ParserServicer(rpc.ParserServicer):
    async def ParseBook(self, request, context) -> pb.ParsedBook | None:
        """Parses, validates and stores book data from the request."""
        avail_match = AVAIL_PATTERN.search(request.availability)
        if not avail_match:
            logger.warning(f"Could not parse availability: '{request.availability}'")
            await context.abort(
                grpc.StatusCode.INVALID_ARGUMENT, "invalid availability"
            )
            return
        availability = int(avail_match.group(1))

        try:
            price_excl = float(request.price_excl_tax)
            tax = float(request.tax)
        except ValueError:
            logger.warning(
                f"Invalid price/tax: '{request.price_excl_tax}', '{request.tax}'"
            )
            await context.abort(
                grpc.StatusCode.INVALID_ARGUMENT, "invalid price or tax"
            )
            return
        raw = {
            "Name": request.name,
            "UPC": request.upc,
            "Price_excl_tax": price_excl,
            "Tax": tax,
            "Availability": availability,
            "URL": request.url,
        }

        if not validate_record(raw):
            logger.warning(f"Validation failed for UPC={raw['UPC']}")
            await context.abort(grpc.StatusCode.INVALID_ARGUMENT, "validation failed")
            return
        if record_is_duplicate(raw["UPC"], UPC_SEEN):
            logger.warning(f"Duplicate UPC={raw['UPC']}, skipping")
            await context.abort(grpc.StatusCode.ALREADY_EXISTS, "duplicate UPC")
            return

        try:
            store_record(raw)
            logger.info(f"Stored UPC={raw['UPC']} Name={raw['Name']}")
        except Exception as e:
            logger.warning(f"Storage error for UPC={raw['UPC']}: {e}")
            await context.abort(grpc.StatusCode.INTERNAL, "storage error")
            return

        return pb.ParsedBook(
            name=raw["Name"],
            upc=raw["UPC"],
            price_excl_tax=raw["Price_excl_tax"],
            tax=raw["Tax"],
            availability=raw["Availability"],
            url=raw["URL"],
        )


async def serve() -> None:
    """Starts the gRPC server for the parser service."""
    server = grpc.aio.server()
    rpc.add_ParserServicer_to_server(ParserServicer(), server)
    listen_addr = f"[::]:{GRPC_PORT}"
    server.add_insecure_port(listen_addr)
    await server.start()
    logger.info(f"gRPC Parser service listening on {listen_addr}")
    await server.wait_for_termination()


if __name__ == "__main__":
    asyncio.run(serve())
