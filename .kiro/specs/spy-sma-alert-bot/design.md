# Design Document

## Overview

The SPY SMA Alert Bot is a Telegram bot that monitors the SPY ETF price and sends alerts when the price crosses above or below key Simple Moving Averages (25-day, 50-day, 75-day, and 100-day). The system consists of three main components: a Telegram bot interface for user interaction, a monitoring service that continuously checks for crossover events, and a chart generation service that creates visual representations of price data with SMA overlays.

The bot will be implemented in Python using the `python-telegram-bot` library for Telegram integration, `yfinance` or a similar library for fetching SPY price data, and `matplotlib` for chart generation. The system will maintain state in memory (with optional persistence) to track user subscriptions and previous crossover states to prevent duplicate alerts.

## Architecture

The system follows a modular architecture with clear separation of concerns:

```
┌─────────────────────────────────────────────────────────────┐
│                     Telegram Bot Layer                      │
│  (Command Handlers: /start, /stop, /status)                 │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────┐
│                   Application Core                          │
│  - User Subscription Manager                                │
│  - Alert Dispatcher                                         │
└─────────┬───────────────────────────────┬───────────────────┘
          │                               │
┌─────────▼─────────────┐    ┌───────────▼──────────────────┐
│  Monitoring Service   │    │   Chart Generation Service   │
│  - Price Fetcher      │    │   - Data Formatter           │
│  - SMA Calculator     │    │   - Plot Generator           │
│  - Crossover Detector │    │   - Image Exporter           │
└─────────┬─────────────┘    └──────────────────────────────┘
          │
┌─────────▼──────────────┐
│  Price Data Provider   │
│  (yfinance/Alpha       │
│   Vantage API)         │
└────────────────────────┘
```

The monitoring service runs as a background task that periodically fetches price data, calculates SMAs, detects crossovers, and triggers alerts through the alert dispatcher.

## Components and Interfaces

### 1. Telegram Bot Interface

**Responsibilities:**
- Handle incoming commands from users (/start, /stop, /status)
- Send alert messages and chart images to subscribed users
- Manage bot lifecycle and error handling

**Key Methods:**
```python
async def handle_start(update: Update, context: ContextTypes.DEFAULT_TYPE)
async def handle_stop(update: Update, context: ContextTypes.DEFAULT_TYPE)
async def handle_status(update: Update, context: ContextTypes.DEFAULT_TYPE)
async def send_alert(chat_id: int, message: str, chart_image: bytes)
```

### 2. User Subscription Manager

**Responsibilities:**
- Track which users are subscribed to alerts
- Add and remove user subscriptions
- Retrieve list of active subscribers

**Key Methods:**
```python
def subscribe_user(chat_id: int) -> bool
def unsubscribe_user(chat_id: int) -> bool
def is_subscribed(chat_id: int) -> bool
def get_all_subscribers() -> List[int]
```

### 3. Price Data Service

**Responsibilities:**
- Fetch current and historical SPY price data
- Cache data to minimize API calls
- Validate data completeness and correctness

**Key Methods:**
```python
def fetch_current_price() -> float
def fetch_historical_prices(days: int) -> List[PricePoint]
def validate_price_data(data: List[PricePoint]) -> bool
```

### 4. SMA Calculator

**Responsibilities:**
- Calculate Simple Moving Averages for specified periods
- Maintain efficient computation using sliding windows

**Key Methods:**
```python
def calculate_sma(prices: List[float], period: int) -> float
def calculate_all_smas(prices: List[float]) -> Dict[int, float]
```

### 5. Crossover Detector

**Responsibilities:**
- Detect when price crosses above or below an SMA
- Track previous states to prevent duplicate alerts
- Identify which SMAs have been crossed

**Key Methods:**
```python
def detect_crossovers(current_price: float, previous_price: float, 
                      smas: Dict[int, float], previous_states: Dict[int, str]) -> List[Crossover]
def update_crossover_state(smas: Dict[int, float], current_price: float) -> Dict[int, str]
```

### 6. Chart Generation Service

**Responsibilities:**
- Generate price charts with SMA overlays
- Format charts for Telegram delivery
- Apply visual styling for clarity

**Key Methods:**
```python
def generate_chart(prices: List[PricePoint], smas: Dict[int, List[float]]) -> bytes
def format_chart_for_telegram(chart: matplotlib.figure.Figure) -> bytes
```

### 7. Monitoring Service

**Responsibilities:**
- Orchestrate periodic price checks
- Coordinate between price fetching, SMA calculation, and crossover detection
- Trigger alerts when crossovers are detected

**Key Methods:**
```python
async def start_monitoring(interval_minutes: int)
async def check_for_crossovers() -> List[Crossover]
async def process_crossovers(crossovers: List[Crossover])
```

## Data Models

### PricePoint
```python
@dataclass
class PricePoint:
    timestamp: datetime
    close: float
```

### Crossover
```python
@dataclass
class Crossover:
    sma_period: int  # 25, 50, 75, or 100
    direction: str   # "above" or "below"
    price: float
    sma_value: float
    timestamp: datetime
```

### CrossoverState
```python
@dataclass
class CrossoverState:
    sma_period: int
    position: str  # "above", "below", or "unknown"
```

### BotConfig
```python
@dataclass
class BotConfig:
    telegram_token: str
    price_api_key: Optional[str]
    monitoring_interval_minutes: int = 5
    chart_history_days: int = 100
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*


### Property 1: Upward crossover detection and notification
*For any* price sequence where the current price crosses above any SMA (25, 50, 75, or 100-day), all subscribed users should receive a notification indicating an upward crossover with the correct SMA period.
**Validates: Requirements 1.1, 1.3, 1.5, 1.7**

### Property 2: Downward crossover detection and notification
*For any* price sequence where the current price crosses below any SMA (25, 50, 75, or 100-day), all subscribed users should receive a notification indicating a downward crossover with the correct SMA period.
**Validates: Requirements 1.2, 1.4, 1.6, 1.8**

### Property 3: User subscription registration
*For any* user ID, when the user sends the "/start" command, the user should be registered as subscribed and receive a confirmation message.
**Validates: Requirements 2.1**

### Property 4: User subscription cancellation
*For any* subscribed user ID, when the user sends the "/stop" command, the user should be unregistered from subscriptions and receive a confirmation message.
**Validates: Requirements 2.2**

### Property 5: Status command completeness
*For r sending the "/staommand, the response should contain the user's subscription status, current SPY price, and all four SMA values (25, 50, 75, 100-day).
**Validates: Requirements 2.3**

### Property 6: SMA calculation correctness
*For any* sequence of closing prices and any SMA period N, the calculated SMA should equal the arithmetic mean of the last N closing prices.
**Validates: Requirements 3.1**

### Property 7: Historical data sufficiency
*For any* request for historical price data, the returned data should contain at least 100 trading days of closing prices.
**Validates: Requirements 3.2**

### Property 8: Price data validation
*For any* price data received from the provider, the data should be validated to contain both closing prices and timestamps before being used in calculations.
**Validates: Requirements 3.3**

### Property 9: Monitoring interval compliance
*For any* monitoring cycle, the time between consecutive crossover checks should be between 1 and 15 minutes.
**Validates: Requirements 4.1**

### Property 10: Duplicate alert prevention (idempotence)
*For any* crossover event, detecting the same crossover multiple times without an intervening price change should result in only one notification being sent.
**Validates: Requirements 4.2**

### Property 11: Crossover detection accuracy
*For any* two consecutive price checks, a crossover should only be detected when the price position relative to an SMA changes from one side to the other (above to below or below to above).
**Validates: Requirements 4.3**

### Property 12: Crossover message completeness
*For any* crossover notification, the message should include the crossover direction, SMA period, current SPY price, SMA value, and timestamp.
**Validates: Requirements 5.1, 5.2**

### Property 13: Status message SMA display
*For any* status response, the message should display all four SMA values (25, 50, 75, 100-day) alongside the current SPY price.
**Validates: Requirements 5.3**

### Property 14: Price provider error resilience
*For any* failure when fetching price data, the system should log the error, retry after a delay, and continue running without crashing.
**Validates: Requirements 6.1**

### Property 15: Telegram API error resilience
*For any* failure when sending a Telegram message, the system should log the failure and continue monitoring without stopping.
**Validates: Requirements 6.2**

### Property 16: Invalid data rejection
*For any* invalid or incomplete price data received, the system should reject the data, log a warning, and not use it for calculations.
**Validates: Requirements 6.3**

### Property 17: General error resilience
*For any* unexpected error during monitoring, the system should log the error details and continue operating.
**Validates: Requirements 6.4**

### Property 18: Chart image inclusion in crossover alerts
*For any* crossover notification, the message should include a chart image showing SPY price history with all four SMA lines overlaid.
**Validates: Requirements 7.1**

### Property 19: Chart historical data completeness
*For any* generated chart image, the chart should display at least 100 trading days of price history.
**Validates: Requirements 7.2**

### Property 20: Chart SMA visual distinction
*For any* generated chart image, each of the four SMA lines should have visually distinguishable colors or line styles.
**Validates: Requirements 7.3**

### Property 21: Chart legend presence
*For any* generated chart image, the chart should include a legend identifying each SMA line and the price line.
**Validates: Requirements 7.4**

### Property 22: Chart inclusion in status response
*For any* status command response, the message should include a chart image showing current price and SMA positions.
**Validates: Requirements 7.5**

### Property 23: Configuration loading with defaults
*For any* bot startup, the system should read the Telegram token, price API credentials, and monitoring interval from configuration, using default values for optional settings.
**Validates: Requirements 8.1, 8.2, 8.3**

### Property 24: Required configuration validation
*For any* bot startup where required configuration values (Telegram token) are missing, the system should log an error and refuse to start.
**Validates: Requirements 8.4**

## Error Handling

The system implements comprehensive error handling at multiple levels:

### 1. Network Errors
- **Price Data Fetching**: Implement exponential backoff retry logic (initial delay: 30s, max delay: 5 minutes, max retries: 5)
- **Telegram API**: Retry failed message sends up to 3 times with 10-second delays
- **Timeout Handling**: Set reasonable timeouts for all network requests (30 seconds for price data, 10 seconds for Telegram API)

### 2. Data Validation Errors
- **Missing Fields**: Check for required fields (timestamp, close price) before processing
- **Invalid Values**: Reject negative prices, future timestamps, or NaN values
- **Insufficient Data**: Ensure at least 100 days of data before calculating 100-day SMA

### 3. Calculation Errors
- **Division by Zero**: Handle edge cases in SMA calculation when period is zero or data is empty
- **Floating Point Precision**: Use appropriate rounding for price comparisons (2 decimal places)

### 4. State Management Errors
- **Concurrent Access**: Use thread-safe data structures for user subscriptions and crossover states
- **State Corruption**: Validate state before using it; reset to safe defaults if corrupted

### 5. Chart Generation Errors
- **Memory Limits**: Limit chart size and resolution to prevent memory exhaustion
- **File I/O**: Handle temporary file creation failures gracefully
- **Format Errors**: Catch matplotlib exceptions and log detailed error messages

### 6. Logging Strategy
- **Error Logs**: All exceptions with full stack traces
- **Warning Logs**: Data validation failures, retry attempts
- **Info Logs**: Successful crossover detections, user subscriptions/unsubscriptions
- **Debug Logs**: Price fetches, SMA calculations (disabled in production)

## Testing Strategy

The testing strategy employs both unit testing and property-based testing to ensure comprehensive coverage and correctness.

### Unit Testing Approach

Unit tests will verify specific examples and integration points:

1. **Command Handlers**: Test /start, /stop, /status commands with specific user IDs
2. **Edge Cases**: 
   - Empty price data
   - Single data point
   - Exact price equals SMA value
   - User subscribing twice
   - User unsubscribing when not subscribed
3. **Integration Points**:
   - Bot initialization with valid/invalid config
   - Message formatting with real crossover data
   - Chart generation with sample price data

### Property-Based Testing Approach

Property-based tests will verify universal properties across many randomly generated inputs using the **Hypothesis** library for Python. Each property test will:

- Run a minimum of 100 iterations with randomly generated data
- Be tagged with a comment referencing the specific correctness property from this design document
- Use the format: `# Feature: spy-sma-alert-bot, Property N: [property text]`

**Key Property Tests:**

1. **SMA Calculation (Property 6)**: Generate random price sequences and verify SMA equals arithmetic mean
2. **Crossover Detection (Properties 1, 2, 11)**: Generate price sequences with known crossovers and verify detection
3. **Duplicate Prevention (Property 10)**: Run detection multiple times on same data, verify single alert
4. **Message Completeness (Properties 12, 13)**: Generate random crossovers, verify all required fields present
5. **Data Validation (Property 8)**: Generate invalid price data, verify rejection
6. **Configuration Loading (Property 23)**: Generate various config combinations, verify correct loading

**Test Data Generators:**

- Price sequences: Random walks with configurable volatility
- SMA periods: Random selection from [25, 50, 75, 100]
- User IDs: Random integers in valid Telegram ID range
- Timestamps: Random dates within reasonable ranges
- Configuration objects: Random valid/invalid combinations

### Test Organization

```
tests/
├── unit/
│   ├── test_commands.py
│   ├── test_sma_calculator.py
│   ├── test_crossover_detector.py
│   ├── test_chart_generator.py
│   └── test_config.py
├── property/
│   ├── test_sma_properties.py
│   ├── test_crossover_properties.py
│   ├── test_message_properties.py
│   └── test_resilience_properties.py
└── integration/
    └── test_end_to_end.py
```

### Mocking Strategy

- **External APIs**: Mock yfinance and Telegram API calls in unit tests
- **Time**: Mock datetime for testing time-dependent behavior
- **File System**: Mock file operations for chart generation tests
- **Property Tests**: Minimize mocking to test real logic; use test doubles only for external services

## Implementation Notes

### Technology Stack
- **Language**: Python 3.10+
- **Telegram Bot**: python-telegram-bot (v20+)
- **Price Data**: yfinance library (free, no API key required)
- **Charting**: matplotlib with seaborn styling
- **Testing**: pytest + hypothesis
- **Configuration**: python-dotenv for environment variables
- **Async**: asyncio for concurrent operations

### Deployment Considerations
- **Hosting**: Can run on any Python-capable platform (AWS Lambda, Heroku, VPS)
- **Persistence**: Optional SQLite database for user subscriptions (in-memory acceptable for MVP)
- **Monitoring**: Structured logging to stdout for container-based deployments
- **Scheduling**: Use asyncio tasks for monitoring loop (no external scheduler needed)

### Performance Considerations
- **API Rate Limits**: yfinance has no strict rate limits but implement caching (5-minute cache for price data)
- **Chart Generation**: Generate charts on-demand, cache for 5 minutes
- **Memory Usage**: Limit historical data to 100 days, clear old data periodically
- **Concurrent Users**: Async message sending to handle multiple subscribers efficiently

### Security Considerations
- **Token Storage**: Store Telegram bot token in environment variables, never in code
- **Input Validation**: Sanitize all user inputs to prevent injection attacks
- **Rate Limiting**: Implement per-user rate limiting for commands (max 10 commands/minute)
- **Error Messages**: Don't expose internal d