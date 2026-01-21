"""Stock data models."""

from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class StockInfo(BaseModel):
    """Core stock information from Yahoo Finance."""

    symbol: str
    company_name: str
    sector: Optional[str] = None
    industry: Optional[str] = None
    currency: str = "USD"
    exchange: Optional[str] = None
    website: Optional[str] = None
    description: Optional[str] = None


class FundamentalData(BaseModel):
    """Fundamental analysis metrics."""

    # Valuation
    market_cap: Optional[float] = None
    pe_ratio: Optional[float] = None
    forward_pe: Optional[float] = None
    peg_ratio: Optional[float] = None
    price_to_book: Optional[float] = None
    price_to_sales: Optional[float] = None
    enterprise_value: Optional[float] = None

    # Profitability
    profit_margin: Optional[float] = None
    operating_margin: Optional[float] = None
    gross_margin: Optional[float] = None
    return_on_equity: Optional[float] = None
    return_on_assets: Optional[float] = None

    # Per Share Data
    eps: Optional[float] = None
    eps_forward: Optional[float] = None
    book_value: Optional[float] = None

    # Revenue & Growth
    revenue: Optional[float] = None
    revenue_per_share: Optional[float] = None
    revenue_growth: Optional[float] = None
    earnings_growth: Optional[float] = None
    quarterly_revenue_growth: Optional[float] = None
    quarterly_earnings_growth: Optional[float] = None

    # Financial Health
    total_debt: Optional[float] = None
    total_cash: Optional[float] = None
    debt_to_equity: Optional[float] = None
    current_ratio: Optional[float] = None
    quick_ratio: Optional[float] = None
    free_cash_flow: Optional[float] = None

    # Dividends
    dividend_yield: Optional[float] = None
    dividend_rate: Optional[float] = None
    payout_ratio: Optional[float] = None
    ex_dividend_date: Optional[datetime] = None


class EarningsData(BaseModel):
    """Earnings history and estimates."""

    quarterly_earnings: List[Dict] = Field(default_factory=list)
    annual_earnings: List[Dict] = Field(default_factory=list)
    next_earnings_date: Optional[datetime] = None


class StockAnalysis(BaseModel):
    """Complete stock analysis result."""

    info: StockInfo
    fundamentals: FundamentalData
    earnings: EarningsData = Field(default_factory=EarningsData)

    # Price data
    current_price: Optional[float] = None
    previous_close: Optional[float] = None
    open_price: Optional[float] = None
    day_low: Optional[float] = None
    day_high: Optional[float] = None
    fifty_two_week_high: Optional[float] = None
    fifty_two_week_low: Optional[float] = None

    # Volume
    volume: Optional[int] = None
    average_volume: Optional[int] = None

    # Analyst data
    analyst_rating: Optional[str] = None
    target_high_price: Optional[float] = None
    target_low_price: Optional[float] = None
    target_mean_price: Optional[float] = None
    number_of_analysts: Optional[int] = None

    # Metadata
    fetched_at: datetime = Field(default_factory=datetime.now)


class StockSearchResult(BaseModel):
    """A stock search result."""

    symbol: str
    name: str
    exchange: Optional[str] = None
    type: Optional[str] = None  # EQUITY, ETF, etc.


class NewsArticle(BaseModel):
    """A news article related to a stock."""

    title: str
    summary: Optional[str] = None
    publisher: str
    url: str
    published_at: datetime
    thumbnail_url: Optional[str] = None

    @property
    def time_ago(self) -> str:
        """Human-readable time since publication."""
        # Handle timezone-aware vs naive datetime comparison
        now = datetime.now()
        pub_time = self.published_at
        if pub_time.tzinfo is not None:
            pub_time = pub_time.replace(tzinfo=None)

        delta = now - pub_time
        if delta.days > 0:
            return f"{delta.days}d ago"
        hours = delta.seconds // 3600
        if hours > 0:
            return f"{hours}h ago"
        minutes = delta.seconds // 60
        return f"{minutes}m ago"
