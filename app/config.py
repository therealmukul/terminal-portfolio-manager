"""Application configuration using Pydantic settings."""

from typing import List, Optional

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

    # Email/Newsletter Configuration
    smtp_host: str = Field(
        default="smtp.gmail.com", description="SMTP server host"
    )
    smtp_port: int = Field(
        default=587, description="SMTP server port"
    )
    smtp_username: Optional[str] = Field(
        default=None, description="SMTP username (email address)"
    )
    smtp_password: Optional[str] = Field(
        default=None, description="SMTP password or app password"
    )
    newsletter_sender_email: Optional[str] = Field(
        default=None, description="Sender email address for newsletter"
    )
    newsletter_sender_name: str = Field(
        default="Portfolio Manager", description="Sender name for newsletter"
    )
    newsletter_recipients: Optional[str] = Field(
        default=None, description="Comma-separated list of recipient email addresses"
    )
    newsletter_schedule_morning: str = Field(
        default="08:00", description="Morning newsletter time (HH:MM)"
    )
    newsletter_schedule_evening: str = Field(
        default="17:30", description="Evening newsletter time (HH:MM)"
    )

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
    }

    def get_newsletter_recipients(self) -> List[str]:
        """Parse newsletter recipients from comma-separated string."""
        if not self.newsletter_recipients:
            return []
        return [email.strip() for email in self.newsletter_recipients.split(",") if email.strip()]


def get_settings() -> Settings:
    """Get application settings (can be used for dependency injection)."""
    return Settings()
