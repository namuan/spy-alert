"""Configuration dataclass for the spy-alert bot."""

from dataclasses import dataclass
import os
import re
from typing import Any


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
            "Telegram token cannot be empty. Please provide a valid Telegram bot token in the format 'digits:alphanumeric'."
        )

    if not config.chat_id:
        raise ValueError(
            "Chat ID cannot be empty. Please provide a valid Telegram chat ID."
        )

    # Validate Telegram token format
    if not re.match(r"^\d+:[a-zA-Z0-9_-]{35}$", config.telegram_token):
        raise ValueError(
            "Invalid Telegram token format. Expected format: 'digits:alphanumeric' (e.g., '123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11'). Please check your token and ensure it matches the expected pattern."
        )

    # Validate numeric fields are positive integers
    if config.monitoring_interval is not None and config.monitoring_interval <= 0:
        raise ValueError(
            f"Monitoring interval must be a positive integer. Got: {config.monitoring_interval}. Please provide a positive integer value for MONITORING_INTERVAL."
        )

    if config.sma_short_window is not None and config.sma_short_window <= 0:
        raise ValueError(
            f"SMA short window must be a positive integer. Got: {config.sma_short_window}. Please provide a positive integer value for SMA_SHORT_WINDOW."
        )

    if config.sma_long_window is not None and config.sma_long_window <= 0:
        raise ValueError(
            f"SMA long window must be a positive integer. Got: {config.sma_long_window}. Please provide a positive integer value for SMA_LONG_WINDOW."
        )

    # Validate SMA window relationship
    if (
        config.sma_short_window is not None
        and config.sma_long_window is not None
        and config.sma_short_window >= config.sma_long_window
    ):
        raise ValueError(
            f"SMA short window ({config.sma_short_window}) must be smaller than SMA long window ({config.sma_long_window}). Please adjust the window sizes accordingly."
        )


def _get_required_env(name: str) -> str:
    value = os.getenv(name)
    if value is None:
        raise ValueError(f"Missing required environment variable: {name}")
    return value


def _parse_int_env(name: str) -> int | None:
    value = os.getenv(name)
    if value is None:
        return None
    try:
        return int(value)
    except ValueError:
        raise ValueError(f"Invalid {name} value: {value}") from None


def _parse_bool_env(name: str) -> bool | None:
    value = os.getenv(name)
    if value is None:
        return None
    return value.lower() in {"true", "1", "t", "y", "yes"}


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
    telegram_token = _get_required_env("TELEGRAM_TOKEN")
    chat_id = _get_required_env("TELEGRAM_CHAT_ID")

    # Read optional environment variables with type conversion
    monitoring_interval = _parse_int_env("MONITORING_INTERVAL")

    sma_short_window = _parse_int_env("SMA_SHORT_WINDOW")

    sma_long_window = _parse_int_env("SMA_LONG_WINDOW")

    debug = _parse_bool_env("DEBUG")

    config_args: dict[str, Any] = {
        "telegram_token": telegram_token,
        "chat_id": chat_id,
    }
    if monitoring_interval is not None:
        config_args["monitoring_interval"] = monitoring_interval
    if sma_short_window is not None:
        config_args["sma_short_window"] = sma_short_window
    if sma_long_window is not None:
        config_args["sma_long_window"] = sma_long_window
    if debug is not None:
        config_args["debug"] = debug

    config = BotConfig(**config_args)

    # Validate the configuration before returning
    validate_config(config)

    return config
