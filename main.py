#!/usr/bin/env python3
"""Stock Analysis Agent - Entry point."""

import argparse
import sys

from dotenv import load_dotenv


def main():
    """Main entry point for the stock analysis agent."""
    # Load environment variables
    load_dotenv()

    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description="Terminal-based stock analysis agent powered by Yahoo Finance and Claude AI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py                    # Start interactive mode (prompts for model)
  python main.py --model sonnet     # Use Claude Sonnet
  python main.py --model opus AAPL  # Analyze Apple with Claude Opus
  python main.py MSFT --no-ai       # Analyze Microsoft without AI insights
  python main.py "Nvidia"           # Search by company name
  python main.py "Tesla Motors"     # Fuzzy search for company

Available models:
  opus, opus-4.5    - Claude Opus 4.5 (most capable)
  opus-4            - Claude Opus 4
  sonnet, sonnet-4  - Claude Sonnet 4 (balanced)
  haiku, haiku-3.5  - Claude Haiku 3.5 (fastest)
        """,
    )
    parser.add_argument(
        "symbol",
        nargs="?",
        help="Stock symbol or company name to analyze (e.g., AAPL, MSFT, 'Apple', 'Nvidia'). If not provided, starts interactive mode.",
    )
    parser.add_argument(
        "--no-ai",
        action="store_true",
        help="Skip AI-powered analysis (only show fundamental data)",
    )
    parser.add_argument(
        "--model", "-m",
        type=str,
        choices=["opus", "opus-4.5", "opus-4", "sonnet", "sonnet-4", "haiku", "haiku-3.5"],
        help="Claude model to use (default: prompts interactively)",
    )

    args = parser.parse_args()

    try:
        # Import here to catch configuration errors early
        from app.agent import StockAgent
        from app.ui.prompts import StockPrompts, MODEL_SHORTCUTS
        from app.utils.exceptions import StockAgentError

        # Determine model to use
        model = None
        if args.model:
            # CLI flag provided - use the shortcut mapping
            model = MODEL_SHORTCUTS.get(args.model)
        elif not args.no_ai:
            # No CLI flag and AI is enabled - prompt for selection
            model = StockPrompts.get_model_selection()

        # Create agent with selected model
        agent = StockAgent(model=model)

        if args.symbol:
            # Non-interactive mode: analyze single stock (supports ticker or company name)
            try:
                agent.analyze_single(args.symbol, with_ai=not args.no_ai)
            except StockAgentError as e:
                print(f"Error: {e}", file=sys.stderr)
                sys.exit(1)
        else:
            # Interactive mode
            agent.run()

    except KeyboardInterrupt:
        print("\nGoodbye!")
        sys.exit(0)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        print("\nMake sure you have set ANTHROPIC_API_KEY in your .env file.")
        sys.exit(1)


if __name__ == "__main__":
    main()
