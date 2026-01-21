"""Custom exceptions for the stock analysis agent."""


class StockAgentError(Exception):
    """Base exception for stock agent."""

    pass


class StockNotFoundError(StockAgentError):
    """Raised when a stock symbol is not found."""

    pass


class DataFetchError(StockAgentError):
    """Raised when data fetching fails."""

    pass


class AIServiceError(StockAgentError):
    """Raised when AI service fails."""

    pass


class RateLimitExceededError(StockAgentError):
    """Raised when rate limit is exceeded."""

    pass


class PortfolioError(StockAgentError):
    """Base exception for portfolio operations."""

    pass


class PositionNotFoundError(PortfolioError):
    """Raised when a position is not found."""

    pass


class InvalidPositionError(PortfolioError):
    """Raised when position data is invalid."""

    pass


class EmailServiceError(StockAgentError):
    """Raised when email service fails."""

    pass


class NewsletterError(StockAgentError):
    """Raised when newsletter generation or sending fails."""

    pass
