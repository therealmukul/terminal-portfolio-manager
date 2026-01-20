# Terminal Portfolio Manager

A command-line stock analysis and portfolio management tool powered by Yahoo Finance for real-time market data and Claude AI for intelligent investment insights.

## Features

- **Real-Time Stock Analysis** - Fetch current prices, fundamentals, technical indicators, and analyst ratings via Yahoo Finance
- **AI-Powered Insights** - Claude generates detailed stock analysis with buy/sell/hold recommendations, SWOT-style breakdowns, and risk assessments
- **Portfolio Tracking** - Track multiple positions with tax lot details, unrealized gains, holding periods, and sector allocation
- **News Analysis** - Retrieve company news with AI-powered sentiment analysis and impact assessment
- **Tax Optimization** - Tax-loss harvesting recommendations, wash sale warnings, and long-term vs short-term gain tracking
- **Performance History** - View 90-day portfolio value trends and identify top gainers/losers

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/terminal-portfolio-manager.git
   cd terminal-portfolio-manager
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Configure environment variables:
   ```bash
   cp .env.example .env
   ```

4. Edit `.env` and add your Anthropic API key:
   ```
   ANTHROPIC_API_KEY=your_api_key_here
   ```

## Usage

### Interactive Mode

Launch the interactive menu-driven interface:

```bash
python main.py
```

Available commands:

| Command | Description |
|---------|-------------|
| `analyze` | Analyze stock fundamentals with optional AI insights |
| `news` | Get latest news articles for a stock |
| `news-analysis` | AI sentiment analysis of stock news |
| `portfolio` | View portfolio with live prices |
| `add` | Add a position to your portfolio |
| `remove` | Remove a position from your portfolio |
| `analyze-portfolio` | AI-powered portfolio health analysis |
| `portfolio-news` | Cross-portfolio news analysis |
| `history` | View 90-day portfolio value history |
| `performance` | See holding contributions to gains/losses |
| `help` | Display available commands |
| `quit` | Exit the application |

### Non-Interactive Mode

Analyze stocks directly from the command line:

```bash
# Analyze a stock with default AI model
python main.py AAPL

# Analyze without AI (fundamentals only)
python main.py MSFT --no-ai

# Specify a Claude model
python main.py TSLA --model opus-4.5
```

## Architecture

```
main.py (CLI Entry Point)
    │
    ▼
StockAgent (Orchestrator)
    ├── StockService     → Yahoo Finance API integration
    ├── AIService        → Claude API for analysis
    ├── PortfolioService → SQLite database operations
    ├── RateLimiter      → API throttling
    └── StockDisplay     → Rich terminal UI
```

### Project Structure

```
terminal-portfolio-manager/
├── main.py                    # CLI entry point
├── requirements.txt           # Python dependencies
├── .env.example               # Environment configuration template
├── data/
│   └── portfolio.db           # SQLite database (auto-created)
└── app/
    ├── config.py              # Application settings
    ├── agent/
    │   └── stock_agent.py     # Main orchestrator
    ├── services/
    │   ├── stock_service.py   # Yahoo Finance integration
    │   ├── ai_service.py      # Claude API integration
    │   ├── portfolio_service.py # Portfolio CRUD operations
    │   └── rate_limiter.py    # Sliding window rate limiter
    ├── models/
    │   ├── stock.py           # Stock and news data models
    │   ├── portfolio.py       # Portfolio and position models
    │   └── ai_response.py     # AI analysis response models
    ├── ui/
    │   ├── console.py         # Rich console wrapper
    │   ├── display.py         # Table and panel formatters
    │   └── prompts.py         # User input handling
    └── utils/
        ├── exceptions.py      # Custom exceptions
        ├── formatters.py      # Number and currency formatting
        └── validators.py      # Input validation
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `ANTHROPIC_API_KEY` | Your Anthropic API key (required for AI features) | - |
| `CLAUDE_MODEL` | Default Claude model to use | `claude-sonnet-4-20250514` |
| `CLAUDE_MAX_TOKENS` | Maximum tokens for AI responses | `4096` |
| `YFINANCE_REQUESTS_PER_MINUTE` | Rate limit for Yahoo Finance | `60` |
| `CLAUDE_REQUESTS_PER_MINUTE` | Rate limit for Claude API | `50` |

### Supported Claude Models

| Model | Description |
|-------|-------------|
| `claude-opus-4-5-20251101` | Most capable, best for complex analysis |
| `claude-opus-4-20250514` | High capability, balanced performance |
| `claude-sonnet-4-20250514` | Balanced speed and quality |
| `claude-haiku-3-5-20241022` | Fastest and most economical |

## Data Storage

Portfolio data is stored locally in a SQLite database at `data/portfolio.db`. The database is automatically initialized on first run and includes:

- **Positions** - Individual tax lots with purchase price, date, and shares
- **Snapshots** - Historical portfolio values for performance tracking
- **No external database required** - Everything runs locally

## Dependencies

- **yfinance** - Yahoo Finance API wrapper for stock data
- **anthropic** - Official Anthropic SDK for Claude API
- **rich** - Terminal UI with tables, panels, and colors
- **pydantic** - Data validation and serialization
- **python-dotenv** - Environment variable management

## Example Workflow

1. **Add positions to your portfolio:**
   ```
   > add
   Enter stock symbol: AAPL
   Number of shares: 50
   Purchase price per share: 150.00
   Purchase date (YYYY-MM-DD): 2024-06-15
   ```

2. **View your portfolio with live prices:**
   ```
   > portfolio
   ```

3. **Get AI analysis on a stock:**
   ```
   > analyze
   Enter stock symbol: NVDA
   Include AI analysis? [Y/n]: y
   ```

4. **Analyze your entire portfolio:**
   ```
   > analyze-portfolio
   ```

## License

MIT License
