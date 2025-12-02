"""Configuration dataclass for the spy-alert bot."""

import os
import re
from dataclasses import dataclass

@dataclass
class BotConfig:
    """Configuration structure for the spy-alert Telegram bot.

    This dataclass defines the required and optional configuration parameters
    for the spy-alert bot that monitors SMA (Simple Moving Average) crossovers.
    """

    # Required fields
    telegram_token: str
    chat_id: str

    # Optional fields with default values
    monitoring_interval: int = 300
    sma_short_window: int = 10
    sma_long_window: int = 50
    debug: bool = False

def validate_config(config: BotConfig) -> None:
    """Validate the BotConfig instance according to required rules.

    This function validates that:
    - Required fields (telegram_token and chat_id) are not None or empty strings
    - Telegram token follows the expected format (digits:alphanumeric)
    - Numeric fields are positive integers

    Args:
        config: BotConfig instance to validate

    Raises:
        ValueError: If any validation rule is violated, with descriptive messages
                   explaining what went wrong and how to fix it.
    """

    # Validate required fields
    if not config.telegram_token:
        raise ValueError(
            "Telegram token cannot be empty. "
            "Please provide a valid Telegram bot token in the format 'digits:alphanumeric'."
        )

    if not config.chat_id:
        raise ValueError(
            "Chat ID cannot be empty. "
            "Please provide a valid Telegram chat ID."
        )

    # Validate Telegram token format
    if not re.match(r'^\d+:[a-zA-Z0-9_-]{35}$', config.telegram_token):
        raise ValueError(
            "Invalid Telegram token format. "
            "Expected format: 'digits:alphanumeric' (e.g., '123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11'). "
            "Please check your token and ensure it matches the expected pattern."
        )

    # Validate numeric fields are positive integers
    if config.monitoring_interval is not None and config.monitoring_interval <= 0:
        raise ValueError(
            f"Monitoring interval must be a positive integer. Got: {config.monitoring_interval}. "
            "Please provide a positive integer value for MONITORING_INTERVAL."
        )

    if config.sma_short_window is not None and config.sma_short_window <= 0:
        raise ValueError(
            f"SMA short window must be a positive integer. Got: {config.sma_short_window}. "
            "Please provide a positive integer value for SMA_SHORT_WINDOW."
        )

    if config.sma_long_window is not None and config.sma_long_window <= 0:
        raise ValueError(
            f"SMA long window must be a positive integer. Got: {config.sma_long_window}. "
            "Please provide a positive integer value for SMA_LONG_WINDOW."
        )

    # Validate SMA window relationship
    if (config.sma_short_window is not None and config.sma_long_window is not None and
        config.sma_short_window >= config.sma_long_window):
        raise ValueError(
            f"SMA short window ({config.sma_short_window}) must be smaller than "
            f"SMA long window ({config.sma_long_window}). "
            "Please adjust the window sizes accordingly."
        )

def load_config() -> BotConfig:
    """Load configuration from environment variables and return a BotConfig instance.

    This function reads environment variables, converts them to the appropriate types,
    and creates a BotConfig instance with the loaded values. Required fields must be
    present in the environment, while optional fields use default values from BotConfig
    when not specified.

    Returns:
        BotConfig: A configured instance of the BotConfig dataclass.

    Raises:
        ValueError: If required environment variables are missing or type conversion fails.
    """
    # Read and validate required environment variables
    telegram_token = os.getenv("TELEGRAM_TOKEN")
    if telegram_token is None:
        raise ValueError("Missing required environment variable: TELEGRAM_TOKEN")

    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    if chat_id is None:
        raise ValueError("Missing required environment variable: TELEGRAM_CHAT_ID")

    # Read optional environment variables with type conversion
    monitoring_interval = os.getenv("MONITORING_INTERVAL")
    if monitoring_interval is not None:
        try:
            monitoring_interval = int(monitoring_interval)
        except ValueError:
            raise ValueError(f"Invalid MONITORING_INTERVAL value: {monitoring_interval}")

    sma_short_window = os.getenv("SMA_SHORT_WINDOW")
    if sma_short_window is not None:
        try:
            sma_short_window = int(sma_short_window)
        except ValueError:
            raise ValueError(f"Invalid SMA_SHORT_WINDOW value: {sma_short_window}")

    sma_long_window = os.getenv("SMA_LONG_WINDOW")
    if sma_long_window is not None:
        try:
            sma_long_window = int(sma_long_window)
        except ValueError:
            raise ValueError(f"Invalid SMA_LONG_WINDOW value: {sma_long_window}")

    debug = os.getenv("DEBUG")
    if debug is not None:
        debug = debug.lower() in ("true", "1", "t", "y", "yes")

    config = BotConfig(
        telegram_token=telegram_token,
        chat_id=chat_id,
        monitoring_interval=monitoring_interval,
        sma_short_window=sma_short_window,
        sma_long_window=sma_long_window,
        debug=debug,
    )

    # Validate the configuration before returning
    validate_config(config)

    return config