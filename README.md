# Terminal Portfolio Manager

A command-line tool for tracking your stock portfolio and getting AI-powered insights. It pulls real-time data from Yahoo Finance and uses Claude AI to help you understand what's happening with your investments.

## What it does

- **Track your portfolio** - Add positions, see current values, gains/losses, and sector allocation
- **Analyze any stock** - Look up fundamentals, valuation metrics, and get AI-generated insights
- **Stay on top of news** - Get news for any stock with AI sentiment analysis for each article

## Quick Start

```bash
# Install
pip install -e .

# Set up your API key (create a .env file)
echo "ANTHROPIC_API_KEY=your_key_here" > .env

# Run it
portfolio
```

You'll be prompted to pick a Claude model, then dropped into an interactive shell where you can run commands.

## Security Best Practices

**IMPORTANT**: Never commit sensitive credentials to version control!

1. **Use `.env` for secrets** - Copy `.env.example` to `.env` and add your real credentials there
2. **Never commit `.env`** - It's already in `.gitignore`, but double-check before pushing
3. **Use App Passwords** - For Gmail, create an App Password instead of using your account password
4. **Rotate compromised credentials** - If you accidentally commit credentials, immediately:
   - Revoke/rotate the exposed credentials
   - Remove them from git history (see [GitHub's guide](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/removing-sensitive-data-from-a-repository))
   - Force push the cleaned history

## Commands

Once you're in the interactive mode, here's what you can do:

| Command | What it does |
|---------|--------------|
| `stock` | Look up any stock - shows fundamentals and optional AI analysis |
| `news` | Get recent news for a stock with sentiment analysis |
| `news-analysis` | Deep dive into news themes and their potential impact |
| `portfolio` | See your current holdings with live prices |
| `add` | Add a new position (supports fuzzy search - type "apple" to find AAPL) |
| `remove` | Remove a position |
| `analyze-portfolio` | Get AI insights on your overall portfolio |
| `history` | See how your portfolio value has changed over time |
| `performance` | See which stocks are helping or hurting your returns |
| `help` | Show available commands |
| `quit` | Exit |

## One-off Analysis

Don't want interactive mode? Just pass a ticker:

```bash
# Quick analysis of Apple
portfolio AAPL

# Without AI (just the numbers)
portfolio MSFT --no-ai

# Use a specific model
portfolio NVDA --model opus
```

## Configuration

Everything is configured through environment variables stored in a `.env` file.

**Setup steps:**

1. Copy the example file:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` with your actual values (never commit this file!):
   ```bash
   # Required for AI features
   ANTHROPIC_API_KEY=sk-ant-your-actual-key-here

   # Optional - defaults shown
   CLAUDE_MODEL=claude-sonnet-4-20250514
   PORTFOLIO_DB_PATH=data/portfolio.db
   ```

See `.env.example` for all available configuration options with documentation.

## How it works

**Data sources:**
- Stock prices and fundamentals come from Yahoo Finance (via yfinance)
- AI analysis is powered by Claude (Anthropic's API)

**Portfolio storage:**
- Your positions are stored in a local SQLite database
- Historical snapshots are saved when you view your portfolio

**The AI stuff:**
- When you ask for analysis, the app sends the stock data to Claude
- Claude looks at the fundamentals, news, and context to give you insights
- It's genuinely useful for understanding what's going on, but obviously don't make investment decisions based solely on AI output

## Requirements

- Python 3.10+
- An Anthropic API key (for AI features)
- Internet connection (for stock data)

## Project Structure

```
app/
├── agent/          # Main interactive agent
├── services/       # Stock data, AI, portfolio
├── models/         # Data models (Pydantic)
├── ui/             # Display formatting and prompts
└── utils/          # Helpers and exceptions
```

## License

MIT
