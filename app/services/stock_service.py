"""Stock data service using Yahoo Finance."""

from datetime import datetime
from typing import Any, List, Optional

import yfinance as yf

import requests

from app.models.stock import (
    EarningsData,
    FundamentalData,
    NewsArticle,
    StockAnalysis,
    StockInfo,
    StockSearchResult,
)
from app.services.rate_limiter import RateLimiter
from app.utils.exceptions import DataFetchError, StockNotFoundError


class StockService:
    """Service for fetching stock data from Yahoo Finance."""

    def __init__(self, rate_limiter: RateLimiter):
        """
        Initialize the stock service.

        Args:
            rate_limiter: Rate limiter for API calls
        """
        self.rate_limiter = rate_limiter

    def search_stocks(self, query: str, limit: int = 8) -> List[StockSearchResult]:
        """
        Search for stocks by ticker symbol or company name.

        Args:
            query: Search query (ticker or company name)
            limit: Maximum number of results to return

        Returns:
            List of StockSearchResult objects

        Raises:
            DataFetchError: If search fails
        """
        self.rate_limiter.acquire_sync()

        try:
            # Use Yahoo Finance search API
            url = "https://query2.finance.yahoo.com/v1/finance/search"
            params = {
                "q": query,
                "quotesCount": limit,
                "newsCount": 0,
                "listsCount": 0,
                "enableFuzzyQuery": True,
                "quotesQueryId": "tss_match_phrase_query",
            }
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }

            response = requests.get(url, params=params, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()

            results = []
            for quote in data.get("quotes", []):
                # Filter to stocks and ETFs only
                quote_type = quote.get("quoteType", "")
                if quote_type not in ("EQUITY", "ETF"):
                    continue

                symbol = quote.get("symbol", "")
                name = quote.get("shortname") or quote.get("longname") or symbol

                results.append(
                    StockSearchResult(
                        symbol=symbol,
                        name=name,
                        exchange=quote.get("exchange"),
                        type=quote_type,
                    )
                )

            return results[:limit]

        except requests.RequestException as e:
            raise DataFetchError(f"Stock search failed: {e}")
        except Exception as e:
            raise DataFetchError(f"Stock search failed: {e}")

    def get_stock_analysis(self, symbol: str) -> StockAnalysis:
        """
        Fetch comprehensive stock data for analysis.

        Args:
            symbol: Stock ticker symbol

        Returns:
            StockAnalysis object with all available data

        Raises:
            StockNotFoundError: If the stock symbol is not found
            DataFetchError: If data fetching fails
        """
        self.rate_limiter.acquire_sync()

        try:
            ticker = yf.Ticker(symbol.upper())
            info = ticker.info

            # Check if we got valid data
            if not info or info.get("regularMarketPrice") is None:
                # Try to check if it's a valid symbol by looking at other fields
                if not info or "symbol" not in info:
                    raise StockNotFoundError(f"Stock symbol '{symbol}' not found")

            return StockAnalysis(
                info=self._extract_stock_info(info, symbol),
                fundamentals=self._extract_fundamentals(info),
                earnings=self._extract_earnings(ticker),
                current_price=self._safe_get(info, "currentPrice", "regularMarketPrice"),
                previous_close=info.get("previousClose"),
                open_price=info.get("open", info.get("regularMarketOpen")),
                day_low=info.get("dayLow", info.get("regularMarketDayLow")),
                day_high=info.get("dayHigh", info.get("regularMarketDayHigh")),
                fifty_two_week_high=info.get("fiftyTwoWeekHigh"),
                fifty_two_week_low=info.get("fiftyTwoWeekLow"),
                volume=info.get("volume", info.get("regularMarketVolume")),
                average_volume=info.get("averageVolume"),
                analyst_rating=info.get("recommendationKey"),
                target_high_price=info.get("targetHighPrice"),
                target_low_price=info.get("targetLowPrice"),
                target_mean_price=info.get("targetMeanPrice"),
                number_of_analysts=info.get("numberOfAnalystOpinions"),
            )

        except StockNotFoundError:
            raise
        except Exception as e:
            raise DataFetchError(f"Failed to fetch data for {symbol}: {e}")

    def _safe_get(self, data: dict, *keys: str) -> Optional[Any]:
        """Get the first non-None value from multiple keys."""
        for key in keys:
            value = data.get(key)
            if value is not None:
                return value
        return None

    def _extract_stock_info(self, info: dict, symbol: str) -> StockInfo:
        """Extract basic stock information."""
        return StockInfo(
            symbol=info.get("symbol", symbol.upper()),
            company_name=info.get("longName", info.get("shortName", symbol)),
            sector=info.get("sector"),
            industry=info.get("industry"),
            currency=info.get("currency", "USD"),
            exchange=info.get("exchange"),
            website=info.get("website"),
            description=info.get("longBusinessSummary"),
        )

    def _extract_fundamentals(self, info: dict) -> FundamentalData:
        """Extract fundamental analysis metrics."""
        # Handle ex-dividend date
        ex_div_timestamp = info.get("exDividendDate")
        ex_dividend_date = None
        if ex_div_timestamp:
            try:
                ex_dividend_date = datetime.fromtimestamp(ex_div_timestamp)
            except (ValueError, TypeError, OSError):
                pass

        return FundamentalData(
            # Valuation
            market_cap=info.get("marketCap"),
            pe_ratio=info.get("trailingPE"),
            forward_pe=info.get("forwardPE"),
            peg_ratio=info.get("pegRatio"),
            price_to_book=info.get("priceToBook"),
            price_to_sales=info.get("priceToSalesTrailing12Months"),
            enterprise_value=info.get("enterpriseValue"),
            # Profitability
            profit_margin=info.get("profitMargins"),
            operating_margin=info.get("operatingMargins"),
            gross_margin=info.get("grossMargins"),
            return_on_equity=info.get("returnOnEquity"),
            return_on_assets=info.get("returnOnAssets"),
            # Per Share Data
            eps=info.get("trailingEps"),
            eps_forward=info.get("forwardEps"),
            book_value=info.get("bookValue"),
            # Revenue & Growth
            revenue=info.get("totalRevenue"),
            revenue_per_share=info.get("revenuePerShare"),
            revenue_growth=info.get("revenueGrowth"),
            earnings_growth=info.get("earningsGrowth"),
            quarterly_revenue_growth=info.get("revenueQuarterlyGrowth"),
            quarterly_earnings_growth=info.get("earningsQuarterlyGrowth"),
            # Financial Health
            total_debt=info.get("totalDebt"),
            total_cash=info.get("totalCash"),
            debt_to_equity=info.get("debtToEquity"),
            current_ratio=info.get("currentRatio"),
            quick_ratio=info.get("quickRatio"),
            free_cash_flow=info.get("freeCashflow"),
            # Dividends
            dividend_yield=info.get("dividendYield"),
            dividend_rate=info.get("dividendRate"),
            payout_ratio=info.get("payoutRatio"),
            ex_dividend_date=ex_dividend_date,
        )

    def _extract_earnings(self, ticker: yf.Ticker) -> EarningsData:
        """Extract earnings data."""
        earnings_data = EarningsData()

        try:
            # Get earnings dates
            calendar = ticker.calendar
            if calendar is not None and not calendar.empty:
                if "Earnings Date" in calendar.index:
                    earnings_dates = calendar.loc["Earnings Date"]
                    if hasattr(earnings_dates, "iloc") and len(earnings_dates) > 0:
                        earnings_data.next_earnings_date = earnings_dates.iloc[0]
        except Exception:
            pass

        try:
            # Get quarterly earnings
            earnings = ticker.quarterly_earnings
            if earnings is not None and not earnings.empty:
                earnings_data.quarterly_earnings = earnings.reset_index().to_dict(
                    "records"
                )
        except Exception:
            pass

        try:
            # Get annual earnings
            earnings = ticker.earnings
            if earnings is not None and not earnings.empty:
                earnings_data.annual_earnings = earnings.reset_index().to_dict("records")
        except Exception:
            pass

        return earnings_data

    def get_news(self, symbol: str, limit: int = 10) -> List[NewsArticle]:
        """
        Fetch news articles for a stock.

        Args:
            symbol: Stock ticker symbol
            limit: Maximum number of articles to return

        Returns:
            List of NewsArticle objects

        Raises:
            StockNotFoundError: If the stock symbol is not found
            DataFetchError: If news fetching fails
        """
        self.rate_limiter.acquire_sync()

        try:
            ticker = yf.Ticker(symbol.upper())
            news_data = ticker.news

            if not news_data:
                return []

            articles = []
            for item in news_data[:limit]:
                try:
                    content = item.get("content", {})
                    if not content:
                        continue

                    # Parse publication date
                    pub_date_str = content.get("pubDate")
                    if pub_date_str:
                        published_at = datetime.fromisoformat(
                            pub_date_str.replace("Z", "+00:00")
                        )
                    else:
                        published_at = datetime.now()

                    # Get thumbnail URL
                    thumbnail = content.get("thumbnail", {})
                    thumbnail_url = None
                    if thumbnail:
                        resolutions = thumbnail.get("resolutions", [])
                        if resolutions:
                            thumbnail_url = resolutions[0].get("url")

                    # Get URL
                    url = ""
                    canonical = content.get("canonicalUrl", {})
                    if canonical:
                        url = canonical.get("url", "")

                    # Get provider
                    provider = content.get("provider", {})
                    publisher = provider.get("displayName", "Unknown")

                    articles.append(
                        NewsArticle(
                            title=content.get("title", "Untitled"),
                            summary=content.get("summary") or content.get("description"),
                            publisher=publisher,
                            url=url,
                            published_at=published_at,
                            thumbnail_url=thumbnail_url,
                        )
                    )
                except Exception:
                    # Skip malformed articles
                    continue

            # Sort by published date descending (most recent first)
            articles.sort(key=lambda a: a.published_at, reverse=True)
            return articles

        except Exception as e:
            raise DataFetchError(f"Failed to fetch news for {symbol}: {e}")
