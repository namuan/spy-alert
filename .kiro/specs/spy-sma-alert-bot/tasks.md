# Implementation Plan

- [x] 1. Set up project structure and dependencies
  - Update pyproject.toml for spy-sma-alert-bot (change project name, add dependencies: python-telegram-bot, yfinance, matplotlib, hypothesis)
  - Update Makefile for spy-sma-alert-bot (update PROJECTNAME and run command)
  - Create project directory structure (spy_sma_alert_bot/, tests/unit/, tests/property/)
  - Create .env.example file with required configuration variables (TELEGRAM_BOT_TOKEN, MONITORING_INTERVAL_MINUTES)
  - Run uv sync to install dependencies
  - _Requirements: 8.1, 8.2, 8.3_

- [x] 2. Implement configuration management
  - Create BotConfig dataclass for configuration values
  - Implement configuration loader that reads from environment variables
  - Add default values for optional settings (monitoring interval)
  - Implement validation for required configuration (Telegram token)
  - _Requirements: 8.1, 8.2, 8.3, 8.4_

- [ ]* 2.1 Write property test for configuration loading
  - **Property 23: Configuration loading with defaults**
  - **Validates: Requirements 8.1, 8.2, 8.3**

- [ ]* 2.2 Write property test for configuration validation
  - **Property 24: Required configuration validation**
  - **Validates: Requirements 8.4**

- [ ] 3. Implement data models
  - Create PricePoint dataclass with timestamp and close price
  - Create Crossover dataclass with SMA period, direction, price, SMA value, and timestamp
  - Create CrossoverState dataclass for tracking position relative to SMAs
  - _Requirements: 3.1, 3.3_

- [ ] 4. Implement price data service
  - Create PriceDataService class with yfinance integration
  - Implement fetch_current_price() method
  - Implement fetch_historical_prices(days) method to retrieve at least 100 days
  - Implement validate_price_data() to check for required fields (timestamp, close)
  - Add caching mechanism (5-minute cache) to minimize API calls
  - _Requirements: 3.2, 3.3_

- [ ]* 4.1 Write property test for historical data sufficiency
  - **Property 7: Historical data sufficiency**
  - **Validates: Requirements 3.2**

- [ ]* 4.2 Write property test for price data validation
  - **Property 8: Price data validation**
  - **Validates: Requirements 3.3**

- [ ] 5. Implement SMA calculator
  - Create SMACalculator class
  - Implement calculate_sma(prices, period) to compute arithmetic mean
  - Implement calculate_all_smas(prices) to compute all four SMAs (25, 50, 75, 100)
  - Handle edge cases (insufficient data, empty lists)
  - _Requirements: 3.1_

- [ ]* 5.1 Write property test for SMA calculation correctness
  - **Property 6: SMA calculation correctness**
  - **Validates: Requirements 3.1**

- [ ] 6. Implement crossover detector
  - Create CrossoverDetector class
  - Implement detect_crossovers() to identify when price crosses above/below SMAs
  - Implement update_crossover_state() to track current position relative to each SMA
  - Add state tracking to prevent duplicate alerts for same crossover
  - _Requirements: 4.2, 4.3_

- [ ]* 6.1 Write property test for upward crossover detection
  - **Property 1: Upward crossover detection and notification**
  - **Validates: Requirements 1.1, 1.3, 1.5, 1.7**

- [ ]* 6.2 Write property test for downward crossover detection
  - **Property 2: Downward crossover detection and notification**
  - **Validates: Requirements 1.2, 1.4, 1.6, 1.8**

- [ ]* 6.3 Write property test for crossover detection accuracy
  - **Property 11: Crossover detection accuracy**
  - **Validates: Requirements 4.3**

- [ ]* 6.4 Write property test for duplicate alert prevention
  - **Property 10: Duplicate alert prevention (idempotence)**
  - **Validates: Requirements 4.2**

- [ ] 7. Implement chart generation service
  - Create ChartGenerator class using matplotlib
  - Implement generate_chart() to create price chart with SMA overlays
  - Configure chart to display at least 100 days of history
  - Use different colors/styles for each SMA line (25, 50, 75, 100)
  - Add legend identifying each line
  - Implement format_chart_for_telegram() to export as bytes for Telegram
  - _Requirements: 7.1, 7.2, 7.3, 7.4_

- [ ]* 7.1 Write property test for chart historical data completeness
  - **Property 19: Chart historical data completeness**
  - **Validates: Requirements 7.2**

- [ ]* 7.2 Write property test for chart SMA visual distinction
  - **Property 20: Chart SMA visual distinction**
  - **Validates: Requirements 7.3**

- [ ]* 7.3 Write property test for chart legend presence
  - **Property 21: Chart legend presence**
  - **Validates: Requirements 7.4**

- [ ] 8. Implement user subscription manager
  - Create UserSubscriptionManager class
  - Implement subscribe_user(chat_id) method
  - Implement unsubscribe_user(chat_id) method
  - Implement is_subscribed(chat_id) method
  - Implement get_all_subscribers() method
  - Use thread-safe data structure (set with lock or asyncio-safe structure)
  - _Requirements: 2.1, 2.2_

- [ ]* 8.1 Write property test for user subscription registration
  - **Property 3: User subscription registration**
  - **Validates: Requirements 2.1**

- [ ]* 8.2 Write property test for user subscription cancellation
  - **Property 4: User subscription cancellation**
  - **Validates: Requirements 2.2**

- [ ] 9. Implement message formatting utilities
  - Create MessageFormatter class
  - Implement format_crossover_message() with all required fields (direction, SMA period, price, SMA value, timestamp)
  - Implement format_status_message() with subscription status, current price, and all SMA values
  - Implement format_confirmation_messages() for subscribe/unsubscribe
  - _Requirements: 5.1, 5.2, 5.3_

- [ ]* 9.1 Write property test for crossover message completeness
  - **Property 12: Crossover message completeness**
  - **Validates: Requirements 5.1, 5.2**

- [ ]* 9.2 Write property test for status message SMA display
  - **Property 13: Status message SMA display**
  - **Validates: Requirements 5.3**

- [ ] 10. Implement Telegram bot command handlers
  - Create TelegramBot class with python-telegram-bot
  - Implement handle_start() command to subscribe users
  - Implement handle_stop() command to unsubscribe users
  - Implement handle_status() command to show current status with chart
  - Integrate with UserSubscriptionManager for subscription operations
  - Integrate with MessageFormatter for response messages
  - _Requirements: 2.1, 2.2, 2.3, 7.5_

- [ ]* 10.1 Write property test for status command completeness
  - **Property 5: Status command completeness**
  - **Validates: Requirements 2.3**

- [ ]* 10.2 Write property test for chart inclusion in status response
  - **Property 22: Chart inclusion in status response**
  - **Validates: Requirements 7.5**

- [ ] 11. Implement alert dispatcher
  - Create AlertDispatcher class
  - Implement send_alert() method to send messages with chart images to users
  - Implement send_alert_to_all_subscribers() to broadcast to all subscribed users
  - Add error handling for failed message sends (log and continue)
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 1.8, 6.2, 7.1_

- [ ]* 11.1 Write property test for chart image inclusion in crossover alerts
  - **Property 18: Chart image inclusion in crossover alerts**
  - **Validates: Requirements 7.1**

- [ ]* 11.2 Write property test for Telegram API error resilience
  - **Property 15: Telegram API error resilience**
  - **Validates: Requirements 6.2**

- [ ] 12. Implement monitoring service
  - Create MonitoringService class
  - Implement check_for_crossovers() to orchestrate price fetch, SMA calculation, and crossover detection
  - Implement process_crossovers() to generate charts and dispatch alerts
  - Implement start_monitoring() with async loop at configured interval (1-15 minutes)
  - Add error handling with exponential backoff for price data fetching
  - Add logging for all operations (info, warning, error levels)
  - _Requirements: 4.1, 6.1, 6.3, 6.4_

- [ ]* 12.1 Write property test for monitoring interval compliance
  - **Property 9: Monitoring interval compliance**
  - **Validates: Requirements 4.1**

- [ ]* 12.2 Write property test for price provider error resilience
  - **Property 14: Price provider error resilience**
  - **Validates: Requirements 6.1**

- [ ]* 12.3 Write property test for invalid data rejection
  - **Property 16: Invalid data rejection**
  - **Validates: Requirements 6.3**

- [ ]* 12.4 Write property test for general error resilience
  - **Property 17: General error resilience**
  - **Validates: Requirements 6.4**

- [ ] 13. Implement main application entry point
  - Create main.py with application initialization
  - Load configuration using BotConfig
  - Initialize all services (PriceDataService, SMACalculator, CrossoverDetector, ChartGenerator, UserSubscriptionManager, AlertDispatcher, MonitoringService)
  - Initialize and start Telegram bot
  - Start monitoring service as background task
  - Add graceful shutdown handling
  - _Requirements: 8.1, 8.2, 8.3, 8.4_

- [ ] 14. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ]* 15. Create integration tests
  - Write end-to-end test simulating full crossover detection and alert flow
  - Test bot startup with various configuration scenarios
  - Test complete user journey (subscribe, receive alert, check status, unsubscribe)
  - _Requirements: All_

- [ ] 16. Create documentation
  - Write README.md with setup instructions
  - Document environment variables in .env.example
  - Add usage examples for bot commands
  - Document deployment options
  - _Requirements: 8.1, 8.2, 8.3_
