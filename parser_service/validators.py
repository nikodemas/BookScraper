"""
Contains validation functions for the parser service, including
record validation and duplicate detection logic.
"""

import re

from parser_service.config import BASE_URL
import logging

logger = logging.getLogger(__name__)

UPC_PATTERN = re.compile(
    r"^[A-Za-z0-9]{16}$"
)  # UPC must be exactly 16 alphanumeric characters


def validate_name(name: str) -> bool:
    """Validates that the name is non-empty and does not exceed 256 characters."""
    if not name:
        logger.info("Invalid Name: empty string.")
        return False
    if len(name) > 256:
        logger.info(f"Invalid Name: too long ({len(name)} chars).")
        return False
    return True


def validate_upc(upc: str) -> bool:
    """Validates that the UPC is non-empty and matches the required 16-character format."""
    if not upc:
        logger.info("Invalid UPC: missing.")
        return False
    if not UPC_PATTERN.match(upc):
        logger.info(
            f"Invalid UPC format or length: '{upc}' (must be 16 alphanumeric characters)."
        )
        return False
    return True


def validate_price_tax(value: float, field: str) -> bool:
    """Validates that the price or tax value is non-negative."""
    if value < 0:
        logger.info(f"Invalid {field}: negative value {value}.")
        return False
    return True


def validate_availability(amount: int) -> bool:
    """Validates that the availability amount is non-negative."""
    if amount < 0:
        logger.info(f"Invalid Availability: negative amount {amount}.")
        return False
    return True


def validate_url(url: str, base: str = BASE_URL) -> bool:
    """Validates that the URL starts with the specified base domain."""
    if not url.startswith(base):
        logger.info(f"Invalid URL: outside base domain '{url}'.")
        return False
    return True


def validate_record(record: dict) -> bool:
    """Validates all fields of a record using individual validation functions."""
    if not (
        validate_name(record["Name"])
        and validate_upc(record["UPC"])
        and validate_price_tax(record["Price_excl_tax"], "Price_excl_tax")
        and validate_price_tax(record["Tax"], "Tax")
        and validate_availability(record["Availability"])
        and validate_url(record["URL"])
    ):
        return False
    return True


def record_is_duplicate(upc: str, existing_upcs: set) -> bool:
    """Checks if the given UPC already exists in the set of existing UPCs."""
    if upc in existing_upcs:
        logger.info(f"Duplicate UPC {upc}.")
        return True
    return False
