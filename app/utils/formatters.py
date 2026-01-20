"""Number and currency formatting utilities."""

from typing import Optional


def format_currency(value: Optional[float], currency: str = "USD") -> str:
    """
    Format a value as currency.

    Args:
        value: The numeric value to format
        currency: Currency code (default: USD)

    Returns:
        Formatted currency string
    """
    if value is None:
        return "N/A"

    symbols = {"USD": "$", "EUR": "€", "GBP": "£", "JPY": "¥"}
    symbol = symbols.get(currency, "$")

    if abs(value) >= 1:
        return f"{symbol}{value:,.2f}"
    else:
        return f"{symbol}{value:.4f}"


def format_percentage(value: Optional[float], decimal_places: int = 2) -> str:
    """
    Format a value as percentage.

    Args:
        value: The numeric value to format (0.15 = 15%)
        decimal_places: Number of decimal places

    Returns:
        Formatted percentage string
    """
    if value is None:
        return "N/A"

    return f"{value * 100:.{decimal_places}f}%"


def format_large_number(value: Optional[float]) -> str:
    """
    Format large numbers with suffixes (K, M, B, T).

    Args:
        value: The numeric value to format

    Returns:
        Formatted string with appropriate suffix
    """
    if value is None:
        return "N/A"

    if value == 0:
        return "$0"

    is_negative = value < 0
    value = abs(value)

    suffixes = ["", "K", "M", "B", "T"]
    magnitude = 0

    while value >= 1000 and magnitude < len(suffixes) - 1:
        magnitude += 1
        value /= 1000

    formatted = f"${value:.2f}{suffixes[magnitude]}"
    return f"-{formatted}" if is_negative else formatted


def format_yield(value: Optional[float], decimal_places: int = 2) -> str:
    """
    Format a yield value that's already in percentage form.

    yfinance returns dividend yield as a percentage (0.41 = 0.41%, not 41%).

    Args:
        value: The numeric value already in percentage form
        decimal_places: Number of decimal places

    Returns:
        Formatted percentage string
    """
    if value is None:
        return "N/A"

    return f"{value:.{decimal_places}f}%"


def format_ratio(value: Optional[float], decimal_places: int = 2) -> str:
    """
    Format a ratio value.

    Args:
        value: The numeric value to format
        decimal_places: Number of decimal places

    Returns:
        Formatted ratio string
    """
    if value is None:
        return "N/A"

    return f"{value:.{decimal_places}f}"


def format_volume(value: Optional[int]) -> str:
    """
    Format trading volume with suffixes.

    Args:
        value: The volume value

    Returns:
        Formatted volume string
    """
    if value is None:
        return "N/A"

    if value >= 1_000_000_000:
        return f"{value / 1_000_000_000:.2f}B"
    elif value >= 1_000_000:
        return f"{value / 1_000_000:.2f}M"
    elif value >= 1_000:
        return f"{value / 1_000:.2f}K"
    else:
        return str(value)
