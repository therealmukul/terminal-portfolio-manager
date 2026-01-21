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

| Command | Aliases | What it does |
|---------|---------|--------------|
| **Stock Analysis** |||
| `stock` | - | Look up any stock - shows fundamentals and optional AI analysis |
| `news` | - | Get recent news for a stock with sentiment analysis |
| `analysis` | `news-analysis` | Deep dive into news themes and their potential impact |
| **Portfolio Management** |||
| `portfolio` | - | See your current holdings with live prices |
| `buy` | `add` | Add a new position (supports fuzzy search - type "apple" to find AAPL) |
| `sell` | `remove` | Remove a position |
| `analyze` | `analyze-portfolio`, `ap` | Get AI insights on your overall portfolio |
| `portfolio-news` | `pnews`, `pn` | AI analysis of news across all your holdings |
| `history` | - | See how your portfolio value has changed over time |
| `performance` | `perf` | See which stocks are helping or hurting your returns |
| **Utility** |||
| `help` | - | Show available commands |
| `quit` | `exit`, `q` | Exit the application |

### Pro Tips

- **Shorter aliases**: Use `ap` instead of `analyze-portfolio`, `pn` instead of `portfolio-news` to save typing
- **Context retention**: After analyzing a stock, you'll be asked if you want to analyze it again - no need to re-enter the symbol
- **Clearer names**: Use `buy`/`sell` instead of `add`/`remove` for portfolio operations (both work, but buy/sell are more intuitive)

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

**⚠️ Security Note**: Always use `.env` for credentials, never commit them to git!

1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` and add your real credentials:
   ```bash
   # For Gmail (you'll need an App Password - regular password won't work)
   SMTP_HOST=smtp.gmail.com
   SMTP_PORT=587
   SMTP_USERNAME=you@gmail.com
   SMTP_PASSWORD=your_app_password_here
   NEWSLETTER_SENDER_EMAIL=you@gmail.com
   NEWSLETTER_RECIPIENTS=you@gmail.com

   # When to send (24-hour format)
   NEWSLETTER_SCHEDULE_MORNING=08:00
   NEWSLETTER_SCHEDULE_EVENING=17:30
   ```

3. Get a Gmail App Password (more secure than your account password):
   - Enable 2FA on your Google account
   - Visit https://myaccount.google.com/apppasswords
   - Generate an app-specific password for this application

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

   # For newsletter features (all optional)
   SMTP_HOST=smtp.gmail.com
   SMTP_PORT=587
   SMTP_USERNAME=your-email@gmail.com
   SMTP_PASSWORD=your-app-password-here
   NEWSLETTER_SENDER_EMAIL=your-email@gmail.com
   NEWSLETTER_RECIPIENTS=recipient@example.com
   NEWSLETTER_SCHEDULE_MORNING=08:00
   NEWSLETTER_SCHEDULE_EVENING=17:30
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
├── services/       # Stock data, AI, portfolio, email, newsletter
├── models/         # Data models (Pydantic)
├── ui/             # Display formatting and prompts
├── newsletter/     # Newsletter CLI and scheduler
└── utils/          # Helpers and exceptions
```

## License

MIT
