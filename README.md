# SPY SMA Alert Bot

A Telegram bot that monitors the SPY (SPDR S&P 500 ETF Trust) stock price and sends real-time alerts when the price crosses above or below Simple Moving Averages (SMAs) of various periods (25, 50, 75, and 100 days).

## Project Overview

The SPY SMA Alert Bot provides automated trading signals and market monitoring through Telegram notifications. It helps users track key technical indicators without constant manual monitoring by:

- Monitoring SPY price in real-time
- Detecting SMA crossover events
- Sending Telegram alerts with detailed information
- Generating price charts with SMA overlays
- Supporting multiple user subscriptions

## Key Features

✅ Real-time SPY price monitoring
✅ SMA crossover detection (25, 50, 75, 100 day periods)
✅ Telegram bot interface with commands
✅ Chart generation with SMA overlays
✅ Property-based testing for reliability
✅ Caching mechanism to minimize API calls

## Project Structure

```
spy_sma_alert_bot/
├── config.py            # Configuration management
├── models.py            # Data models (PricePoint, Crossover, etc.)
└── services/
    ├── price_data.py    # SPY price data fetching
    └── sma_calculator.py # SMA calculation logic
```

## Setup Instructions

### Prerequisites

- Python 3.12+
- Telegram Bot Token (obtain from @BotFather)
- Telegram Chat ID

### Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd spy-alert
   ```

2. Install dependencies:
   ```bash
   make install
   # or
   uv sync
   ```

3. Install pre-commit hooks:
   ```bash
   uv run pre-commit install
   ```

### Configuration

1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` with your configuration:
   ```ini
   TELEGRAM_TOKEN=your_bot_token
   TELEGRAM_CHAT_ID=your_chat_id
   MONITORING_INTERVAL_MINUTES=5  # Optional
   ```

## Usage

### Running the Application

```bash
make run
# or
uv run python -m spy_sma_alert_bot.main
```

### Telegram Commands

- `/start` - Subscribe to alerts
- `/stop` - Unsubscribe from alerts
- `/status` - Get current price, SMA values, and chart

### Alert Types

The bot sends two types of alerts:
1. **Upward crossover**: Price crosses above SMA
2. **Downward crossover**: Price crosses below SMA

Each alert includes:
- Current price
- SMA value
- Chart image
- Timestamp

## Testing

### Property-Based Testing

The project uses Hypothesis for property-based testing to validate universal properties across random inputs:

- SMA calculation correctness
- Price data sufficiency (minimum 100 days)
- Data validation robustness

### Running Tests

```bash
# Run all tests
make test

# Run specific test file
make test-single TEST=test_file.py
```

## Development

### Code Quality Tools

- **ruff**: Linting and formatting
- **basedpyright**: Strict type checking
- **pre-commit**: Automated quality checks
- **radon**: Code complexity analysis
- **skylos**: Dead code detection

### Quality Commands

```bash
# Full quality check
make check

# Auto-fix formatting
make format

# Comprehensive quality assessment
uv run poe quality
```

## Deployment

### Packaging

```bash
# Create executable
make package

# Install on macOS
make install-macosx
```

## Special Considerations

🔹 **API Rate Limiting**: 5-minute caching minimizes yfinance API calls
🔹 **Error Resilience**: Exponential backoff for network failures
🔹 **Thread Safety**: Designed for concurrent user management
🔹 **Data Validation**: Strict validation of price data and configuration
🔹 **Type Safety**: Maximum strictness with basedpyright
🔹 **Testing Rigor**: Property-based testing ensures mathematical correctness

## Contributing

1. Follow strict coding standards (ruff, basedpyright)
2. Write property tests for new features
3. Maintain 80% test coverage
4. Use pre-commit hooks for quality assurance

## License

MIT License