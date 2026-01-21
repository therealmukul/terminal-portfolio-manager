"""Application configuration using Pydantic settings."""

from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application configuration with environment variable support."""

    # API Keys (optional - only required if using AI features)
    anthropic_api_key: Optional[str] = Field(
        default=None, description="Anthropic API key for Claude"
    )

    # Claude Configuration
    claude_model: str = Field(
        default="claude-sonnet-4-20250514", description="Claude model to use"
    )
    claude_max_tokens: int = Field(
        default=4096, description="Max tokens for Claude responses"
    )

    # Rate Limiting
    yfinance_requests_per_minute: int = Field(
        default=60, description="yfinance rate limit"
    )
    claude_requests_per_minute: int = Field(
        default=50, description="Claude API rate limit"
    )

    # Portfolio Configuration
    portfolio_db_path: str = Field(
        default="data/portfolio.db",
        description="Path to SQLite database for portfolio storage",
    )

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
    }


def get_settings() -> Settings:
    """Get application settings (can be used for dependency injection)."""
    return Settings()
