"""Newsletter service for generating portfolio news emails."""

from datetime import datetime
from typing import Dict, List, Optional

from app.config import Settings
from app.models.ai_response import NewsSentiment, PortfolioNewsAnalysis
from app.models.portfolio import Portfolio
from app.services.ai_service import AIService
from app.services.email_service import EmailService
from app.services.portfolio_service import PortfolioService
from app.services.rate_limiter import RateLimiter
from app.services.stock_service import StockService
from app.utils.exceptions import NewsletterError


class NewsletterService:
    """Service for generating and sending portfolio newsletters."""

    def __init__(self, settings: Settings):
        """
        Initialize the newsletter service.

        Args:
            settings: Application settings
        """
        self.settings = settings

        # Initialize rate limiters
        yfinance_limiter = RateLimiter(settings.yfinance_requests_per_minute)
        claude_limiter = RateLimiter(settings.claude_requests_per_minute)

        # Initialize services
        self.stock_service = StockService(yfinance_limiter)
        self.portfolio_service = PortfolioService(
            settings.portfolio_db_path, self.stock_service
        )
        self.ai_service = AIService(settings, claude_limiter)
        self.email_service = EmailService(settings)

    def generate_newsletter(self) -> tuple[str, str, PortfolioNewsAnalysis]:
        """
        Generate newsletter content from portfolio news analysis.

        Returns:
            Tuple of (subject, html_content, analysis)

        Raises:
            NewsletterError: If generation fails
        """
        # Load portfolio
        portfolio = self.portfolio_service.get_portfolio(include_prices=True)

        if portfolio.num_positions == 0:
            raise NewsletterError("Portfolio is empty. Add positions first.")

        # Get unique symbols
        symbols = list({agg.symbol for agg in portfolio.aggregated})

        # Fetch news for each symbol
        news_by_symbol: Dict[str, List] = {}
        sector_by_symbol: Dict[str, str] = {}
        weight_by_symbol: Dict[str, float] = {}

        for agg in portfolio.aggregated:
            try:
                articles = self.stock_service.get_news(agg.symbol, limit=10)
                if articles:
                    news_by_symbol[agg.symbol] = articles
                    sector_by_symbol[agg.symbol] = agg.sector or "Unknown"
                    weight_by_symbol[agg.symbol] = agg.weight_pct or 0
            except Exception:
                # Skip symbols where news fetch fails
                pass

        if not news_by_symbol:
            raise NewsletterError("No news found for any portfolio holdings.")

        # Analyze with AI
        analysis = self.ai_service.analyze_portfolio_news(
            news_by_symbol, sector_by_symbol, weight_by_symbol
        )

        # Generate HTML
        html_content = self._generate_html(portfolio, analysis)

        # Generate subject
        sentiment_text = analysis.portfolio_sentiment.value.replace("_", " ").title()
        subject = f"Portfolio News: {sentiment_text} - {datetime.now().strftime('%b %d, %Y')}"

        return subject, html_content, analysis

    def send_newsletter(self) -> None:
        """
        Generate and send the newsletter to configured recipients.

        Raises:
            NewsletterError: If sending fails
        """
        recipients = self.settings.get_newsletter_recipients()
        if not recipients:
            raise NewsletterError(
                "No newsletter recipients configured. "
                "Set NEWSLETTER_RECIPIENTS in your .env file."
            )

        subject, html_content, _ = self.generate_newsletter()

        self.email_service.send_email(
            recipients=recipients,
            subject=subject,
            html_content=html_content,
        )

    def _generate_html(
        self, portfolio: Portfolio, analysis: PortfolioNewsAnalysis
    ) -> str:
        """Generate HTML email content from portfolio news analysis."""
        sentiment_colors = {
            NewsSentiment.VERY_BULLISH: "#00d26a",
            NewsSentiment.BULLISH: "#7ed957",
            NewsSentiment.NEUTRAL: "#ffd166",
            NewsSentiment.BEARISH: "#ff9f43",
            NewsSentiment.VERY_BEARISH: "#ff6b6b",
        }

        sentiment_icons = {
            NewsSentiment.VERY_BULLISH: "&#9650;&#9650;",  # ▲▲
            NewsSentiment.BULLISH: "&#9650;",  # ▲
            NewsSentiment.NEUTRAL: "&#9679;",  # ●
            NewsSentiment.BEARISH: "&#9660;",  # ▼
            NewsSentiment.VERY_BEARISH: "&#9660;&#9660;",  # ▼▼
        }

        s_color = sentiment_colors.get(analysis.portfolio_sentiment, "#999")
        s_icon = sentiment_icons.get(analysis.portfolio_sentiment, "●")
        s_text = analysis.portfolio_sentiment.value.replace("_", " ").upper()

        # Format portfolio value
        total_value = f"${portfolio.total_current_value:,.2f}"
        gain_loss = portfolio.total_unrealized_gain
        gain_loss_pct = portfolio.total_unrealized_gain_pct
        gain_color = "#00d26a" if gain_loss >= 0 else "#ff6b6b"
        gain_sign = "+" if gain_loss >= 0 else ""

        # Build stock summaries HTML
        stock_summaries_html = ""
        for s in analysis.stock_summaries:
            color = sentiment_colors.get(s.sentiment, "#999")
            icon = sentiment_icons.get(s.sentiment, "●")
            label = s.sentiment.value.replace("_", " ").title()

            sources_html = ""
            if s.source_articles:
                sources_html = "<ul style='margin: 10px 0 0 0; padding-left: 20px;'>"
                for article in s.source_articles[:3]:  # Limit to 3 sources
                    sources_html += f"""
                    <li style="margin-bottom: 5px;">
                        <a href="{article.url}" style="color: #4a90d9; text-decoration: none;">{article.title[:60]}{'...' if len(article.title) > 60 else ''}</a>
                        <br><span style="color: #888; font-size: 12px;">{article.publisher} • {article.time_ago}</span>
                    </li>
                    """
                sources_html += "</ul>"

            stock_summaries_html += f"""
            <div style="background: #f8f9fa; border-left: 4px solid {color}; padding: 15px; margin-bottom: 15px; border-radius: 4px;">
                <div style="font-weight: bold; font-size: 16px; margin-bottom: 8px;">
                    {s.symbol}
                    <span style="color: {color}; font-size: 14px; margin-left: 10px;">{icon} {label}</span>
                </div>
                <p style="margin: 0; color: #333;">{s.headline_summary}</p>
                {f'<p style="margin: 8px 0 0 0; color: #666; font-size: 13px;"><em>Driver: {s.sentiment_driver}</em></p>' if s.sentiment_driver else ''}
                {sources_html}
            </div>
            """

        # Build alerts HTML
        alerts_html = ""
        if analysis.alerts:
            urgency_colors = {
                "immediate": "#ff6b6b",
                "this_week": "#ffd166",
                "monitor": "#4a90d9",
            }
            for alert in analysis.alerts:
                color = urgency_colors.get(alert.urgency, "#999")
                alerts_html += f"""
                <div style="background: #fff3cd; border-left: 4px solid {color}; padding: 12px; margin-bottom: 10px; border-radius: 4px;">
                    <strong style="color: {color};">[{alert.urgency.upper()}]</strong> {alert.title}
                    <p style="margin: 5px 0 0 0; font-size: 14px;">{alert.description}</p>
                    {f'<p style="margin: 5px 0 0 0; font-size: 13px; color: #666;"><strong>Action:</strong> {alert.recommended_action}</p>' if alert.recommended_action else ''}
                </div>
                """

        # Build key takeaways HTML
        takeaways_html = ""
        if analysis.key_takeaways:
            takeaways_html = "<ul style='margin: 0; padding-left: 20px;'>"
            for t in analysis.key_takeaways:
                takeaways_html += f"<li style='margin-bottom: 8px;'>{t}</li>"
            takeaways_html += "</ul>"

        # Build opportunities HTML
        opportunities_html = ""
        if analysis.opportunities:
            opportunities_html = "<ul style='margin: 0; padding-left: 20px;'>"
            for o in analysis.opportunities:
                opportunities_html += f"<li style='margin-bottom: 8px; color: #00d26a;'>{o}</li>"
            opportunities_html += "</ul>"

        # Build risks HTML
        risks_html = ""
        if analysis.correlated_risks:
            risks_html = "<ul style='margin: 0; padding-left: 20px;'>"
            for r in analysis.correlated_risks:
                risks_html += f"<li style='margin-bottom: 8px; color: #ff6b6b;'>{r}</li>"
            risks_html += "</ul>"

        html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Portfolio News Update</title>
</head>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; line-height: 1.6; color: #333; max-width: 700px; margin: 0 auto; padding: 20px; background: #f5f5f5;">
    <div style="background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
        <!-- Header -->
        <div style="background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); color: white; padding: 30px; text-align: center;">
            <h1 style="margin: 0 0 10px 0; font-size: 24px;">Portfolio News Update</h1>
            <p style="margin: 0; opacity: 0.8; font-size: 14px;">{datetime.now().strftime('%B %d, %Y • %I:%M %p')}</p>
        </div>

        <!-- Portfolio Summary -->
        <div style="padding: 25px; background: #fafafa; border-bottom: 1px solid #eee;">
            <table style="width: 100%; border-collapse: collapse;">
                <tr>
                    <td style="padding: 10px 0;">
                        <div style="font-size: 13px; color: #666; text-transform: uppercase;">Portfolio Value</div>
                        <div style="font-size: 28px; font-weight: bold; color: #1a1a2e;">{total_value}</div>
                    </td>
                    <td style="padding: 10px 0; text-align: right;">
                        <div style="font-size: 13px; color: #666; text-transform: uppercase;">Total Gain/Loss</div>
                        <div style="font-size: 20px; font-weight: bold; color: {gain_color};">
                            {gain_sign}${abs(gain_loss):,.2f} ({gain_sign}{gain_loss_pct:.1f}%)
                        </div>
                    </td>
                </tr>
            </table>
        </div>

        <!-- Overall Sentiment -->
        <div style="padding: 25px; text-align: center; border-bottom: 1px solid #eee;">
            <div style="font-size: 13px; color: #666; text-transform: uppercase; margin-bottom: 10px;">News Sentiment</div>
            <div style="font-size: 32px; color: {s_color}; font-weight: bold;">{s_icon}</div>
            <div style="font-size: 18px; color: {s_color}; font-weight: bold; margin-top: 5px;">{s_text}</div>
            <div style="font-size: 13px; color: #888; margin-top: 5px;">{analysis.sentiment_breakdown}</div>
        </div>

        <!-- Executive Summary -->
        <div style="padding: 25px; border-bottom: 1px solid #eee;">
            <h2 style="margin: 0 0 15px 0; font-size: 18px; color: #1a1a2e;">Executive Summary</h2>
            <p style="margin: 0; color: #444;">{analysis.summary}</p>
        </div>

        <!-- Alerts -->
        {f'''
        <div style="padding: 25px; border-bottom: 1px solid #eee;">
            <h2 style="margin: 0 0 15px 0; font-size: 18px; color: #1a1a2e;">⚠️ Alerts</h2>
            {alerts_html}
        </div>
        ''' if alerts_html else ''}

        <!-- Stock News -->
        <div style="padding: 25px; border-bottom: 1px solid #eee;">
            <h2 style="margin: 0 0 15px 0; font-size: 18px; color: #1a1a2e;">Holdings News</h2>
            {stock_summaries_html}
        </div>

        <!-- Key Takeaways -->
        {f'''
        <div style="padding: 25px; border-bottom: 1px solid #eee;">
            <h2 style="margin: 0 0 15px 0; font-size: 18px; color: #1a1a2e;">Key Takeaways</h2>
            {takeaways_html}
        </div>
        ''' if takeaways_html else ''}

        <!-- Opportunities -->
        {f'''
        <div style="padding: 25px; border-bottom: 1px solid #eee;">
            <h2 style="margin: 0 0 15px 0; font-size: 18px; color: #00d26a;">Opportunities</h2>
            {opportunities_html}
        </div>
        ''' if opportunities_html else ''}

        <!-- Risks -->
        {f'''
        <div style="padding: 25px; border-bottom: 1px solid #eee;">
            <h2 style="margin: 0 0 15px 0; font-size: 18px; color: #ff6b6b;">Correlated Risks</h2>
            {risks_html}
        </div>
        ''' if risks_html else ''}

        <!-- Portfolio Health -->
        {f'''
        <div style="padding: 25px; border-bottom: 1px solid #eee;">
            <h2 style="margin: 0 0 15px 0; font-size: 18px; color: #1a1a2e;">Portfolio News Health</h2>
            <p style="margin: 0; color: #444;">{analysis.portfolio_news_health}</p>
        </div>
        ''' if analysis.portfolio_news_health else ''}

        <!-- Footer -->
        <div style="padding: 20px; background: #f8f9fa; text-align: center; font-size: 12px; color: #888;">
            <p style="margin: 0 0 10px 0;">{analysis.disclaimer}</p>
            <p style="margin: 0;">
                Generated by Portfolio Manager • {analysis.stocks_analyzed} holdings • {analysis.total_articles_analyzed} articles analyzed
            </p>
        </div>
    </div>
</body>
</html>
        """

        return html
