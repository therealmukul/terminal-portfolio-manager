"""AI service for Claude-powered stock analysis."""

import json
import re

from anthropic import Anthropic

from app.config import Settings
from datetime import datetime, timedelta
from typing import Dict, List

from app.models.ai_response import (
    AIInsight,
    NewsAnalysis,
    NewsSentiment,
    NewsTheme,
    PortfolioNewsAlert,
    PortfolioNewsAnalysis,
    RecommendationType,
    SectorTrend,
    SourceArticle,
    StockNewsSummary,
)
from app.models.stock import NewsArticle
from app.models.portfolio import (
    InsightCategory,
    InsightSeverity,
    Portfolio,
    PortfolioAnalysis,
    PortfolioInsight,
)
from app.models.stock import StockAnalysis
from app.services.rate_limiter import RateLimiter
from app.utils.exceptions import AIServiceError
from app.utils.formatters import (
    format_currency,
    format_large_number,
    format_percentage,
    format_ratio,
)


class AIService:
    """Service for Claude-powered stock analysis."""

    def __init__(self, settings: Settings, rate_limiter: RateLimiter):
        """
        Initialize the AI service.

        Args:
            settings: Application settings
            rate_limiter: Rate limiter for API calls
        """
        self.client = Anthropic(api_key=settings.anthropic_api_key)
        self.rate_limiter = rate_limiter
        self.model = settings.claude_model
        self.max_tokens = settings.claude_max_tokens

    def analyze_stock(self, analysis: StockAnalysis) -> AIInsight:
        """
        Generate AI-powered insights from stock data.

        Args:
            analysis: Stock analysis data

        Returns:
            AIInsight with Claude's analysis

        Raises:
            AIServiceError: If AI analysis fails
        """
        self.rate_limiter.acquire_sync()

        try:
            prompt = self._build_analysis_prompt(analysis)

            response = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                system=self._get_system_prompt(),
                messages=[{"role": "user", "content": prompt}],
            )

            return self._parse_response(response.content[0].text)

        except Exception as e:
            raise AIServiceError(f"AI analysis failed: {e}")

    def _get_system_prompt(self) -> str:
        """Get the system prompt for Claude."""
        return """You are an expert financial analyst providing stock analysis.
Your task is to analyze fundamental data and provide balanced, educational insights.

IMPORTANT: You must respond in valid JSON format with the following structure:
{
    "summary": "A 2-3 sentence executive summary of the stock",
    "strengths": ["strength 1", "strength 2", ...],
    "weaknesses": ["weakness 1", "weakness 2", ...],
    "opportunities": ["opportunity 1", "opportunity 2", ...],
    "risks": ["risk 1", "risk 2", ...],
    "recommendation": "one of: strong_buy, buy, hold, sell, strong_sell",
    "confidence_level": "one of: low, medium, high",
    "valuation_assessment": "Assessment of current valuation relative to fundamentals",
    "key_metrics_analysis": "Analysis of the most important metrics"
}

Guidelines:
- Be objective and balanced - mention both positives and negatives
- Base recommendations on the provided data, not speculation
- Consider industry context when evaluating metrics
- Keep each point concise but informative
- Provide 3-5 items for strengths, weaknesses, opportunities, and risks
- Always remind that this is for educational purposes only"""

    def _build_analysis_prompt(self, analysis: StockAnalysis) -> str:
        """Build the analysis prompt with stock data."""
        info = analysis.info
        fund = analysis.fundamentals

        prompt = f"""Please analyze the following stock data and provide your insights:

## Company Information
- **Symbol**: {info.symbol}
- **Company**: {info.company_name}
- **Sector**: {info.sector or 'N/A'}
- **Industry**: {info.industry or 'N/A'}

## Current Price Data
- **Current Price**: {format_currency(analysis.current_price)}
- **52-Week High**: {format_currency(analysis.fifty_two_week_high)}
- **52-Week Low**: {format_currency(analysis.fifty_two_week_low)}
- **Previous Close**: {format_currency(analysis.previous_close)}

## Valuation Metrics
- **Market Cap**: {format_large_number(fund.market_cap)}
- **P/E Ratio (Trailing)**: {format_ratio(fund.pe_ratio)}
- **P/E Ratio (Forward)**: {format_ratio(fund.forward_pe)}
- **PEG Ratio**: {format_ratio(fund.peg_ratio)}
- **Price to Book**: {format_ratio(fund.price_to_book)}
- **Price to Sales**: {format_ratio(fund.price_to_sales)}
- **Enterprise Value**: {format_large_number(fund.enterprise_value)}

## Profitability
- **Profit Margin**: {format_percentage(fund.profit_margin)}
- **Operating Margin**: {format_percentage(fund.operating_margin)}
- **Gross Margin**: {format_percentage(fund.gross_margin)}
- **Return on Equity**: {format_percentage(fund.return_on_equity)}
- **Return on Assets**: {format_percentage(fund.return_on_assets)}

## Per Share Data
- **EPS (Trailing)**: {format_currency(fund.eps)}
- **EPS (Forward)**: {format_currency(fund.eps_forward)}
- **Book Value**: {format_currency(fund.book_value)}

## Revenue & Growth
- **Total Revenue**: {format_large_number(fund.revenue)}
- **Revenue Growth**: {format_percentage(fund.revenue_growth)}
- **Earnings Growth**: {format_percentage(fund.earnings_growth)}

## Financial Health
- **Total Debt**: {format_large_number(fund.total_debt)}
- **Total Cash**: {format_large_number(fund.total_cash)}
- **Debt to Equity**: {format_ratio(fund.debt_to_equity)}
- **Current Ratio**: {format_ratio(fund.current_ratio)}
- **Quick Ratio**: {format_ratio(fund.quick_ratio)}
- **Free Cash Flow**: {format_large_number(fund.free_cash_flow)}

## Dividends
- **Dividend Yield**: {format_percentage(fund.dividend_yield)}
- **Dividend Rate**: {format_currency(fund.dividend_rate)}
- **Payout Ratio**: {format_percentage(fund.payout_ratio)}

## Analyst Data
- **Analyst Rating**: {analysis.analyst_rating or 'N/A'}
- **Target Price (Mean)**: {format_currency(analysis.target_mean_price)}
- **Target Price (High)**: {format_currency(analysis.target_high_price)}
- **Target Price (Low)**: {format_currency(analysis.target_low_price)}
- **Number of Analysts**: {analysis.number_of_analysts or 'N/A'}

Please provide your analysis in the JSON format specified."""

        return prompt

    def _parse_response(self, response_text: str) -> AIInsight:
        """Parse Claude's response into AIInsight."""
        try:
            # Try to extract JSON from the response
            json_match = re.search(r"\{[\s\S]*\}", response_text)
            if json_match:
                data = json.loads(json_match.group())
            else:
                # If no JSON found, create a basic response
                return AIInsight(
                    summary=response_text[:500],
                    strengths=["Unable to parse detailed analysis"],
                    weaknesses=[],
                    opportunities=[],
                    risks=[],
                )

            # Map recommendation string to enum
            recommendation = None
            rec_str = data.get("recommendation", "").lower().replace(" ", "_")
            for rec_type in RecommendationType:
                if rec_type.value == rec_str:
                    recommendation = rec_type
                    break

            return AIInsight(
                summary=data.get("summary", ""),
                strengths=data.get("strengths", []),
                weaknesses=data.get("weaknesses", []),
                opportunities=data.get("opportunities", []),
                risks=data.get("risks", []),
                recommendation=recommendation,
                confidence_level=data.get("confidence_level"),
                valuation_assessment=data.get("valuation_assessment", ""),
                key_metrics_analysis=data.get("key_metrics_analysis", ""),
            )

        except json.JSONDecodeError:
            # Fallback if JSON parsing fails
            return AIInsight(
                summary=response_text[:500],
                strengths=["Analysis provided in non-structured format"],
                weaknesses=[],
                opportunities=[],
                risks=[],
            )

    # ============ Portfolio Analysis ============

    def analyze_portfolio(self, portfolio: Portfolio) -> PortfolioAnalysis:
        """
        Generate AI-powered insights for the entire portfolio.

        Args:
            portfolio: Portfolio with positions and current prices

        Returns:
            PortfolioAnalysis with AI insights

        Raises:
            AIServiceError: If AI analysis fails
        """
        self.rate_limiter.acquire_sync()

        try:
            prompt = self._build_portfolio_prompt(portfolio)

            response = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                system=self._get_portfolio_system_prompt(),
                messages=[{"role": "user", "content": prompt}],
            )

            return self._parse_portfolio_response(response.content[0].text)

        except Exception as e:
            raise AIServiceError(f"Portfolio analysis failed: {e}")

    def _get_portfolio_system_prompt(self) -> str:
        """Get the system prompt for portfolio analysis."""
        return """You are an expert financial advisor providing portfolio analysis for a long-term investor.
Your task is to analyze the portfolio and provide actionable insights on rebalancing, risk management, and tax optimization.

IMPORTANT: You must respond in valid JSON format with the following structure:
{
    "summary": "A 2-3 sentence executive summary of the portfolio health",
    "overall_health": "one of: excellent, good, fair, needs_attention",
    "concentration_risk_score": "one of: low, medium, high",
    "diversification_score": "one of: poor, fair, good, excellent",
    "confidence_level": "one of: low, medium, high",

    "rebalancing_insights": [
        {
            "severity": "one of: info, warning, alert, action_required",
            "title": "Short title",
            "description": "Detailed explanation",
            "affected_symbols": ["SYM1", "SYM2"],
            "recommended_action": "What to do",
            "action_urgency": "one of: immediate, this_week, this_month, when_convenient"
        }
    ],

    "risk_insights": [
        {
            "severity": "...",
            "title": "...",
            "description": "...",
            "affected_symbols": [],
            "recommended_action": "...",
            "action_urgency": "..."
        }
    ],

    "tax_insights": [
        {
            "severity": "...",
            "title": "...",
            "description": "...",
            "affected_symbols": [],
            "recommended_action": "...",
            "action_urgency": "..."
        }
    ],

    "tax_loss_harvesting_opportunities": ["Symbol1 - reason", "Symbol2 - reason"],
    "wash_sale_warnings": ["Warning about recent sales if any"],

    "action_items": [
        {
            "severity": "...",
            "title": "...",
            "description": "...",
            "affected_symbols": [],
            "recommended_action": "...",
            "action_urgency": "..."
        }
    ],

    "hold_recommendations": ["Symbol - reason to continue holding"]
}

Guidelines:
- Focus on long-term investing perspective
- Be specific with actionable recommendations
- Consider tax implications (short-term vs long-term capital gains)
- Flag concentration risk if any position exceeds 20% of portfolio
- Flag sector concentration if any sector exceeds 40%
- Identify tax-loss harvesting opportunities (positions with unrealized losses held >30 days)
- Warn about wash sale rules if relevant
- Prioritize action items by urgency
- Recommend continuing to hold positions with strong fundamentals
- Keep insights concise but actionable
- Always remind this is for educational purposes only"""

    def _build_portfolio_prompt(self, portfolio: Portfolio) -> str:
        """Build the analysis prompt with portfolio data."""
        # Portfolio summary
        prompt = f"""Please analyze my investment portfolio and provide insights:

## Portfolio Summary
- **Total Value**: {format_currency(portfolio.total_current_value)}
- **Total Cost Basis**: {format_currency(portfolio.total_cost_basis)}
- **Total Unrealized Gain/Loss**: {format_currency(portfolio.total_unrealized_gain)} ({format_percentage(portfolio.total_unrealized_gain_pct)})
- **Number of Holdings**: {portfolio.num_symbols}
- **Number of Tax Lots**: {portfolio.num_positions}

## Sector Allocation
"""
        # Sector breakdown
        if portfolio.sector_allocation:
            for sector, weight in sorted(
                portfolio.sector_allocation.items(), key=lambda x: x[1], reverse=True
            ):
                prompt += f"- **{sector}**: {format_percentage(weight)}\n"
        else:
            prompt += "- Sector data not available\n"

        # Individual holdings
        prompt += "\n## Holdings Detail\n"
        for agg in portfolio.aggregated:
            prompt += f"""
### {agg.symbol}
- **Sector**: {agg.sector or 'N/A'}
- **Industry**: {agg.industry or 'N/A'}
- **Total Shares**: {agg.total_shares:.4f}
- **Average Cost**: {format_currency(agg.average_cost)}
- **Current Price**: {format_currency(agg.current_price)}
- **Current Value**: {format_currency(agg.current_value)}
- **Weight**: {format_percentage(agg.weight_pct)}
- **Unrealized Gain/Loss**: {format_currency(agg.unrealized_gain)} ({format_percentage(agg.unrealized_gain_pct)})
"""
            # Tax lot detail
            if len(agg.lots) > 1:
                prompt += "- **Tax Lots**:\n"
                for lot in agg.lots:
                    holding_type = "Long-term" if lot.is_long_term else "Short-term"
                    prompt += f"  - {lot.shares:.4f} shares @ {format_currency(lot.purchase_price)} on {lot.purchase_date} ({holding_type}, {lot.holding_period_days} days) - "
                    prompt += f"Gain: {format_currency(lot.unrealized_gain)} ({format_percentage(lot.unrealized_gain_pct)})\n"
            else:
                lot = agg.lots[0] if agg.lots else None
                if lot:
                    holding_type = "Long-term" if lot.is_long_term else "Short-term"
                    prompt += f"- **Holding Period**: {holding_type} ({lot.holding_period_days} days since {lot.purchase_date})\n"

        prompt += """
## Analysis Request
Based on my portfolio above, please provide:
1. Overall portfolio health assessment
2. Rebalancing recommendations (if any positions are overweight/underweight)
3. Risk analysis (concentration, sector exposure, volatility)
4. Tax optimization opportunities (tax-loss harvesting, wash sale concerns)
5. Clear action items vs hold recommendations

Remember: I am a long-term investor. Please prioritize recommendations by urgency and importance."""

        return prompt

    def _parse_portfolio_response(self, response_text: str) -> PortfolioAnalysis:
        """Parse Claude's response into PortfolioAnalysis."""
        try:
            # Try to extract JSON from the response
            json_match = re.search(r"\{[\s\S]*\}", response_text)
            if not json_match:
                return PortfolioAnalysis(
                    summary=response_text[:500],
                    overall_health="Unable to parse analysis",
                )

            data = json.loads(json_match.group())

            # Parse insights
            def parse_insights(insights_data: list) -> list:
                """Parse insight list from JSON."""
                insights = []
                for item in insights_data or []:
                    try:
                        severity = InsightSeverity(item.get("severity", "info"))
                    except ValueError:
                        severity = InsightSeverity.INFO

                    insights.append(
                        PortfolioInsight(
                            category=InsightCategory.GENERAL,
                            severity=severity,
                            title=item.get("title", ""),
                            description=item.get("description", ""),
                            affected_symbols=item.get("affected_symbols", []),
                            recommended_action=item.get("recommended_action"),
                            action_urgency=item.get("action_urgency"),
                        )
                    )
                return insights

            # Set categories for insights
            rebalancing_insights = parse_insights(data.get("rebalancing_insights", []))
            for insight in rebalancing_insights:
                insight.category = InsightCategory.REBALANCING

            risk_insights = parse_insights(data.get("risk_insights", []))
            for insight in risk_insights:
                insight.category = InsightCategory.RISK

            tax_insights = parse_insights(data.get("tax_insights", []))
            for insight in tax_insights:
                insight.category = InsightCategory.TAX

            action_items = parse_insights(data.get("action_items", []))
            for insight in action_items:
                insight.category = InsightCategory.OPPORTUNITY

            return PortfolioAnalysis(
                summary=data.get("summary", ""),
                overall_health=data.get("overall_health", ""),
                concentration_risk_score=data.get("concentration_risk_score"),
                diversification_score=data.get("diversification_score"),
                confidence_level=data.get("confidence_level"),
                rebalancing_insights=rebalancing_insights,
                risk_insights=risk_insights,
                tax_insights=tax_insights,
                tax_loss_harvesting_opportunities=data.get(
                    "tax_loss_harvesting_opportunities", []
                ),
                wash_sale_warnings=data.get("wash_sale_warnings", []),
                action_items=action_items,
                hold_recommendations=data.get("hold_recommendations", []),
            )

        except json.JSONDecodeError:
            return PortfolioAnalysis(
                summary=response_text[:500],
                overall_health="Analysis provided in non-structured format",
            )

    # ============ News Analysis ============

    def analyze_news(self, symbol: str, articles: List[NewsArticle]) -> NewsAnalysis:
        """
        Generate AI-powered analysis of news articles for a stock.

        Args:
            symbol: Stock ticker symbol
            articles: List of news articles to analyze

        Returns:
            NewsAnalysis with sentiment, themes, and insights

        Raises:
            AIServiceError: If AI analysis fails
        """
        # Filter articles from the past 2 weeks
        two_weeks_ago = datetime.now() - timedelta(days=14)
        recent_articles = []
        for article in articles:
            pub_time = article.published_at
            if pub_time.tzinfo is not None:
                pub_time = pub_time.replace(tzinfo=None)
            if pub_time >= two_weeks_ago:
                recent_articles.append(article)

        if not recent_articles:
            raise AIServiceError(f"No news articles found for {symbol} in the past 2 weeks")

        self.rate_limiter.acquire_sync()

        try:
            prompt = self._build_news_analysis_prompt(symbol, recent_articles)

            response = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                system=self._get_news_analysis_system_prompt(),
                messages=[{"role": "user", "content": prompt}],
            )

            return self._parse_news_analysis_response(
                response.content[0].text, symbol, recent_articles
            )

        except AIServiceError:
            raise
        except Exception as e:
            raise AIServiceError(f"News analysis failed: {e}")

    def _get_news_analysis_system_prompt(self) -> str:
        """Get the system prompt for news analysis."""
        return """You are an expert financial analyst specializing in news analysis and sentiment assessment.
Your task is to analyze recent news articles about a stock and provide insights on sentiment, key themes, and potential market impact.

IMPORTANT: You must respond in valid JSON format with the following structure:
{
    "overall_sentiment": "one of: very_bullish, bullish, neutral, bearish, very_bearish",
    "sentiment_reasoning": "2-3 sentence explanation of why you assessed this sentiment",
    "confidence_level": "one of: low, medium, high",

    "key_themes": [
        {
            "theme": "Theme name (e.g., 'Earnings Performance', 'Product Launch')",
            "description": "Brief description of this theme in the news",
            "sentiment": "one of: very_bullish, bullish, neutral, bearish, very_bearish",
            "relevance": "one of: high, medium, low"
        }
    ],

    "short_term_impact": "Assessment of potential impact over days to weeks",
    "long_term_impact": "Assessment of potential impact over months or longer",

    "summary": "Executive summary of the news landscape (2-3 sentences)",
    "key_takeaways": ["Key point 1", "Key point 2", "Key point 3"],
    "watch_items": ["Thing to monitor 1", "Thing to monitor 2"]
}

Guidelines:
- Give GREATER WEIGHT to more recent articles when assessing overall sentiment
- Articles from the past 1-3 days are most important, followed by 4-7 days, then 8-14 days
- Identify 3-5 key themes from the news
- Be specific about potential market impacts
- Consider both company-specific news and broader market/sector context
- Provide actionable takeaways for investors
- Note any conflicting signals in the news
- Always remind that news sentiment can change rapidly"""

    def _build_news_analysis_prompt(self, symbol: str, articles: List[NewsArticle]) -> str:
        """Build the news analysis prompt with article data."""
        # Sort articles by date (most recent first)
        sorted_articles = sorted(articles, key=lambda a: a.published_at, reverse=True)

        prompt = f"""Please analyze the following news articles for {symbol} and provide your assessment:

## Stock: {symbol}
## Articles: {len(sorted_articles)} articles from the past 2 weeks
## Analysis Date: {datetime.now().strftime('%Y-%m-%d')}

---

"""
        for i, article in enumerate(sorted_articles, 1):
            recency_note = ""
            days_ago = (datetime.now() - article.published_at.replace(tzinfo=None)).days
            if days_ago == 0:
                recency_note = " [TODAY - HIGH WEIGHT]"
            elif days_ago <= 3:
                recency_note = f" [{days_ago}d ago - HIGH WEIGHT]"
            elif days_ago <= 7:
                recency_note = f" [{days_ago}d ago - MEDIUM WEIGHT]"
            else:
                recency_note = f" [{days_ago}d ago - LOWER WEIGHT]"

            prompt += f"""### Article {i}{recency_note}
**Title:** {article.title}
**Publisher:** {article.publisher}
**Date:** {article.published_at.strftime('%Y-%m-%d %H:%M')}
"""
            if article.summary:
                prompt += f"**Summary:** {article.summary}\n"
            prompt += "\n---\n\n"

        prompt += """
Based on these articles, please provide:
1. Overall sentiment assessment (weighted by recency)
2. Key themes emerging from the news
3. Short-term and long-term potential impacts
4. Actionable takeaways for investors

Respond in the JSON format specified."""

        return prompt

    def _parse_news_analysis_response(
        self, response_text: str, symbol: str, articles: List[NewsArticle]
    ) -> NewsAnalysis:
        """Parse Claude's response into NewsAnalysis."""
        # Calculate date range
        dates = [a.published_at for a in articles]
        oldest = min(dates).strftime('%Y-%m-%d')
        newest = max(dates).strftime('%Y-%m-%d')
        date_range = f"{oldest} to {newest}"

        # Build source articles from original data (sorted by date, most recent first)
        sorted_articles = sorted(articles, key=lambda a: a.published_at, reverse=True)
        source_articles = [
            SourceArticle(
                title=article.title,
                url=article.url,
                publisher=article.publisher,
                time_ago=article.time_ago,
            )
            for article in sorted_articles
        ]

        try:
            json_match = re.search(r"\{[\s\S]*\}", response_text)
            if not json_match:
                return NewsAnalysis(
                    symbol=symbol,
                    articles_analyzed=len(articles),
                    date_range=date_range,
                    overall_sentiment=NewsSentiment.NEUTRAL,
                    sentiment_reasoning="Unable to parse detailed analysis",
                    confidence_level="low",
                    short_term_impact="Analysis unavailable",
                    long_term_impact="Analysis unavailable",
                    summary=response_text[:500],
                    source_articles=source_articles,
                )

            data = json.loads(json_match.group())

            # Parse sentiment
            try:
                overall_sentiment = NewsSentiment(data.get("overall_sentiment", "neutral"))
            except ValueError:
                overall_sentiment = NewsSentiment.NEUTRAL

            # Parse key themes
            key_themes = []
            for theme_data in data.get("key_themes", []):
                try:
                    theme_sentiment = NewsSentiment(theme_data.get("sentiment", "neutral"))
                except ValueError:
                    theme_sentiment = NewsSentiment.NEUTRAL

                key_themes.append(
                    NewsTheme(
                        theme=theme_data.get("theme", "Unknown"),
                        description=theme_data.get("description", ""),
                        sentiment=theme_sentiment,
                        relevance=theme_data.get("relevance", "medium"),
                    )
                )

            return NewsAnalysis(
                symbol=symbol,
                articles_analyzed=len(articles),
                date_range=date_range,
                overall_sentiment=overall_sentiment,
                sentiment_reasoning=data.get("sentiment_reasoning", ""),
                confidence_level=data.get("confidence_level", "medium"),
                key_themes=key_themes,
                short_term_impact=data.get("short_term_impact", ""),
                long_term_impact=data.get("long_term_impact", ""),
                summary=data.get("summary", ""),
                key_takeaways=data.get("key_takeaways", []),
                watch_items=data.get("watch_items", []),
                source_articles=source_articles,
            )

        except json.JSONDecodeError:
            return NewsAnalysis(
                symbol=symbol,
                articles_analyzed=len(articles),
                date_range=date_range,
                overall_sentiment=NewsSentiment.NEUTRAL,
                sentiment_reasoning="Analysis provided in non-structured format",
                confidence_level="low",
                short_term_impact="Analysis unavailable",
                long_term_impact="Analysis unavailable",
                summary=response_text[:500],
                source_articles=source_articles,
            )

    # ============ Portfolio News Analysis ============

    def analyze_portfolio_news(
        self,
        news_by_symbol: Dict[str, List[NewsArticle]],
        sector_by_symbol: Dict[str, str],
        weight_by_symbol: Dict[str, float],
    ) -> PortfolioNewsAnalysis:
        """
        Generate AI-powered news analysis across all portfolio holdings.

        Args:
            news_by_symbol: Dict mapping symbols to their news articles
            sector_by_symbol: Dict mapping symbols to their sectors
            weight_by_symbol: Dict mapping symbols to their portfolio weight

        Returns:
            PortfolioNewsAnalysis with cross-portfolio insights

        Raises:
            AIServiceError: If AI analysis fails
        """
        # Filter articles from the past 2 weeks for each symbol
        two_weeks_ago = datetime.now() - timedelta(days=14)
        filtered_news: Dict[str, List[NewsArticle]] = {}
        total_articles = 0

        for symbol, articles in news_by_symbol.items():
            recent = []
            for article in articles:
                pub_time = article.published_at
                if pub_time.tzinfo is not None:
                    pub_time = pub_time.replace(tzinfo=None)
                if pub_time >= two_weeks_ago:
                    recent.append(article)
            if recent:
                filtered_news[symbol] = recent
                total_articles += len(recent)

        if not filtered_news:
            raise AIServiceError("No recent news articles found for any portfolio holdings")

        self.rate_limiter.acquire_sync()

        try:
            prompt = self._build_portfolio_news_prompt(
                filtered_news, sector_by_symbol, weight_by_symbol
            )

            response = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                system=self._get_portfolio_news_system_prompt(),
                messages=[{"role": "user", "content": prompt}],
            )

            return self._parse_portfolio_news_response(
                response.content[0].text,
                filtered_news,
                total_articles,
            )

        except AIServiceError:
            raise
        except Exception as e:
            raise AIServiceError(f"Portfolio news analysis failed: {e}")

    def _get_portfolio_news_system_prompt(self) -> str:
        """Get the system prompt for portfolio news analysis."""
        return """You are an expert financial analyst specializing in portfolio-wide news analysis.
Your task is to synthesize news across multiple holdings and identify cross-portfolio patterns, risks, and opportunities.

IMPORTANT: You must respond in valid JSON format with the following structure:
{
    "portfolio_sentiment": "one of: very_bullish, bullish, neutral, bearish, very_bearish",
    "sentiment_breakdown": "e.g., '3 bullish, 2 neutral, 1 bearish holdings'",
    "confidence_level": "one of: low, medium, high",

    "summary": "2-3 sentence executive summary of the portfolio news landscape",

    "stock_summaries": [
        {
            "symbol": "AAPL",
            "sentiment": "one of: very_bullish, bullish, neutral, bearish, very_bearish",
            "article_count": 5,
            "headline_summary": "One-line summary of key news for this stock",
            "sentiment_driver": "Main factor driving sentiment"
        }
    ],

    "sector_trends": [
        {
            "sector": "Technology",
            "sentiment": "one of: very_bullish, bullish, neutral, bearish, very_bearish",
            "key_development": "Main news development in this sector",
            "affected_holdings": ["AAPL", "MSFT"]
        }
    ],

    "correlated_risks": ["Risk affecting multiple holdings"],
    "cross_portfolio_themes": ["Theme appearing across multiple stocks"],

    "alerts": [
        {
            "urgency": "one of: immediate, this_week, monitor",
            "alert_type": "one of: risk, opportunity, information",
            "title": "Short alert title",
            "description": "Detailed description",
            "affected_symbols": ["SYM1", "SYM2"],
            "recommended_action": "What to do"
        }
    ],

    "opportunities": ["Opportunity identified from news"],

    "portfolio_news_health": "Overall assessment of the news environment (1-2 sentences)",
    "key_takeaways": ["Key point 1", "Key point 2", "Key point 3"]
}

Guidelines:
- Weight analysis by portfolio allocation (larger positions matter more)
- Give greater weight to more recent articles
- Identify correlations - news affecting multiple holdings
- Flag sector-wide trends that impact portfolio concentration
- Prioritize alerts by urgency and portfolio impact
- Consider how news for one holding might affect others
- Note any conflicting signals between holdings
- Focus on actionable insights for the portfolio owner"""

    def _build_portfolio_news_prompt(
        self,
        news_by_symbol: Dict[str, List[NewsArticle]],
        sector_by_symbol: Dict[str, str],
        weight_by_symbol: Dict[str, float],
    ) -> str:
        """Build the portfolio news analysis prompt."""
        prompt = f"""Please analyze the news across my portfolio holdings and provide a comprehensive assessment:

## Portfolio Overview
- **Holdings Analyzed:** {len(news_by_symbol)}
- **Analysis Date:** {datetime.now().strftime('%Y-%m-%d')}

## Holdings by Weight (largest first):
"""
        # Sort by weight
        sorted_symbols = sorted(
            news_by_symbol.keys(),
            key=lambda s: weight_by_symbol.get(s, 0),
            reverse=True
        )

        for symbol in sorted_symbols:
            weight = weight_by_symbol.get(symbol, 0)
            sector = sector_by_symbol.get(symbol, "Unknown")
            prompt += f"- **{symbol}**: {weight:.1f}% of portfolio (Sector: {sector})\n"

        prompt += "\n---\n\n"

        # Add news for each symbol
        for symbol in sorted_symbols:
            articles = news_by_symbol[symbol]
            weight = weight_by_symbol.get(symbol, 0)
            sector = sector_by_symbol.get(symbol, "Unknown")

            # Sort articles by date
            sorted_articles = sorted(articles, key=lambda a: a.published_at, reverse=True)

            prompt += f"""## {symbol} ({sector}) - Portfolio Weight: {weight:.1f}%
**{len(articles)} articles in the past 2 weeks**

"""
            for i, article in enumerate(sorted_articles[:5], 1):  # Limit to 5 per stock
                days_ago = (datetime.now() - article.published_at.replace(tzinfo=None)).days
                recency = "TODAY" if days_ago == 0 else f"{days_ago}d ago"

                prompt += f"**[{recency}]** {article.title}\n"
                if article.summary:
                    summary = article.summary[:150] + "..." if len(article.summary) > 150 else article.summary
                    prompt += f"   {summary}\n"
                prompt += "\n"

            prompt += "---\n\n"

        prompt += """
Based on the news above, please provide:
1. Portfolio-wide sentiment assessment (weighted by position size)
2. Individual stock sentiment summaries
3. Sector-level trends affecting the portfolio
4. Correlated risks and cross-portfolio themes
5. Prioritized alerts and opportunities
6. Key takeaways for portfolio management

Respond in the JSON format specified."""

        return prompt

    def _parse_portfolio_news_response(
        self,
        response_text: str,
        news_by_symbol: Dict[str, List[NewsArticle]],
        total_articles: int,
    ) -> PortfolioNewsAnalysis:
        """Parse Claude's response into PortfolioNewsAnalysis."""
        # Calculate date range
        all_dates = []
        for articles in news_by_symbol.values():
            all_dates.extend([a.published_at for a in articles])

        oldest = min(all_dates).strftime('%Y-%m-%d')
        newest = max(all_dates).strftime('%Y-%m-%d')
        date_range = f"{oldest} to {newest}"

        try:
            json_match = re.search(r"\{[\s\S]*\}", response_text)
            if not json_match:
                return PortfolioNewsAnalysis(
                    total_articles_analyzed=total_articles,
                    stocks_analyzed=len(news_by_symbol),
                    date_range=date_range,
                    analysis_date=datetime.now().strftime('%Y-%m-%d'),
                    portfolio_sentiment=NewsSentiment.NEUTRAL,
                    sentiment_breakdown="Unable to parse analysis",
                    confidence_level="low",
                    summary=response_text[:500],
                    portfolio_news_health="Analysis unavailable",
                )

            data = json.loads(json_match.group())

            # Parse portfolio sentiment
            try:
                portfolio_sentiment = NewsSentiment(data.get("portfolio_sentiment", "neutral"))
            except ValueError:
                portfolio_sentiment = NewsSentiment.NEUTRAL

            # Parse stock summaries
            stock_summaries = []
            for summary_data in data.get("stock_summaries", []):
                try:
                    sentiment = NewsSentiment(summary_data.get("sentiment", "neutral"))
                except ValueError:
                    sentiment = NewsSentiment.NEUTRAL

                symbol = summary_data.get("symbol", "")

                # Attach source articles from original news data
                source_articles = []
                if symbol in news_by_symbol:
                    # Sort by date (most recent first) and take top 5
                    sorted_articles = sorted(
                        news_by_symbol[symbol],
                        key=lambda a: a.published_at,
                        reverse=True
                    )[:5]
                    for article in sorted_articles:
                        source_articles.append(
                            SourceArticle(
                                title=article.title,
                                url=article.url,
                                publisher=article.publisher,
                                time_ago=article.time_ago,
                            )
                        )

                stock_summaries.append(
                    StockNewsSummary(
                        symbol=symbol,
                        sentiment=sentiment,
                        article_count=summary_data.get("article_count", 0),
                        headline_summary=summary_data.get("headline_summary", ""),
                        sentiment_driver=summary_data.get("sentiment_driver", ""),
                        source_articles=source_articles,
                    )
                )

            # Parse sector trends
            sector_trends = []
            for trend_data in data.get("sector_trends", []):
                try:
                    sentiment = NewsSentiment(trend_data.get("sentiment", "neutral"))
                except ValueError:
                    sentiment = NewsSentiment.NEUTRAL

                sector_trends.append(
                    SectorTrend(
                        sector=trend_data.get("sector", ""),
                        sentiment=sentiment,
                        key_development=trend_data.get("key_development", ""),
                        affected_holdings=trend_data.get("affected_holdings", []),
                    )
                )

            # Parse alerts
            alerts = []
            for alert_data in data.get("alerts", []):
                alerts.append(
                    PortfolioNewsAlert(
                        urgency=alert_data.get("urgency", "monitor"),
                        alert_type=alert_data.get("alert_type", "information"),
                        title=alert_data.get("title", ""),
                        description=alert_data.get("description", ""),
                        affected_symbols=alert_data.get("affected_symbols", []),
                        recommended_action=alert_data.get("recommended_action"),
                    )
                )

            return PortfolioNewsAnalysis(
                total_articles_analyzed=total_articles,
                stocks_analyzed=len(news_by_symbol),
                date_range=date_range,
                analysis_date=datetime.now().strftime('%Y-%m-%d'),
                portfolio_sentiment=portfolio_sentiment,
                sentiment_breakdown=data.get("sentiment_breakdown", ""),
                confidence_level=data.get("confidence_level", "medium"),
                summary=data.get("summary", ""),
                stock_summaries=stock_summaries,
                sector_trends=sector_trends,
                correlated_risks=data.get("correlated_risks", []),
                cross_portfolio_themes=data.get("cross_portfolio_themes", []),
                alerts=alerts,
                opportunities=data.get("opportunities", []),
                portfolio_news_health=data.get("portfolio_news_health", ""),
                key_takeaways=data.get("key_takeaways", []),
            )

        except json.JSONDecodeError:
            return PortfolioNewsAnalysis(
                total_articles_analyzed=total_articles,
                stocks_analyzed=len(news_by_symbol),
                date_range=date_range,
                analysis_date=datetime.now().strftime('%Y-%m-%d'),
                portfolio_sentiment=NewsSentiment.NEUTRAL,
                sentiment_breakdown="Analysis provided in non-structured format",
                confidence_level="low",
                summary=response_text[:500],
                portfolio_news_health="Analysis unavailable",
            )
