# Terminal Portfolio Manager

A command-line tool for tracking your stock portfolio and getting AI-powered insights. It pulls real-time data from Yahoo Finance and uses Claude AI to help you understand what's happening with your investments.

## What it does

- **Track your portfolio** - Add positions, see current values, gains/losses, and sector allocation
- **Analyze any stock** - Look up fundamentals, valuation metrics, and get AI-generated insights
- **Stay on top of news** - Get news for any stock with AI sentiment analysis for each article
- **Daily newsletters** - Automatically email yourself a summary of news affecting your holdings

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
| `portfolio-news` | AI analysis of news across all your holdings |
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

## The Newsletter Feature

This is pretty cool - you can set it up to email you a portfolio news digest twice a day. It analyzes news for all your holdings and sends you a nicely formatted email with:

- Overall sentiment (bullish/bearish/neutral)
- News summary for each stock you own
- Alerts if something needs attention
- Key takeaways

### Setting it up

Add these to your `.env` file:

```bash
# For Gmail (you'll need an App Password - regular password won't work)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=you@gmail.com
SMTP_PASSWORD=your_app_password
NEWSLETTER_SENDER_EMAIL=you@gmail.com
NEWSLETTER_RECIPIENTS=you@gmail.com

# When to send (24-hour format)
NEWSLETTER_SCHEDULE_MORNING=08:00
NEWSLETTER_SCHEDULE_EVENING=17:30
```

To get a Gmail App Password: enable 2FA on your Google account, then go to https://myaccount.google.com/apppasswords

### Running it

```bash
# Test your email config
portfolio-newsletter --test

# Send one right now
portfolio-newsletter

# Run as a daemon (sends at scheduled times)
portfolio-newsletter --daemon
```

## Configuration

Everything is configured through environment variables. Create a `.env` file in the project root:

```bash
# Required for AI features
ANTHROPIC_API_KEY=sk-ant-...

# Optional - defaults shown
CLAUDE_MODEL=claude-sonnet-4-20250514
PORTFOLIO_DB_PATH=data/portfolio.db

# For newsletter (all optional)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=
SMTP_PASSWORD=
NEWSLETTER_SENDER_EMAIL=
NEWSLETTER_RECIPIENTS=
NEWSLETTER_SCHEDULE_MORNING=08:00
NEWSLETTER_SCHEDULE_EVENING=17:30
```

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
├── services/       # Stock data, AI, portfolio, email, newsletter
├── models/         # Data models (Pydantic)
├── ui/             # Display formatting and prompts
├── newsletter/     # Newsletter CLI and scheduler
└── utils/          # Helpers and exceptions
```

## License

MIT
