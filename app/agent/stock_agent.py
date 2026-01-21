"""Main stock analysis agent orchestrator."""

from typing import Optional

from rich.progress import Progress, SpinnerColumn, TextColumn

from app.config import Settings, get_settings
from app.services.ai_service import AIService
from app.services.portfolio_service import PortfolioService
from app.services.rate_limiter import RateLimiter
from app.services.stock_service import StockService
from app.ui.console import StockConsole
from app.ui.display import StockDisplay
from app.ui.prompts import StockPrompts
from app.utils.exceptions import (
    AIServiceError,
    DataFetchError,
    StockAgentError,
    StockNotFoundError,
)


class StockAgent:
    """Main agent coordinating stock analysis workflow."""

    def __init__(self, settings: Optional[Settings] = None, model: Optional[str] = None):
        """
        Initialize the stock agent.

        Args:
            settings: Application settings (uses defaults if not provided)
            model: Claude model ID to use (overrides settings if provided)
        """
        self.settings = settings or get_settings()

        # Override model if provided
        if model:
            self.settings.claude_model = model

        self.console = StockConsole()
        self.display = StockDisplay(self.console)
        self.prompts = StockPrompts()

        # Track last analyzed symbol for quick re-use
        self.last_symbol: Optional[str] = None

        # Initialize rate limiters
        self.yfinance_limiter = RateLimiter(self.settings.yfinance_requests_per_minute)
        self.claude_limiter = RateLimiter(self.settings.claude_requests_per_minute)

        # Initialize services
        self.stock_service = StockService(self.yfinance_limiter)

        # Initialize portfolio service
        self.portfolio_service = PortfolioService(
            db_path=self.settings.portfolio_db_path,
            stock_service=self.stock_service,
        )

        # Only initialize AI service if API key is available
        self.ai_service: Optional[AIService] = None
        if self.settings.anthropic_api_key:
            self.ai_service = AIService(self.settings, self.claude_limiter)

    def run(self):
        """Main agent loop."""
        self.display.display_welcome()

        while True:
            try:
                command = self.prompts.get_command()

                if command == "quit":
                    self.display.display_goodbye()
                    break
                elif command == "help":
                    self.display.display_help()
                elif command == "stock":
                    self._analyze_stock()
                elif command == "news":
                    self._get_news()
                elif command == "news-analysis":
                    self._analyze_news()
                elif command == "portfolio":
                    self._view_portfolio()
                elif command == "add":
                    self._add_position()
                elif command == "remove":
                    self._remove_position()
                elif command == "analyze-portfolio":
                    self._analyze_portfolio()
                elif command == "portfolio-news":
                    self._analyze_portfolio_news()
                elif command == "history":
                    self._view_history()
                elif command == "performance":
                    self._view_performance()

            except KeyboardInterrupt:
                self.console.print("")
                self.display.display_goodbye()
                break
            except StockAgentError as e:
                self.console.print_error(str(e))
            except Exception as e:
                self.console.print_error(f"Unexpected error: {e}")

    def _analyze_stock(self):
        """Analyze a single stock."""
        # Offer to reuse last symbol if available
        if self.last_symbol:
            if self.prompts.confirm_reuse_symbol(self.last_symbol):
                symbol = self.last_symbol
            else:
                symbol = self.prompts.get_stock_symbol_with_search(self.stock_service)
                if not symbol:
                    return
        else:
            symbol = self.prompts.get_stock_symbol_with_search(self.stock_service)
            if not symbol:
                return

        # Save as last symbol for future commands
        self.last_symbol = symbol

        # Fetch stock data with progress spinner
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console.console,
            transient=True,
        ) as progress:
            task = progress.add_task(f"Fetching data for {symbol}...", total=None)

            try:
                analysis = self.stock_service.get_stock_analysis(symbol)
                progress.update(task, description=f"[green]Data fetched for {symbol}[/green]")
            except StockNotFoundError:
                self.console.print_error(f"Stock symbol '{symbol}' not found")
                return
            except DataFetchError as e:
                self.console.print_error(f"Failed to fetch data: {e}")
                return

        # Display fundamental data
        self.display.display_stock_info(analysis)
        self.display.display_fundamentals(analysis)

        # Offer AI analysis if available
        if self.ai_service is None:
            self.console.print_muted(
                "\nAI insights not available. Set ANTHROPIC_API_KEY in .env to enable."
            )
            return

        if self.prompts.confirm_ai_analysis():
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=self.console.console,
                transient=True,
            ) as progress:
                task = progress.add_task("Generating AI insights...", total=None)

                try:
                    insight = self.ai_service.analyze_stock(analysis)
                    progress.update(task, description="[green]Analysis complete[/green]")
                except AIServiceError as e:
                    self.console.print_error(f"AI analysis failed: {e}")
                    self.console.print_info("Showing fundamental data only.")
                    return

            self.display.display_ai_insight(insight)

    def _get_news(self):
        """Get news for a stock with AI sentiment analysis."""
        # Offer to reuse last symbol if available
        if self.last_symbol:
            if self.prompts.confirm_reuse_symbol(self.last_symbol):
                symbol = self.last_symbol
            else:
                symbol = self.prompts.get_stock_symbol_with_search(self.stock_service)
                if not symbol:
                    return
        else:
            symbol = self.prompts.get_stock_symbol_with_search(self.stock_service)
            if not symbol:
                return

        # Save as last symbol for future commands
        self.last_symbol = symbol

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console.console,
            transient=True,
        ) as progress:
            task = progress.add_task(f"Fetching news for {symbol}...", total=None)

            try:
                articles = self.stock_service.get_news(symbol)
                progress.update(task, description=f"[green]News fetched for {symbol}[/green]")
            except DataFetchError as e:
                self.console.print_error(f"Failed to fetch news: {e}")
                return

        if not articles:
            self.console.print_info(f"No news articles found for {symbol}")
            return

        # Get AI sentiment analysis if available
        sentiments = None
        if self.ai_service:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=self.console.console,
                transient=True,
            ) as progress:
                task = progress.add_task("Analyzing sentiment...", total=None)
                try:
                    sentiments = self.ai_service.analyze_article_sentiments(symbol, articles)
                    progress.update(task, description="[green]Sentiment analysis complete[/green]")
                except AIServiceError:
                    # Silently continue without sentiment if AI fails
                    pass

        self.display.display_news(symbol, articles, sentiments)

    def _analyze_news(self):
        """Analyze news for a stock using AI."""
        if self.ai_service is None:
            self.console.print_warning(
                "AI news analysis not available. Set ANTHROPIC_API_KEY in .env to enable."
            )
            return

        # Offer to reuse last symbol if available
        if self.last_symbol:
            if self.prompts.confirm_reuse_symbol(self.last_symbol):
                symbol = self.last_symbol
            else:
                symbol = self.prompts.get_stock_symbol_with_search(self.stock_service)
                if not symbol:
                    return
        else:
            symbol = self.prompts.get_stock_symbol_with_search(self.stock_service)
            if not symbol:
                return

        # Save as last symbol for future commands
        self.last_symbol = symbol

        # Fetch news
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console.console,
            transient=True,
        ) as progress:
            task = progress.add_task(f"Fetching news for {symbol}...", total=None)

            try:
                articles = self.stock_service.get_news(symbol, limit=10)
                progress.update(task, description=f"[green]Fetched {len(articles)} articles[/green]")
            except DataFetchError as e:
                self.console.print_error(f"Failed to fetch news: {e}")
                return

        if not articles:
            self.console.print_info(f"No news articles found for {symbol}")
            return

        # Analyze with AI
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console.console,
            transient=True,
        ) as progress:
            task = progress.add_task("Analyzing news with AI...", total=None)

            try:
                analysis = self.ai_service.analyze_news(symbol, articles)
                progress.update(task, description="[green]Analysis complete[/green]")
            except AIServiceError as e:
                self.console.print_error(f"AI analysis failed: {e}")
                return

        self.display.display_news_analysis(analysis)

    # ============ Portfolio Commands ============

    def _view_portfolio(self):
        """Display current portfolio."""
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console.console,
            transient=True,
        ) as progress:
            task = progress.add_task("Loading portfolio...", total=None)
            portfolio = self.portfolio_service.get_portfolio(include_prices=True)
            progress.update(task, description="[green]Portfolio loaded[/green]")

        if portfolio.num_positions == 0:
            self.console.print_info(
                "Your portfolio is empty. Use 'add' to add positions."
            )
            return

        # Save a snapshot for history tracking
        self.portfolio_service.save_snapshot(portfolio)

        self.display.display_portfolio(portfolio)

    def _add_position(self):
        """Add a new position to the portfolio."""
        # Get position details via prompts with fuzzy search
        symbol = self.prompts.get_stock_symbol_with_search(self.stock_service)
        if not symbol:
            return

        # Validate symbol exists
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console.console,
            transient=True,
        ) as progress:
            task = progress.add_task(f"Validating {symbol}...", total=None)
            try:
                self.stock_service.get_stock_analysis(symbol)
                progress.update(task, description=f"[green]{symbol} validated[/green]")
            except StockNotFoundError:
                self.console.print_error(f"Symbol '{symbol}' not found")
                return
            except DataFetchError as e:
                self.console.print_error(f"Failed to validate symbol: {e}")
                return

        shares = self.prompts.get_shares()
        purchase_price = self.prompts.get_purchase_price()
        purchase_date = self.prompts.get_purchase_date()
        notes = self.prompts.get_notes()

        # Add position
        position = self.portfolio_service.add_position(
            symbol=symbol,
            shares=shares,
            purchase_price=purchase_price,
            purchase_date=purchase_date,
            notes=notes,
        )

        self.console.print_success(
            f"Added {shares} shares of {symbol} @ ${purchase_price:.2f} on {purchase_date}"
        )

    def _remove_position(self):
        """Remove a position from the portfolio."""
        # Get positions
        portfolio = self.portfolio_service.get_portfolio(include_prices=False)

        if portfolio.num_positions == 0:
            self.console.print_info("Your portfolio is empty.")
            return

        # Display positions for selection
        self.display.display_positions_for_removal(portfolio.positions)

        # Get position ID to remove
        position_id = self.prompts.get_position_id_to_remove(portfolio.positions)

        # Confirm and remove
        if self.prompts.confirm_removal():
            if self.portfolio_service.remove_position(position_id):
                self.console.print_success("Position removed.")
            else:
                self.console.print_error("Failed to remove position.")
        else:
            self.console.print_info("Removal cancelled.")

    def _analyze_portfolio(self):
        """Run AI analysis on the portfolio."""
        if self.ai_service is None:
            self.console.print_warning(
                "AI insights not available. Set ANTHROPIC_API_KEY in .env to enable."
            )
            return

        # Load portfolio
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console.console,
            transient=True,
        ) as progress:
            task = progress.add_task("Loading portfolio...", total=None)
            portfolio = self.portfolio_service.get_portfolio(include_prices=True)
            progress.update(task, description="[green]Portfolio loaded[/green]")

        if portfolio.num_positions == 0:
            self.console.print_info(
                "Your portfolio is empty. Add positions first with 'add'."
            )
            return

        # Display basic portfolio summary
        self.display.display_portfolio_summary(portfolio)

        # Run AI analysis
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console.console,
            transient=True,
        ) as progress:
            task = progress.add_task("Analyzing portfolio with AI...", total=None)
            try:
                analysis = self.ai_service.analyze_portfolio(portfolio)
                progress.update(task, description="[green]Analysis complete[/green]")
            except AIServiceError as e:
                self.console.print_error(f"AI analysis failed: {e}")
                return

        # Display AI insights
        self.display.display_portfolio_analysis(analysis)

    def _analyze_portfolio_news(self):
        """Analyze news for all stocks in the portfolio."""
        if self.ai_service is None:
            self.console.print_warning(
                "AI news analysis not available. Set ANTHROPIC_API_KEY in .env to enable."
            )
            return

        # Load portfolio
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console.console,
            transient=True,
        ) as progress:
            task = progress.add_task("Loading portfolio...", total=None)
            portfolio = self.portfolio_service.get_portfolio(include_prices=True)
            progress.update(task, description="[green]Portfolio loaded[/green]")

        if portfolio.num_positions == 0:
            self.console.print_info(
                "Your portfolio is empty. Add positions first with 'add'."
            )
            return

        # Get unique symbols from portfolio
        symbols = list({agg.symbol for agg in portfolio.aggregated})

        # Fetch news for each symbol
        news_by_symbol = {}
        sector_by_symbol = {}
        weight_by_symbol = {}

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console.console,
            transient=True,
        ) as progress:
            task = progress.add_task(f"Fetching news for {len(symbols)} holdings...", total=None)

            for agg in portfolio.aggregated:
                try:
                    articles = self.stock_service.get_news(agg.symbol, limit=10)
                    if articles:
                        news_by_symbol[agg.symbol] = articles
                        sector_by_symbol[agg.symbol] = agg.sector or "Unknown"
                        weight_by_symbol[agg.symbol] = agg.weight_pct or 0
                except DataFetchError:
                    # Skip symbols where news fetch fails
                    pass

            progress.update(task, description=f"[green]Fetched news for {len(news_by_symbol)} holdings[/green]")

        if not news_by_symbol:
            self.console.print_info("No news found for any portfolio holdings.")
            return

        # Analyze with AI
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console.console,
            transient=True,
        ) as progress:
            task = progress.add_task("Analyzing portfolio news with AI...", total=None)

            try:
                analysis = self.ai_service.analyze_portfolio_news(
                    news_by_symbol, sector_by_symbol, weight_by_symbol
                )
                progress.update(task, description="[green]Analysis complete[/green]")
            except AIServiceError as e:
                self.console.print_error(f"AI analysis failed: {e}")
                return

        self.display.display_portfolio_news_analysis(analysis)

    def _view_history(self):
        """Display portfolio value history."""
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console.console,
            transient=True,
        ) as progress:
            task = progress.add_task("Loading history...", total=None)
            history = self.portfolio_service.get_history(days=90)
            progress.update(task, description="[green]History loaded[/green]")

        self.display.display_history(history)

    def _view_performance(self):
        """Display portfolio performance breakdown."""
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console.console,
            transient=True,
        ) as progress:
            task = progress.add_task("Loading portfolio...", total=None)
            portfolio = self.portfolio_service.get_portfolio(include_prices=True)
            progress.update(task, description="[green]Portfolio loaded[/green]")

        if portfolio.num_positions == 0:
            self.console.print_info(
                "Your portfolio is empty. Add positions first with 'add'."
            )
            return

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console.console,
            transient=True,
        ) as progress:
            task = progress.add_task("Calculating performance...", total=None)
            performance = self.portfolio_service.get_performance(portfolio)
            progress.update(task, description="[green]Performance calculated[/green]")

        self.display.display_performance(performance)

    def analyze_single(self, symbol: str, with_ai: bool = True) -> None:
        """
        Analyze a single stock non-interactively.

        Args:
            symbol: Stock ticker symbol
            with_ai: Whether to include AI analysis
        """
        # Fetch stock data with progress spinner
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console.console,
            transient=True,
        ) as progress:
            task = progress.add_task(f"Fetching data for {symbol}...", total=None)
            analysis = self.stock_service.get_stock_analysis(symbol)
            progress.update(task, description=f"[green]Data fetched for {symbol}[/green]")

        # Display fundamental data
        self.display.display_stock_info(analysis)
        self.display.display_fundamentals(analysis)

        # AI analysis if requested and available
        if with_ai:
            if self.ai_service is None:
                self.console.print_warning(
                    "AI insights not available. Set ANTHROPIC_API_KEY in .env to enable."
                )
                return

            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=self.console.console,
                transient=True,
            ) as progress:
                task = progress.add_task("Generating AI insights...", total=None)
                insight = self.ai_service.analyze_stock(analysis)
                progress.update(task, description="[green]Analysis complete[/green]")

            self.display.display_ai_insight(insight)
