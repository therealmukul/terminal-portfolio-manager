"""Portfolio data models."""

from __future__ import annotations

from datetime import date, datetime
from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


class Position(BaseModel):
    """A single position (tax lot) in the portfolio."""

    id: Optional[int] = None
    symbol: str
    shares: float = Field(gt=0, description="Number of shares")
    purchase_price: float = Field(gt=0, description="Price per share at purchase")
    purchase_date: date
    notes: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    # Computed fields (populated by service)
    current_price: Optional[float] = None
    current_value: Optional[float] = None
    cost_basis: Optional[float] = None
    unrealized_gain: Optional[float] = None
    unrealized_gain_pct: Optional[float] = None
    day_change: Optional[float] = None
    day_change_pct: Optional[float] = None

    @field_validator("symbol")
    @classmethod
    def uppercase_symbol(cls, v: str) -> str:
        return v.upper().strip()

    @property
    def holding_period_days(self) -> int:
        """Days since purchase."""
        return (date.today() - self.purchase_date).days

    @property
    def is_long_term(self) -> bool:
        """True if held for more than 1 year (long-term capital gains)."""
        return self.holding_period_days > 365


class AggregatedPosition(BaseModel):
    """Aggregated view of all lots for a single symbol."""

    symbol: str
    total_shares: float
    total_cost_basis: float
    average_cost: float
    current_price: Optional[float] = None
    current_value: Optional[float] = None
    unrealized_gain: Optional[float] = None
    unrealized_gain_pct: Optional[float] = None
    weight_pct: Optional[float] = None  # Portfolio allocation percentage
    sector: Optional[str] = None
    industry: Optional[str] = None
    lots: List[Position] = Field(default_factory=list)


class Portfolio(BaseModel):
    """Complete portfolio with all positions and summary metrics."""

    positions: List[Position] = Field(default_factory=list)
    aggregated: List[AggregatedPosition] = Field(default_factory=list)

    # Summary metrics
    total_cost_basis: float = 0.0
    total_current_value: float = 0.0
    total_unrealized_gain: float = 0.0
    total_unrealized_gain_pct: float = 0.0
    total_day_change: float = 0.0
    total_day_change_pct: float = 0.0

    # Portfolio stats
    num_positions: int = 0
    num_symbols: int = 0

    # Sector allocation
    sector_allocation: Dict[str, float] = Field(default_factory=dict)

    last_updated: datetime = Field(default_factory=datetime.now)


class InsightSeverity(str, Enum):
    """Severity level for portfolio insights."""

    INFO = "info"
    WARNING = "warning"
    ALERT = "alert"
    ACTION_REQUIRED = "action_required"


class InsightCategory(str, Enum):
    """Category of portfolio insight."""

    REBALANCING = "rebalancing"
    RISK = "risk"
    TAX = "tax"
    OPPORTUNITY = "opportunity"
    GENERAL = "general"


class PortfolioInsight(BaseModel):
    """A single AI-generated portfolio insight."""

    category: InsightCategory
    severity: InsightSeverity
    title: str
    description: str
    affected_symbols: List[str] = Field(default_factory=list)
    recommended_action: Optional[str] = None
    action_urgency: Optional[str] = None  # immediate, this_week, this_month, when_convenient


class PortfolioAnalysis(BaseModel):
    """Complete AI analysis of the portfolio."""

    summary: str = Field(description="Executive summary of portfolio health")

    # Rebalancing insights
    rebalancing_insights: List[PortfolioInsight] = Field(default_factory=list)
    target_allocation_suggestion: Optional[Dict[str, float]] = None

    # Risk analysis
    risk_insights: List[PortfolioInsight] = Field(default_factory=list)
    concentration_risk_score: Optional[str] = None  # low, medium, high
    diversification_score: Optional[str] = None  # poor, fair, good, excellent

    # Tax optimization
    tax_insights: List[PortfolioInsight] = Field(default_factory=list)
    tax_loss_harvesting_opportunities: List[str] = Field(default_factory=list)
    wash_sale_warnings: List[str] = Field(default_factory=list)

    # Action recommendations
    action_items: List[PortfolioInsight] = Field(default_factory=list)
    hold_recommendations: List[str] = Field(default_factory=list)

    # Overall assessment
    overall_health: str = Field(default="", description="Overall portfolio health")
    confidence_level: Optional[str] = None  # low, medium, high

    disclaimer: str = Field(
        default="This is AI-generated analysis for educational purposes only. "
        "Consult a financial advisor before making investment decisions.",
        description="Legal disclaimer",
    )


class PortfolioSnapshot(BaseModel):
    """A point-in-time snapshot of portfolio value."""

    id: Optional[int] = None
    snapshot_date: date
    total_value: float
    total_cost_basis: float
    total_gain: float
    total_gain_pct: float
    num_positions: int
    created_at: Optional[datetime] = None


class PortfolioHistory(BaseModel):
    """Historical portfolio performance data."""

    snapshots: List[PortfolioSnapshot] = Field(default_factory=list)

    # Summary metrics
    earliest_date: Optional[date] = None
    latest_date: Optional[date] = None
    starting_value: Optional[float] = None
    current_value: Optional[float] = None
    total_change: Optional[float] = None
    total_change_pct: Optional[float] = None

    # Performance metrics
    high_value: Optional[float] = None
    high_date: Optional[date] = None
    low_value: Optional[float] = None
    low_date: Optional[date] = None


class HoldingPerformance(BaseModel):
    """Performance metrics for a single holding."""

    symbol: str
    current_value: float
    cost_basis: float
    unrealized_gain: float
    unrealized_gain_pct: float
    weight_pct: float  # Portfolio weight
    contribution_pct: float  # Contribution to total portfolio gain/loss
    sector: Optional[str] = None


class PortfolioPerformance(BaseModel):
    """Portfolio performance breakdown by holdings."""

    holdings: List[HoldingPerformance] = Field(default_factory=list)

    # Top/bottom performers
    top_gainers: List[HoldingPerformance] = Field(default_factory=list)
    top_losers: List[HoldingPerformance] = Field(default_factory=list)

    # Summary
    total_value: float = 0.0
    total_cost_basis: float = 0.0
    total_gain: float = 0.0
    total_gain_pct: float = 0.0

    # Sector performance
    sector_performance: Dict[str, float] = Field(default_factory=dict)
