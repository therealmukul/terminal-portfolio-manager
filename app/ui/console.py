"""Rich console wrapper with custom theming."""

from rich.console import Console
from rich.theme import Theme


def create_stock_theme() -> Theme:
    """Create a custom theme for stock analysis display."""
    return Theme(
        {
            "positive": "bold green",
            "negative": "bold red",
            "neutral": "yellow",
            "info": "cyan",
            "header": "bold magenta",
            "subheader": "bold blue",
            "metric_name": "blue",
            "metric_value": "bold white",
            "warning": "bold yellow",
            "error": "bold red",
            "success": "bold green",
            "muted": "dim white",
            "highlight": "bold cyan",
        }
    )


class StockConsole:
    """Wrapper for Rich console with stock-specific theming."""

    def __init__(self):
        """Initialize the stock console with custom theme."""
        self.console = Console(theme=create_stock_theme())

    def print(self, *args, **kwargs):
        """Print to console."""
        self.console.print(*args, **kwargs)

    def print_header(self, text: str):
        """Print a styled header."""
        self.console.print(f"\n[header]{text}[/header]")

    def print_subheader(self, text: str):
        """Print a styled subheader."""
        self.console.print(f"\n[subheader]{text}[/subheader]")

    def print_positive(self, text: str):
        """Print positive value (green)."""
        self.console.print(f"[positive]{text}[/positive]")

    def print_negative(self, text: str):
        """Print negative value (red)."""
        self.console.print(f"[negative]{text}[/negative]")

    def print_info(self, text: str):
        """Print info text."""
        self.console.print(f"[info]{text}[/info]")

    def print_warning(self, text: str):
        """Print warning text."""
        self.console.print(f"[warning]Warning: {text}[/warning]")

    def print_error(self, text: str):
        """Print error text."""
        self.console.print(f"[error]Error: {text}[/error]")

    def print_success(self, text: str):
        """Print success text."""
        self.console.print(f"[success]{text}[/success]")

    def print_muted(self, text: str):
        """Print muted/dim text."""
        self.console.print(f"[muted]{text}[/muted]")

    def clear(self):
        """Clear the console."""
        self.console.clear()

    def rule(self, title: str = ""):
        """Print a horizontal rule."""
        self.console.rule(title)
