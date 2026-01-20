"""User input handling with Rich prompts."""

from datetime import date, datetime
from typing import Dict, List, Optional, Tuple

from rich.prompt import Confirm, Prompt
from rich.console import Console
from rich.table import Table

from app.models.portfolio import Position
from app.utils.validators import validate_stock_symbol


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
        Prompt for stock symbol.

        Returns:
            Validated uppercase stock symbol
        """
        while True:
            symbol = Prompt.ask("[cyan]Enter stock symbol[/cyan]").upper().strip()
            if validate_stock_symbol(symbol):
                return symbol
            print("[red]Invalid symbol format. Use 1-5 letters (e.g., AAPL, MSFT)[/red]")

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
            choices=["analyze", "news", "news-analysis", "portfolio", "add", "remove", "analyze-portfolio", "portfolio-news", "history", "performance", "help", "quit"],
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
