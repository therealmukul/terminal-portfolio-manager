"""Display formatters for stock analysis using Rich."""

from typing import Dict, List, Optional

from rich.columns import Columns
from rich.panel import Panel
from rich.table import Table

from app.models.ai_response import (
    AIInsight,
    ArticleSentiment,
    NewsAnalysis,
    NewsSentiment,
    PortfolioNewsAnalysis,
    RecommendationType,
)
from app.models.portfolio import (
    Portfolio,
    PortfolioAnalysis,
    PortfolioHistory,
    PortfolioInsight,
    PortfolioPerformance,
    Position,
)
from app.models.stock import NewsArticle, StockAnalysis
from app.ui.console import StockConsole
from app.utils.formatters import (
    format_currency,
    format_large_number,
    format_percentage,
    format_ratio,
    format_volume,
    format_yield,
)


class StockDisplay:
    """Display formatters for stock analysis."""

    def __init__(self, console: StockConsole):
        """
        Initialize the display.

        Args:
            console: StockConsole instance
        """
        self.console = console

    def display_welcome(self):
        """Display welcome message."""
        welcome_text = (
            "[bold cyan]Stock Analysis Agent[/bold cyan]\n"
            "Powered by Yahoo Finance & Claude AI\n\n"
            "[dim]Commands: stock, news, analysis, portfolio, buy, sell,\n"
            "analyze, history, performance, help, quit\n"
            "Type 'help' for full command list with aliases[/dim]"
        )
        panel = Panel(welcome_text, title="Welcome", border_style="cyan", padding=(1, 2))
        self.console.print(panel)

    def display_help(self):
        """Display help information."""
        help_text = """
[bold cyan]Stock Commands:[/bold cyan]
  [bold]stock[/bold]                        - Analyze a stock's fundamentals with optional AI insights
  [bold]news[/bold]                         - Get latest news with AI sentiment analysis per article
  [bold]analysis[/bold]                     - Deep AI analysis of news themes, impact, and takeaways
                                 [dim](alias: news-analysis)[/dim]

[bold cyan]Portfolio Commands:[/bold cyan]
  [bold]portfolio[/bold]                    - View your portfolio with live prices
  [bold]buy[/bold]                          - Add a new position to your portfolio
                                 [dim](aliases: add)[/dim]
  [bold]sell[/bold]                         - Remove a position from your portfolio
                                 [dim](aliases: remove)[/dim]
  [bold]analyze[/bold]                      - Get AI-powered portfolio insights
                                 [dim](aliases: analyze-portfolio, ap)[/dim]
  [bold]portfolio-news[/bold]               - AI analysis of news across all holdings
                                 [dim](aliases: pnews, pn)[/dim]
  [bold]history[/bold]                      - View portfolio value history over time
  [bold]performance[/bold]                  - See which holdings contributed most to gains/losses
                                 [dim](alias: perf)[/dim]

[bold cyan]Other:[/bold cyan]
  [bold]help[/bold]                         - Show this help message
  [bold]quit[/bold]                         - Exit the application
                                 [dim](aliases: exit, q)[/dim]

[bold cyan]Pro Tips:[/bold cyan]
  • After analyzing a stock, you'll be asked if you want to analyze it again
  • Use shorter aliases like 'ap' for analyze-portfolio to save time
  • Buy/sell are clearer than add/remove for portfolio management

[bold cyan]Example Symbols:[/bold cyan]
  AAPL (Apple), MSFT (Microsoft), GOOGL (Alphabet)
"""
        panel = Panel(help_text, title="Help", border_style="blue", padding=(1, 2))
        self.console.print(panel)

    def display_goodbye(self):
        """Display goodbye message."""
        panel = Panel(
            "[bold]Thank you for using Stock Analysis Agent![/bold]\n"
            "[dim]Happy investing![/dim]",
            title="Goodbye",
            border_style="green",
            padding=(1, 2),
        )
        self.console.print(panel)

    def display_stock_info(self, analysis: StockAnalysis):
        """Display basic stock information."""
        info = analysis.info

        # Price change calculation
        price_info = ""
        if analysis.current_price and analysis.previous_close:
            change = analysis.current_price - analysis.previous_close
            change_pct = (change / analysis.previous_close) * 100
            color = "green" if change >= 0 else "red"
            sign = "+" if change >= 0 else ""
            price_info = (
                f"\n[bold]Price:[/bold] {format_currency(analysis.current_price)} "
                f"[{color}]({sign}{change:.2f} / {sign}{change_pct:.2f}%)[/{color}]"
            )

        # 52-week range
        range_info = ""
        if analysis.fifty_two_week_low and analysis.fifty_two_week_high:
            range_info = (
                f"\n[dim]52-Week Range: {format_currency(analysis.fifty_two_week_low)} - "
                f"{format_currency(analysis.fifty_two_week_high)}[/dim]"
            )

        content = (
            f"[bold]{info.company_name}[/bold] ({info.symbol})\n"
            f"[dim]Sector:[/dim] {info.sector or 'N/A'} | "
            f"[dim]Industry:[/dim] {info.industry or 'N/A'}"
            f"{price_info}"
            f"{range_info}"
        )

        panel = Panel(content, title="Stock Information", border_style="blue")
        self.console.print(panel)

    def display_fundamentals(self, analysis: StockAnalysis):
        """Display fundamental metrics in tables."""
        fund = analysis.fundamentals

        # Valuation Table
        valuation_table = Table(title="Valuation", show_header=True, header_style="bold")
        valuation_table.add_column("Metric", style="metric_name", width=20)
        valuation_table.add_column("Value", style="metric_value", justify="right")

        valuation_table.add_row("Market Cap", format_large_number(fund.market_cap))
        valuation_table.add_row("P/E Ratio", self._format_with_assessment(fund.pe_ratio, "pe"))
        valuation_table.add_row("Forward P/E", format_ratio(fund.forward_pe))
        valuation_table.add_row("PEG Ratio", self._format_with_assessment(fund.peg_ratio, "peg"))
        valuation_table.add_row("Price/Book", format_ratio(fund.price_to_book))
        valuation_table.add_row("Price/Sales", format_ratio(fund.price_to_sales))

        # Profitability Table
        profit_table = Table(title="Profitability", show_header=True, header_style="bold")
        profit_table.add_column("Metric", style="metric_name", width=20)
        profit_table.add_column("Value", style="metric_value", justify="right")

        profit_table.add_row("Profit Margin", self._format_margin(fund.profit_margin))
        profit_table.add_row("Operating Margin", self._format_margin(fund.operating_margin))
        profit_table.add_row("Gross Margin", self._format_margin(fund.gross_margin))
        profit_table.add_row("ROE", self._format_margin(fund.return_on_equity))
        profit_table.add_row("ROA", self._format_margin(fund.return_on_assets))

        # Display tables side by side
        self.console.print(Columns([valuation_table, profit_table], expand=True))

        # Financial Health Table
        health_table = Table(title="Financial Health", show_header=True, header_style="bold")
        health_table.add_column("Metric", style="metric_name", width=20)
        health_table.add_column("Value", style="metric_value", justify="right")

        health_table.add_row("Total Debt", format_large_number(fund.total_debt))
        health_table.add_row("Total Cash", format_large_number(fund.total_cash))
        health_table.add_row("Debt/Equity", self._format_with_assessment(fund.debt_to_equity, "de"))
        health_table.add_row("Current Ratio", self._format_with_assessment(fund.current_ratio, "cr"))
        health_table.add_row("Free Cash Flow", format_large_number(fund.free_cash_flow))

        # Growth Table
        growth_table = Table(title="Growth & Income", show_header=True, header_style="bold")
        growth_table.add_column("Metric", style="metric_name", width=20)
        growth_table.add_column("Value", style="metric_value", justify="right")

        growth_table.add_row("Revenue", format_large_number(fund.revenue))
        growth_table.add_row("Revenue Growth", self._format_growth(fund.revenue_growth))
        growth_table.add_row("EPS", format_currency(fund.eps))
        growth_table.add_row("Dividend Yield", format_yield(fund.dividend_yield))
        growth_table.add_row("Payout Ratio", format_percentage(fund.payout_ratio))

        # Display tables side by side
        self.console.print(Columns([health_table, growth_table], expand=True))

        # Analyst Ratings
        if analysis.analyst_rating or analysis.target_mean_price:
            analyst_info = []
            if analysis.analyst_rating:
                analyst_info.append(f"[bold]Rating:[/bold] {analysis.analyst_rating.upper()}")
            if analysis.target_mean_price:
                analyst_info.append(f"[bold]Target Price:[/bold] {format_currency(analysis.target_mean_price)}")
            if analysis.number_of_analysts:
                analyst_info.append(f"[dim]({analysis.number_of_analysts} analysts)[/dim]")

            self.console.print(Panel(
                " | ".join(analyst_info),
                title="Analyst Consensus",
                border_style="yellow"
            ))

    def display_ai_insight(self, insight: AIInsight):
        """Display Claude-generated insights."""
        # Summary panel
        self.console.print(Panel(
            insight.summary,
            title="AI Analysis Summary",
            border_style="green",
            padding=(1, 2)
        ))

        # SWOT Analysis in panels
        strengths_content = "\n".join(f"[green]+ {s}[/green]" for s in insight.strengths) or "[dim]None identified[/dim]"
        weaknesses_content = "\n".join(f"[red]- {w}[/red]" for w in insight.weaknesses) or "[dim]None identified[/dim]"
        opportunities_content = "\n".join(f"[cyan]→ {o}[/cyan]" for o in insight.opportunities) or "[dim]None identified[/dim]"
        risks_content = "\n".join(f"[yellow]! {r}[/yellow]" for r in insight.risks) or "[dim]None identified[/dim]"

        # Display SWOT in columns
        self.console.print(Columns([
            Panel(strengths_content, title="Strengths", border_style="green"),
            Panel(weaknesses_content, title="Weaknesses", border_style="red"),
        ], expand=True))

        self.console.print(Columns([
            Panel(opportunities_content, title="Opportunities", border_style="cyan"),
            Panel(risks_content, title="Risks", border_style="yellow"),
        ], expand=True))

        # Valuation and metrics analysis
        if insight.valuation_assessment:
            self.console.print(Panel(
                insight.valuation_assessment,
                title="Valuation Assessment",
                border_style="blue"
            ))

        if insight.key_metrics_analysis:
            self.console.print(Panel(
                insight.key_metrics_analysis,
                title="Key Metrics Analysis",
                border_style="blue"
            ))

        # Recommendation
        if insight.recommendation:
            rec_color = self._get_recommendation_color(insight.recommendation)
            rec_text = insight.recommendation.value.replace("_", " ").upper()
            confidence = f" (Confidence: {insight.confidence_level})" if insight.confidence_level else ""

            self.console.print(Panel(
                f"[bold {rec_color}]{rec_text}[/bold {rec_color}]{confidence}",
                title="AI Recommendation",
                border_style=rec_color,
                padding=(0, 2)
            ))

        # Disclaimer
        self.console.print(f"\n[dim italic]{insight.disclaimer}[/dim italic]")

    def _format_with_assessment(self, value: Optional[float], metric_type: str) -> str:
        """Format a value with color-coded assessment."""
        if value is None:
            return "N/A"

        formatted = format_ratio(value)

        # Add color based on metric type and value
        if metric_type == "pe":
            if value < 15:
                return f"[green]{formatted}[/green]"
            elif value > 30:
                return f"[red]{formatted}[/red]"
        elif metric_type == "peg":
            if value < 1:
                return f"[green]{formatted}[/green]"
            elif value > 2:
                return f"[red]{formatted}[/red]"
        elif metric_type == "de":
            if value < 50:
                return f"[green]{formatted}[/green]"
            elif value > 150:
                return f"[red]{formatted}[/red]"
        elif metric_type == "cr":
            if value > 1.5:
                return f"[green]{formatted}[/green]"
            elif value < 1:
                return f"[red]{formatted}[/red]"

        return formatted

    def _format_margin(self, value: Optional[float]) -> str:
        """Format margin with color coding."""
        if value is None:
            return "N/A"

        formatted = format_percentage(value)
        if value > 0.15:  # > 15%
            return f"[green]{formatted}[/green]"
        elif value < 0:
            return f"[red]{formatted}[/red]"
        return formatted

    def _format_growth(self, value: Optional[float]) -> str:
        """Format growth with color coding."""
        if value is None:
            return "N/A"

        formatted = format_percentage(value)
        if value > 0:
            return f"[green]{formatted}[/green]"
        elif value < 0:
            return f"[red]{formatted}[/red]"
        return formatted

    def _get_recommendation_color(self, rec: RecommendationType) -> str:
        """Get color for recommendation type."""
        colors = {
            RecommendationType.STRONG_BUY: "green",
            RecommendationType.BUY: "green",
            RecommendationType.HOLD: "yellow",
            RecommendationType.SELL: "red",
            RecommendationType.STRONG_SELL: "red",
        }
        return colors.get(rec, "white")

    # ============ Portfolio Display Methods ============

    def display_portfolio(self, portfolio: Portfolio):
        """Display complete portfolio view."""
        # Summary panel
        change_color = "green" if portfolio.total_unrealized_gain >= 0 else "red"
        day_color = "green" if portfolio.total_day_change >= 0 else "red"
        gain_sign = "+" if portfolio.total_unrealized_gain >= 0 else ""
        day_sign = "+" if portfolio.total_day_change >= 0 else ""

        summary_content = (
            f"[bold]Total Value:[/bold] {format_currency(portfolio.total_current_value)}\n"
            f"[bold]Cost Basis:[/bold] {format_currency(portfolio.total_cost_basis)}\n"
            f"[bold]Total Gain/Loss:[/bold] [{change_color}]{gain_sign}{format_currency(portfolio.total_unrealized_gain)} "
            f"({gain_sign}{portfolio.total_unrealized_gain_pct:.1f}%)[/{change_color}]\n"
            f"[bold]Today's Change:[/bold] [{day_color}]{day_sign}{format_currency(portfolio.total_day_change)} "
            f"({day_sign}{portfolio.total_day_change_pct:.1f}%)[/{day_color}]\n"
            f"[dim]{portfolio.num_positions} positions across {portfolio.num_symbols} symbols[/dim]"
        )

        self.console.print(Panel(summary_content, title="Portfolio Summary", border_style="cyan"))

        # Holdings table
        table = Table(title="Holdings", show_header=True, header_style="bold")
        table.add_column("Symbol", style="bold")
        table.add_column("Shares", justify="right")
        table.add_column("Avg Cost", justify="right")
        table.add_column("Price", justify="right")
        table.add_column("Value", justify="right")
        table.add_column("Gain/Loss", justify="right")
        table.add_column("Weight", justify="right")

        for agg in portfolio.aggregated:
            gain_str = "N/A"
            if agg.unrealized_gain is not None:
                gain_color = "green" if agg.unrealized_gain >= 0 else "red"
                sign = "+" if agg.unrealized_gain >= 0 else ""
                gain_str = f"[{gain_color}]{sign}{format_currency(agg.unrealized_gain)} ({sign}{agg.unrealized_gain_pct:.1f}%)[/{gain_color}]"

            table.add_row(
                agg.symbol,
                f"{agg.total_shares:.2f}",
                format_currency(agg.average_cost),
                format_currency(agg.current_price) if agg.current_price else "N/A",
                format_currency(agg.current_value) if agg.current_value else "N/A",
                gain_str,
                f"{agg.weight_pct:.1f}%" if agg.weight_pct else "N/A",
            )

        self.console.print(table)

        # Sector allocation
        if portfolio.sector_allocation:
            sector_table = Table(title="Sector Allocation", show_header=True, header_style="bold")
            sector_table.add_column("Sector")
            sector_table.add_column("Weight", justify="right")
            sector_table.add_column("", width=20)

            for sector, weight in sorted(
                portfolio.sector_allocation.items(),
                key=lambda x: x[1],
                reverse=True,
            ):
                bar_len = int(weight / 5)
                bar = "[cyan]" + "█" * bar_len + "[/cyan]"
                sector_table.add_row(sector, f"{weight:.1f}%", bar)

            self.console.print(sector_table)

    def display_portfolio_summary(self, portfolio: Portfolio):
        """Display just the portfolio summary (for use before AI analysis)."""
        change_color = "green" if portfolio.total_unrealized_gain >= 0 else "red"
        gain_sign = "+" if portfolio.total_unrealized_gain >= 0 else ""

        summary_content = (
            f"[bold]Total Value:[/bold] {format_currency(portfolio.total_current_value)} | "
            f"[bold]Gain/Loss:[/bold] [{change_color}]{gain_sign}{portfolio.total_unrealized_gain_pct:.1f}%[/{change_color}] | "
            f"[dim]{portfolio.num_symbols} holdings[/dim]"
        )

        self.console.print(Panel(summary_content, title="Portfolio", border_style="cyan"))

    def display_positions_for_removal(self, positions: list):
        """Display positions in a table for removal selection."""
        table = Table(title="Your Positions", show_header=True, header_style="bold")
        table.add_column("ID", style="bold cyan")
        table.add_column("Symbol", style="bold")
        table.add_column("Shares", justify="right")
        table.add_column("Purchase Price", justify="right")
        table.add_column("Purchase Date")
        table.add_column("Notes")

        for pos in positions:
            table.add_row(
                str(pos.id),
                pos.symbol,
                f"{pos.shares:.2f}",
                format_currency(pos.purchase_price),
                pos.purchase_date.isoformat(),
                pos.notes or "",
            )

        self.console.print(table)

    def display_portfolio_analysis(self, analysis: PortfolioAnalysis):
        """Display AI portfolio analysis."""
        # Summary
        self.console.print(Panel(
            analysis.summary,
            title="AI Portfolio Analysis",
            border_style="green",
            padding=(1, 2),
        ))

        # Risk assessment
        risk_content = (
            f"[bold]Concentration Risk:[/bold] {analysis.concentration_risk_score or 'N/A'}\n"
            f"[bold]Diversification:[/bold] {analysis.diversification_score or 'N/A'}"
        )
        self.console.print(Panel(risk_content, title="Risk Assessment", border_style="yellow"))

        # Display insights by category
        if analysis.rebalancing_insights:
            self.console.print_subheader("Rebalancing Insights")
            for insight in analysis.rebalancing_insights:
                self._display_insight(insight, "blue")

        if analysis.risk_insights:
            self.console.print_subheader("Risk Insights")
            for insight in analysis.risk_insights:
                self._display_insight(insight, "yellow")

        if analysis.tax_insights:
            self.console.print_subheader("Tax Insights")
            for insight in analysis.tax_insights:
                self._display_insight(insight, "cyan")

        # Tax opportunities
        if analysis.tax_loss_harvesting_opportunities:
            content = "\n".join(f"[green]•[/green] {opp}" for opp in analysis.tax_loss_harvesting_opportunities)
            self.console.print(Panel(content, title="Tax-Loss Harvesting Opportunities", border_style="green"))

        # Wash sale warnings
        if analysis.wash_sale_warnings:
            content = "\n".join(f"[red]![/red] {warn}" for warn in analysis.wash_sale_warnings)
            self.console.print(Panel(content, title="Wash Sale Warnings", border_style="red"))

        # Action items
        if analysis.action_items:
            self.console.print_subheader("Recommended Actions")
            for item in analysis.action_items:
                urgency_color = {
                    "immediate": "red",
                    "this_week": "yellow",
                    "this_month": "blue",
                    "when_convenient": "dim",
                }.get(item.action_urgency or "", "white")

                self.console.print(
                    f"[{urgency_color}]•[/{urgency_color}] [bold]{item.title}[/bold]: {item.recommended_action or item.description}"
                )

        # Hold recommendations
        if analysis.hold_recommendations:
            content = "\n".join(f"[green]✓[/green] {rec}" for rec in analysis.hold_recommendations)
            self.console.print(Panel(content, title="Continue Holding", border_style="green"))

        # Overall health
        if analysis.overall_health:
            self.console.print(Panel(
                analysis.overall_health,
                title="Overall Portfolio Health",
                border_style="cyan",
            ))

        # Disclaimer
        self.console.print(f"\n[dim italic]{analysis.disclaimer}[/dim italic]")

    def _display_insight(self, insight: PortfolioInsight, color: str):
        """Display a single insight panel."""
        severity_icon = {
            "info": "ℹ",
            "warning": "⚠",
            "alert": "🔔",
            "action_required": "❗",
        }.get(insight.severity.value, "•")

        content = insight.description
        if insight.affected_symbols:
            content += f"\n[dim]Affected: {', '.join(insight.affected_symbols)}[/dim]"
        if insight.recommended_action:
            content += f"\n[bold]Action:[/bold] {insight.recommended_action}"

        self.console.print(Panel(
            content,
            title=f"{severity_icon} {insight.title}",
            border_style=color,
        ))

    # ============ News Display Methods ============

    def display_news(
        self,
        symbol: str,
        articles: List[NewsArticle],
        sentiments: Optional[Dict[int, ArticleSentiment]] = None,
    ):
        """Display news articles for a stock with optional AI sentiment."""
        if not articles:
            self.console.print_info(f"No news articles found for {symbol}")
            return

        # Sentiment styling
        sentiment_colors = {
            NewsSentiment.VERY_BULLISH: "bold green",
            NewsSentiment.BULLISH: "green",
            NewsSentiment.NEUTRAL: "yellow",
            NewsSentiment.BEARISH: "red",
            NewsSentiment.VERY_BEARISH: "bold red",
        }
        sentiment_icons = {
            NewsSentiment.VERY_BULLISH: "▲▲",
            NewsSentiment.BULLISH: "▲",
            NewsSentiment.NEUTRAL: "●",
            NewsSentiment.BEARISH: "▼",
            NewsSentiment.VERY_BEARISH: "▼▼",
        }

        # Header
        header_text = f"[bold]Latest News for {symbol}[/bold]"
        if sentiments:
            header_text += "\n[dim]AI sentiment analysis enabled[/dim]"
        self.console.print(Panel(header_text, border_style="cyan"))

        for i, article in enumerate(articles):
            # Get sentiment for this article
            sentiment_info = sentiments.get(i) if sentiments else None

            # Build article content
            content = f"[bold]{article.title}[/bold]\n"

            # Add sentiment badge if available
            if sentiment_info:
                s_color = sentiment_colors.get(sentiment_info.sentiment, "white")
                s_icon = sentiment_icons.get(sentiment_info.sentiment, "●")
                s_label = sentiment_info.sentiment.value.replace("_", " ").upper()
                content += f"[{s_color}]{s_icon} {s_label}[/{s_color}]"
                if sentiment_info.summary:
                    content += f" [dim]— {sentiment_info.summary}[/dim]"
                content += "\n"

            if article.summary:
                # Truncate summary if too long
                summary = article.summary[:200] + "..." if len(article.summary) > 200 else article.summary
                content += f"\n{summary}\n"

            content += f"\n[dim]{article.publisher} • {article.time_ago}[/dim]"
            if article.url:
                content += f"\n[link={article.url}][blue]{article.url}[/blue][/link]"

            # Color the panel border based on sentiment
            border_color = "blue"
            if sentiment_info:
                border_color = sentiment_colors.get(sentiment_info.sentiment, "blue").replace("bold ", "")

            self.console.print(Panel(
                content,
                title=f"[{i + 1}]",
                border_style=border_color,
                padding=(0, 1),
            ))

    def display_news_analysis(self, analysis: NewsAnalysis):
        """Display AI-generated news analysis."""
        # Sentiment color mapping
        sentiment_colors = {
            NewsSentiment.VERY_BULLISH: "bold green",
            NewsSentiment.BULLISH: "green",
            NewsSentiment.NEUTRAL: "yellow",
            NewsSentiment.BEARISH: "red",
            NewsSentiment.VERY_BEARISH: "bold red",
        }

        sentiment_icons = {
            NewsSentiment.VERY_BULLISH: "▲▲",
            NewsSentiment.BULLISH: "▲",
            NewsSentiment.NEUTRAL: "●",
            NewsSentiment.BEARISH: "▼",
            NewsSentiment.VERY_BEARISH: "▼▼",
        }

        # Header with sentiment
        sentiment_color = sentiment_colors.get(analysis.overall_sentiment, "white")
        sentiment_icon = sentiment_icons.get(analysis.overall_sentiment, "●")
        sentiment_text = analysis.overall_sentiment.value.replace("_", " ").upper()

        header_content = (
            f"[bold]{analysis.symbol}[/bold] News Analysis\n"
            f"[dim]{analysis.articles_analyzed} articles analyzed ({analysis.date_range})[/dim]\n\n"
            f"[{sentiment_color}]{sentiment_icon} Overall Sentiment: {sentiment_text}[/{sentiment_color}]\n"
            f"[dim]Confidence: {analysis.confidence_level}[/dim]"
        )

        self.console.print(Panel(header_content, title="AI News Analysis", border_style="cyan"))

        # Sentiment reasoning
        self.console.print(Panel(
            analysis.sentiment_reasoning,
            title="Sentiment Assessment",
            border_style=sentiment_color.replace("bold ", ""),
        ))

        # Summary
        self.console.print(Panel(
            analysis.summary,
            title="Executive Summary",
            border_style="blue",
        ))

        # Key themes table
        if analysis.key_themes:
            theme_table = Table(title="Key Themes", show_header=True, header_style="bold")
            theme_table.add_column("Theme", style="bold")
            theme_table.add_column("Description")
            theme_table.add_column("Sentiment", justify="center")
            theme_table.add_column("Relevance", justify="center")

            for theme in analysis.key_themes:
                theme_color = sentiment_colors.get(theme.sentiment, "white")
                theme_icon = sentiment_icons.get(theme.sentiment, "●")
                theme_sentiment = f"[{theme_color}]{theme_icon}[/{theme_color}]"

                relevance_color = {"high": "green", "medium": "yellow", "low": "dim"}.get(
                    theme.relevance.lower(), "white"
                )

                theme_table.add_row(
                    theme.theme,
                    theme.description,
                    theme_sentiment,
                    f"[{relevance_color}]{theme.relevance.upper()}[/{relevance_color}]",
                )

            self.console.print(theme_table)

        # Impact analysis
        impact_content = (
            f"[bold cyan]Short-term (days to weeks):[/bold cyan]\n{analysis.short_term_impact}\n\n"
            f"[bold cyan]Long-term (months+):[/bold cyan]\n{analysis.long_term_impact}"
        )
        self.console.print(Panel(impact_content, title="Potential Impact", border_style="yellow"))

        # Key takeaways
        if analysis.key_takeaways:
            takeaways = "\n".join(f"[green]•[/green] {t}" for t in analysis.key_takeaways)
            self.console.print(Panel(takeaways, title="Key Takeaways", border_style="green"))

        # Watch items
        if analysis.watch_items:
            watch = "\n".join(f"[yellow]![/yellow] {w}" for w in analysis.watch_items)
            self.console.print(Panel(watch, title="Watch Items", border_style="yellow"))

        # Source articles
        if analysis.source_articles:
            sources_content = ""
            for article in analysis.source_articles:
                title = article.title[:70] + "..." if len(article.title) > 70 else article.title
                sources_content += f"[bold]•[/bold] {title}\n"
                sources_content += f"  [dim]{article.publisher} • {article.time_ago}[/dim]\n"
                sources_content += f"  [link={article.url}][blue underline]{article.url}[/blue underline][/link]\n\n"

            self.console.print(Panel(
                sources_content.strip(),
                title="Source Articles",
                border_style="cyan",
                padding=(1, 2),
            ))

        # Disclaimer
        self.console.print(f"\n[dim italic]{analysis.disclaimer}[/dim italic]")

    def display_portfolio_news_analysis(self, analysis: PortfolioNewsAnalysis):
        """Display AI-generated portfolio-wide news analysis."""
        sentiment_colors = {
            NewsSentiment.VERY_BULLISH: "bold green",
            NewsSentiment.BULLISH: "green",
            NewsSentiment.NEUTRAL: "yellow",
            NewsSentiment.BEARISH: "red",
            NewsSentiment.VERY_BEARISH: "bold red",
        }
        sentiment_icons = {
            NewsSentiment.VERY_BULLISH: "▲▲",
            NewsSentiment.BULLISH: "▲",
            NewsSentiment.NEUTRAL: "●",
            NewsSentiment.BEARISH: "▼",
            NewsSentiment.VERY_BEARISH: "▼▼",
        }

        # Header
        s_color = sentiment_colors.get(analysis.portfolio_sentiment, "white")
        s_icon = sentiment_icons.get(analysis.portfolio_sentiment, "●")
        s_text = analysis.portfolio_sentiment.value.replace("_", " ").upper()

        header = (
            f"[bold]Portfolio News Analysis[/bold]\n"
            f"[dim]{analysis.stocks_analyzed} holdings • {analysis.total_articles_analyzed} articles • {analysis.date_range}[/dim]\n\n"
            f"[{s_color}]{s_icon} Portfolio Sentiment: {s_text}[/{s_color}]\n"
            f"[dim]{analysis.sentiment_breakdown} | Confidence: {analysis.confidence_level}[/dim]"
        )
        self.console.print(Panel(header, title="AI Portfolio News Analysis", border_style="cyan"))

        # Summary
        self.console.print(Panel(analysis.summary, title="Executive Summary", border_style="blue"))

        # Stock sentiment with source articles
        if analysis.stock_summaries:
            self.console.print_subheader("Holdings News & Sources")

            for s in analysis.stock_summaries:
                color = sentiment_colors.get(s.sentiment, "white").replace("bold ", "")
                icon = sentiment_icons.get(s.sentiment, "●")
                sentiment_label = s.sentiment.value.replace("_", " ").title()

                # Build content with headline summary and sources
                content = f"[{color}]{icon}[/{color}] [bold]{sentiment_label}[/bold] ({s.article_count} articles)\n\n"
                content += f"{s.headline_summary}\n"

                if s.sentiment_driver:
                    content += f"\n[dim]Driver: {s.sentiment_driver}[/dim]\n"

                # Add source articles
                if s.source_articles:
                    content += "\n[bold cyan]Sources:[/bold cyan]\n"
                    for article in s.source_articles:
                        # Truncate long titles
                        title = article.title[:60] + "..." if len(article.title) > 60 else article.title
                        content += f"  [dim]•[/dim] {title}\n"
                        content += f"    [dim]{article.publisher} • {article.time_ago}[/dim]\n"
                        content += f"    [link={article.url}][blue underline]{article.url}[/blue underline][/link]\n"

                self.console.print(Panel(
                    content.strip(),
                    title=f"[bold]{s.symbol}[/bold]",
                    border_style=color,
                    padding=(1, 2),
                ))

        # Sector trends
        if analysis.sector_trends:
            self.console.print_subheader("Sector Trends")
            for trend in analysis.sector_trends:
                color = sentiment_colors.get(trend.sentiment, "white").replace("bold ", "")
                icon = sentiment_icons.get(trend.sentiment, "●")
                holdings = ", ".join(trend.affected_holdings) if trend.affected_holdings else "N/A"
                content = f"[{color}]{icon}[/{color}] {trend.key_development}\n[dim]Holdings: {holdings}[/dim]"
                self.console.print(Panel(content, title=trend.sector, border_style=color))

        # Correlated risks
        if analysis.correlated_risks:
            risks = "\n".join(f"[red]![/red] {r}" for r in analysis.correlated_risks)
            self.console.print(Panel(risks, title="Correlated Risks", border_style="red"))

        # Cross-portfolio themes
        if analysis.cross_portfolio_themes:
            themes = "\n".join(f"[cyan]•[/cyan] {t}" for t in analysis.cross_portfolio_themes)
            self.console.print(Panel(themes, title="Cross-Portfolio Themes", border_style="cyan"))

        # Alerts
        if analysis.alerts:
            self.console.print_subheader("Alerts")
            urgency_colors = {"immediate": "red", "this_week": "yellow", "monitor": "blue"}
            alert_icons = {"risk": "⚠", "opportunity": "★", "information": "ℹ"}

            for alert in analysis.alerts:
                color = urgency_colors.get(alert.urgency, "white")
                icon = alert_icons.get(alert.alert_type, "•")
                content = alert.description
                if alert.affected_symbols:
                    content += f"\n[dim]Affected: {', '.join(alert.affected_symbols)}[/dim]"
                if alert.recommended_action:
                    content += f"\n[bold]Action:[/bold] {alert.recommended_action}"
                label = alert.urgency.replace("_", " ").upper()
                self.console.print(Panel(content, title=f"{icon} [{label}] {alert.title}", border_style=color))

        # Opportunities
        if analysis.opportunities:
            opps = "\n".join(f"[green]★[/green] {o}" for o in analysis.opportunities)
            self.console.print(Panel(opps, title="Opportunities", border_style="green"))

        # Portfolio health & takeaways
        if analysis.portfolio_news_health:
            self.console.print(Panel(analysis.portfolio_news_health, title="Portfolio News Health", border_style="cyan"))

        if analysis.key_takeaways:
            takeaways = "\n".join(f"[green]•[/green] {t}" for t in analysis.key_takeaways)
            self.console.print(Panel(takeaways, title="Key Takeaways", border_style="green"))

        self.console.print(f"\n[dim italic]{analysis.disclaimer}[/dim italic]")

    # ============ History & Performance Display Methods ============

    def display_history(self, history: PortfolioHistory):
        """Display portfolio history with a text-based chart."""
        if not history.snapshots:
            self.console.print_info(
                "No history available yet. Portfolio snapshots are saved when you view your portfolio."
            )
            return

        # Summary panel
        change_color = "green" if (history.total_change or 0) >= 0 else "red"
        change_sign = "+" if (history.total_change or 0) >= 0 else ""

        summary_content = (
            f"[bold]Period:[/bold] {history.earliest_date} to {history.latest_date}\n"
            f"[bold]Starting Value:[/bold] {format_currency(history.starting_value)}\n"
            f"[bold]Current Value:[/bold] {format_currency(history.current_value)}\n"
            f"[bold]Change:[/bold] [{change_color}]{change_sign}{format_currency(history.total_change)} "
            f"({change_sign}{history.total_change_pct:.1f}%)[/{change_color}]\n\n"
            f"[bold cyan]High:[/bold cyan] {format_currency(history.high_value)} on {history.high_date}\n"
            f"[bold yellow]Low:[/bold yellow] {format_currency(history.low_value)} on {history.low_date}"
        )

        self.console.print(Panel(summary_content, title="Portfolio History", border_style="cyan"))

        # Text-based chart
        self._display_value_chart(history)

        # Data table
        table = Table(title="Daily Snapshots", show_header=True, header_style="bold")
        table.add_column("Date", style="dim")
        table.add_column("Value", justify="right")
        table.add_column("Gain/Loss", justify="right")
        table.add_column("Change %", justify="right")

        # Show last 14 days or all if less
        display_snapshots = history.snapshots[-14:]
        for snap in display_snapshots:
            gain_color = "green" if snap.total_gain >= 0 else "red"
            gain_sign = "+" if snap.total_gain >= 0 else ""
            table.add_row(
                snap.snapshot_date.isoformat(),
                format_currency(snap.total_value),
                f"[{gain_color}]{gain_sign}{format_currency(snap.total_gain)}[/{gain_color}]",
                f"[{gain_color}]{gain_sign}{snap.total_gain_pct:.1f}%[/{gain_color}]",
            )

        self.console.print(table)

    def _display_value_chart(self, history: PortfolioHistory):
        """Display a simple text-based line chart of portfolio values."""
        snapshots = history.snapshots
        if len(snapshots) < 2:
            return

        # Chart dimensions
        width = 60
        height = 10

        values = [s.total_value for s in snapshots]
        min_val = min(values)
        max_val = max(values)
        val_range = max_val - min_val if max_val != min_val else 1

        # Build chart
        chart_lines = []
        for row in range(height, -1, -1):
            line = ""
            threshold = min_val + (val_range * row / height)

            for i, val in enumerate(values):
                if len(values) > width:
                    # Sample if too many points
                    if i % (len(values) // width) != 0:
                        continue

                if val >= threshold:
                    # Determine color based on gain/loss relative to start
                    if val >= values[0]:
                        line += "[green]█[/green]"
                    else:
                        line += "[red]█[/red]"
                else:
                    line += " "

            chart_lines.append(line)

        # Add labels
        chart_content = f"[dim]{format_currency(max_val):>12}[/dim] ┤\n"
        for i, line in enumerate(chart_lines):
            if i == len(chart_lines) // 2:
                mid_val = min_val + val_range / 2
                chart_content += f"[dim]{format_currency(mid_val):>12}[/dim] ┤{line}\n"
            elif i == len(chart_lines) - 1:
                chart_content += f"[dim]{format_currency(min_val):>12}[/dim] ┤{line}\n"
            else:
                chart_content += f"{'':>12} │{line}\n"

        chart_content += f"{'':>12} └{'─' * min(len(values), width)}\n"
        chart_content += f"{'':>12}  [dim]{history.earliest_date}{'':>{min(len(values), width) - 20}}{history.latest_date}[/dim]"

        self.console.print(Panel(chart_content, title="Value Over Time", border_style="blue"))

    def display_performance(self, performance: PortfolioPerformance):
        """Display portfolio performance breakdown by holdings."""
        if not performance.holdings:
            self.console.print_info("No holdings to analyze.")
            return

        # Summary panel
        gain_color = "green" if performance.total_gain >= 0 else "red"
        gain_sign = "+" if performance.total_gain >= 0 else ""

        summary_content = (
            f"[bold]Total Value:[/bold] {format_currency(performance.total_value)}\n"
            f"[bold]Cost Basis:[/bold] {format_currency(performance.total_cost_basis)}\n"
            f"[bold]Total Gain/Loss:[/bold] [{gain_color}]{gain_sign}{format_currency(performance.total_gain)} "
            f"({gain_sign}{performance.total_gain_pct:.1f}%)[/{gain_color}]"
        )

        self.console.print(Panel(summary_content, title="Performance Summary", border_style="cyan"))

        # Top Gainers
        if performance.top_gainers:
            self.console.print_subheader("Top Gainers")
            gainers_table = Table(show_header=True, header_style="bold green")
            gainers_table.add_column("Symbol", style="bold")
            gainers_table.add_column("Gain", justify="right")
            gainers_table.add_column("Return", justify="right")
            gainers_table.add_column("Contribution", justify="right")
            gainers_table.add_column("", width=20)

            for h in performance.top_gainers:
                bar_len = min(int(h.contribution_pct / 5), 20) if h.contribution_pct > 0 else 0
                bar = "[green]" + "█" * bar_len + "[/green]"
                gainers_table.add_row(
                    h.symbol,
                    f"[green]+{format_currency(h.unrealized_gain)}[/green]",
                    f"[green]+{h.unrealized_gain_pct:.1f}%[/green]",
                    f"[green]+{h.contribution_pct:.1f}%[/green]",
                    bar,
                )

            self.console.print(gainers_table)

        # Top Losers
        if performance.top_losers:
            self.console.print_subheader("Top Losers")
            losers_table = Table(show_header=True, header_style="bold red")
            losers_table.add_column("Symbol", style="bold")
            losers_table.add_column("Loss", justify="right")
            losers_table.add_column("Return", justify="right")
            losers_table.add_column("Contribution", justify="right")
            losers_table.add_column("", width=20)

            for h in performance.top_losers:
                bar_len = min(int(abs(h.contribution_pct) / 5), 20) if h.contribution_pct < 0 else 0
                bar = "[red]" + "█" * bar_len + "[/red]"
                losers_table.add_row(
                    h.symbol,
                    f"[red]{format_currency(h.unrealized_gain)}[/red]",
                    f"[red]{h.unrealized_gain_pct:.1f}%[/red]",
                    f"[red]{h.contribution_pct:.1f}%[/red]",
                    bar,
                )

            self.console.print(losers_table)

        # All holdings performance table
        self.console.print_subheader("All Holdings")
        table = Table(show_header=True, header_style="bold")
        table.add_column("Symbol", style="bold")
        table.add_column("Sector", style="dim")
        table.add_column("Value", justify="right")
        table.add_column("Gain/Loss", justify="right")
        table.add_column("Return", justify="right")
        table.add_column("Weight", justify="right")
        table.add_column("Contribution", justify="right")

        for h in performance.holdings:
            gain_color = "green" if h.unrealized_gain >= 0 else "red"
            gain_sign = "+" if h.unrealized_gain >= 0 else ""
            contrib_sign = "+" if h.contribution_pct >= 0 else ""

            table.add_row(
                h.symbol,
                h.sector or "N/A",
                format_currency(h.current_value),
                f"[{gain_color}]{gain_sign}{format_currency(h.unrealized_gain)}[/{gain_color}]",
                f"[{gain_color}]{gain_sign}{h.unrealized_gain_pct:.1f}%[/{gain_color}]",
                f"{h.weight_pct:.1f}%",
                f"[{gain_color}]{contrib_sign}{h.contribution_pct:.1f}%[/{gain_color}]",
            )

        self.console.print(table)

        # Sector performance
        if performance.sector_performance:
            self.console.print_subheader("Sector Performance")
            sector_table = Table(show_header=True, header_style="bold")
            sector_table.add_column("Sector")
            sector_table.add_column("Return", justify="right")
            sector_table.add_column("", width=25)

            sorted_sectors = sorted(
                performance.sector_performance.items(),
                key=lambda x: x[1],
                reverse=True
            )

            for sector, return_pct in sorted_sectors:
                color = "green" if return_pct >= 0 else "red"
                sign = "+" if return_pct >= 0 else ""
                bar_len = min(int(abs(return_pct) / 4), 25)
                bar = f"[{color}]" + "█" * bar_len + f"[/{color}]"

                sector_table.add_row(
                    sector,
                    f"[{color}]{sign}{return_pct:.1f}%[/{color}]",
                    bar,
                )

            self.console.print(sector_table)
