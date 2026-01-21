"""User input handling with Rich prompts."""

from datetime import date, datetime
from typing import TYPE_CHECKING, Dict, List, Optional, Tuple

from rich.prompt import Confirm, Prompt
from rich.console import Console
from rich.table import Table

from app.models.portfolio import Position
from app.utils.validators import validate_stock_symbol

if TYPE_CHECKING:
    from app.services.stock_service import StockService


# Available Claude models with descriptions
CLAUDE_MODELS: Dict[str, Tuple[str, str]] = {
    "1": ("claude-opus-4-5-20251101", "Opus 4.5 - Most capable, best for complex analysis"),
    "2": ("claude-opus-4-20250514", "Opus 4 - Highly capable, excellent reasoning"),
    "3": ("claude-sonnet-4-20250514", "Sonnet 4 - Balanced performance and speed"),
    "4": ("claude-haiku-3-5-20241022", "Haiku 3.5 - Fastest, most cost-effective"),
}

# Model name shortcuts for CLI
MODEL_SHORTCUTS: Dict[str, str] = {
    "opus": "claude-opus-4-5-20251101",
    "opus-4.5": "claude-opus-4-5-20251101",
    "opus-4": "claude-opus-4-20250514",
    "sonnet": "claude-sonnet-4-20250514",
    "sonnet-4": "claude-sonnet-4-20250514",
    "haiku": "claude-haiku-3-5-20241022",
    "haiku-3.5": "claude-haiku-3-5-20241022",
}


class StockPrompts:
    """Handle user input with Rich prompts."""

    @staticmethod
    def get_model_selection() -> str:
        """
        Prompt for Claude model selection.

        Returns:
            Selected model ID string
        """
        console = Console()

        console.print("\n[bold cyan]Select Claude Model[/bold cyan]")

        table = Table(show_header=True, header_style="bold", box=None)
        table.add_column("#", style="cyan", width=3)
        table.add_column("Model", style="bold")
        table.add_column("Description")

        for key, (model_id, description) in CLAUDE_MODELS.items():
            model_name = model_id.replace("claude-", "").replace("-", " ").title()
            table.add_row(key, model_name, description)

        console.print(table)

        choice = Prompt.ask(
            "\n[cyan]Choose model[/cyan]",
            choices=list(CLAUDE_MODELS.keys()),
            default="3",  # Default to Sonnet
        )

        model_id, description = CLAUDE_MODELS[choice]
        model_name = model_id.replace("claude-", "").replace("-", " ").title()
        console.print(f"[green]Selected: {model_name}[/green]\n")

        return model_id

    @staticmethod
    def get_stock_symbol() -> str:
        """
        Prompt for stock symbol (basic validation only).

        Returns:
            Validated uppercase stock symbol
        """
        while True:
            symbol = Prompt.ask("[cyan]Enter stock symbol[/cyan]").upper().strip()
            if validate_stock_symbol(symbol):
                return symbol
            print("[red]Invalid symbol format. Use 1-5 letters (e.g., AAPL, MSFT)[/red]")

    @staticmethod
    def get_stock_symbol_with_search(stock_service: "StockService") -> Optional[str]:
        """
        Prompt for stock symbol with fuzzy search support.

        Allows user to enter a ticker symbol or company name.
        Shows matching results and lets user select.

        Args:
            stock_service: StockService instance for searching

        Returns:
            Selected stock symbol or None if cancelled
        """
        console = Console()

        while True:
            query = Prompt.ask(
                "[cyan]Enter stock symbol or company name[/cyan]"
            ).strip()

            if not query:
                continue

            # Check if it looks like a valid ticker (1-5 uppercase letters)
            upper_query = query.upper()
            if validate_stock_symbol(upper_query):
                # Try exact match first
                try:
                    results = stock_service.search_stocks(upper_query, limit=1)
                    if results and results[0].symbol.upper() == upper_query:
                        return upper_query
                except Exception:
                    pass

            # Search for matches
            try:
                results = stock_service.search_stocks(query, limit=8)
            except Exception as e:
                console.print(f"[red]Search failed: {e}[/red]")
                continue

            if not results:
                console.print(f"[yellow]No matches found for '{query}'[/yellow]")
                if Confirm.ask("[cyan]Try again?[/cyan]", default=True):
                    continue
                return None

            # If only one result, confirm and use it
            if len(results) == 1:
                result = results[0]
                console.print(
                    f"[green]Found:[/green] {result.symbol} - {result.name}"
                )
                if Confirm.ask("[cyan]Use this stock?[/cyan]", default=True):
                    return result.symbol
                continue

            # Show results table for selection
            console.print(f"\n[bold]Found {len(results)} matches:[/bold]")

            table = Table(show_header=True, header_style="bold", box=None)
            table.add_column("#", style="cyan", width=3)
            table.add_column("Symbol", style="bold yellow")
            table.add_column("Name")
            table.add_column("Exchange", style="dim")

            for i, result in enumerate(results, 1):
                table.add_row(
                    str(i),
                    result.symbol,
                    result.name[:40] + "..." if len(result.name) > 40 else result.name,
                    result.exchange or "",
                )

            console.print(table)

            # Get selection
            choices = [str(i) for i in range(1, len(results) + 1)] + ["0"]
            selection = Prompt.ask(
                "\n[cyan]Select number (0 to search again)[/cyan]",
                choices=choices,
                default="1",
            )

            if selection == "0":
                continue

            selected = results[int(selection) - 1]
            return selected.symbol

    @staticmethod
    def confirm_ai_analysis() -> bool:
        """
        Confirm if user wants AI analysis.

        Returns:
            True if user wants AI analysis
        """
        return Confirm.ask(
            "[cyan]Would you like AI-powered insights?[/cyan]", default=True
        )

    @staticmethod
    def get_command() -> str:
        """
        Get user command.

        Returns:
            User command string
        """
        return Prompt.ask(
            "\n[bold cyan]Command[/bold cyan]",
            choices=["stock", "news", "news-analysis", "portfolio", "add", "remove", "analyze-portfolio", "portfolio-news", "history", "performance", "help", "quit"],
            default="portfolio",
        )

    @staticmethod
    def press_enter_to_continue():
        """Wait for user to press Enter."""
        Prompt.ask("[muted]Press Enter to continue[/muted]", default="")

    # ============ Portfolio Prompts ============

    @staticmethod
    def get_shares() -> float:
        """Prompt for number of shares."""
        while True:
            try:
                shares_str = Prompt.ask("[cyan]Number of shares[/cyan]")
                shares = float(shares_str)
                if shares <= 0:
                    print("[red]Shares must be positive[/red]")
                    continue
                return shares
            except ValueError:
                print("[red]Please enter a valid number[/red]")

    @staticmethod
    def get_purchase_price() -> float:
        """Prompt for purchase price per share."""
        while True:
            try:
                price_str = Prompt.ask("[cyan]Purchase price per share[/cyan]")
                price = float(price_str)
                if price <= 0:
                    print("[red]Price must be positive[/red]")
                    continue
                return price
            except ValueError:
                print("[red]Please enter a valid price[/red]")

    @staticmethod
    def get_purchase_date() -> date:
        """Prompt for purchase date."""
        while True:
            date_str = Prompt.ask(
                "[cyan]Purchase date (YYYY-MM-DD)[/cyan]",
                default=date.today().isoformat(),
            )
            try:
                parsed = datetime.strptime(date_str, "%Y-%m-%d").date()
                if parsed > date.today():
                    print("[red]Purchase date cannot be in the future[/red]")
                    continue
                return parsed
            except ValueError:
                print("[red]Please enter date in YYYY-MM-DD format[/red]")

    @staticmethod
    def get_notes() -> Optional[str]:
        """Prompt for optional notes."""
        notes = Prompt.ask("[cyan]Notes (optional)[/cyan]", default="")
        return notes if notes.strip() else None

    @staticmethod
    def get_position_id_to_remove(positions: List[Position]) -> int:
        """Prompt for position ID to remove."""
        valid_ids = [str(p.id) for p in positions if p.id is not None]
        return int(
            Prompt.ask(
                "[cyan]Enter position ID to remove[/cyan]",
                choices=valid_ids,
            )
        )

    @staticmethod
    def confirm_removal() -> bool:
        """Confirm position removal."""
        return Confirm.ask(
            "[yellow]Are you sure you want to remove this position?[/yellow]",
            default=False,
        )
