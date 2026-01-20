"""Input validation utilities."""

import re


def validate_stock_symbol(symbol: str) -> bool:
    """
    Validate stock symbol format.

    Args:
        symbol: Stock ticker symbol to validate

    Returns:
        True if valid, False otherwise
    """
    if not symbol:
        return False
    # Allow 1-5 uppercase letters, with optional class suffix (e.g., BRK.A, BRK-B)
    pattern = r"^[A-Z]{1,5}([.-][A-Z]{1,2})?$"
    return bool(re.match(pattern, symbol.upper().strip()))
