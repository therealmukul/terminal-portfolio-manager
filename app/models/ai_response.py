"""AI response models for Claude-generated insights."""

from __future__ import annotations

from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class RecommendationType(str, Enum):
    """Stock recommendation types."""

    STRONG_BUY = "strong_buy"
    BUY = "buy"
    HOLD = "hold"
    SELL = "sell"
    STRONG_SELL = "strong_sell"


class AIInsight(BaseModel):
    """Claude-generated analysis insight."""

    summary: str = Field(description="Executive summary of the analysis")
    strengths: List[str] = Field(default_factory=list, description="Key strengths")
    weaknesses: List[str] = Field(default_factory=list, description="Key weaknesses")
    opportunities: List[str] = Field(
        default_factory=list, description="Growth opportunities"
    )
    risks: List[str] = Field(default_factory=list, description="Key risks")
    recommendation: Optional[RecommendationType] = Field(
        default=None, description="Overall recommendation"
    )
    confidence_level: Optional[str] = Field(
        default=None, description="Confidence in the analysis (low, medium, high)"
    )
    valuation_assessment: str = Field(
        default="", description="Assessment of current valuation"
    )
    key_metrics_analysis: str = Field(
        default="", description="Analysis of key financial metrics"
    )
    disclaimer: str = Field(
        default="This is AI-generated analysis for educational purposes only. Not financial advice.",
        description="Legal disclaimer",
    )


class NewsSentiment(str, Enum):
    """Sentiment classification for news."""

    VERY_BULLISH = "very_bullish"
    BULLISH = "bullish"
    NEUTRAL = "neutral"
    BEARISH = "bearish"
    VERY_BEARISH = "very_bearish"


class ArticleSentiment(BaseModel):
    """AI-generated sentiment for a single news article."""

    sentiment: NewsSentiment = Field(description="Sentiment of the article")
    confidence: str = Field(default="medium", description="Confidence level (low/medium/high)")
    summary: str = Field(default="", description="One-line summary of the article's impact")


class NewsTheme(BaseModel):
    """A key theme identified in the news."""

    theme: str = Field(description="The theme or topic")
    description: str = Field(description="Brief explanation of the theme")
    sentiment: NewsSentiment = Field(description="Sentiment of this theme")
    relevance: str = Field(description="How relevant this is to the stock (high/medium/low)")


class SourceArticle(BaseModel):
    """A source article reference with URL."""

    title: str
    url: str
    publisher: str
    time_ago: str


class NewsAnalysis(BaseModel):
    """AI-generated news analysis for a stock."""

    symbol: str = Field(description="Stock symbol analyzed")
    articles_analyzed: int = Field(description="Number of articles analyzed")
    date_range: str = Field(description="Date range of articles analyzed")

    # Overall sentiment
    overall_sentiment: NewsSentiment = Field(description="Overall news sentiment")
    sentiment_reasoning: str = Field(description="Explanation for the sentiment assessment")
    confidence_level: str = Field(description="Confidence in analysis (low/medium/high)")

    # Key themes
    key_themes: List[NewsTheme] = Field(default_factory=list, description="Major themes in the news")

    # Impact analysis
    short_term_impact: str = Field(description="Potential short-term impact on stock (days to weeks)")
    long_term_impact: str = Field(description="Potential long-term impact on stock (months+)")

    # Actionable summary
    summary: str = Field(description="Executive summary of the news landscape")
    key_takeaways: List[str] = Field(default_factory=list, description="Key points for investors")
    watch_items: List[str] = Field(default_factory=list, description="Things to monitor going forward")

    # Source articles
    source_articles: List[SourceArticle] = Field(
        default_factory=list, description="Source articles with URLs"
    )

    disclaimer: str = Field(
        default="This is AI-generated analysis for educational purposes only. "
        "News sentiment can change rapidly. Not financial advice.",
        description="Legal disclaimer",
    )
