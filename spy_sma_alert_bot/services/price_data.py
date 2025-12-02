"""Price data service for the SPY SMA Alert Bot.

This module provides the PriceDataService class which handles fetching and validating
SPY price data from yfinance, with caching and error handling capabilities.
"""

import time
from datetime import datetime, timedelta
from typing import List, Optional, Tuple

import yfinance as yf
from pydantic import BaseModel, ValidationError

from spy_sma_alert_bot.models import PricePoint

class CachedData(BaseModel):
    """Model for caching price data with timestamp."""
    data: List[PricePoint]
    timestamp: datetime

class PriceDataService:
    """Service for fetching and validating SPY price data.

    This service provides methods to fetch current and historical SPY price data,
    with built-in caching and error handling with exponential backoff.

    Attributes:
        _cache: Dictionary storing cached historical price data
        _cache_duration: Duration in seconds for which cached data is valid
        _max_retries: Maximum number of retry attempts for failed requests
        _initial_delay: Initial delay in seconds for exponential backoff
        _max_delay: Maximum delay in seconds for exponential backoff
    """

    def __init__(self):
        """Initialize the PriceDataService with default settings."""
        self._cache: dict[int, CachedData] = {}  # Key: days, Value: CachedData
        self._cache_duration = timedelta(minutes=5)  # 5-minute cache
        self._max_retries = 5
        self._initial_delay = 30  # 30 seconds initial delay
        self._max_delay = 300  # 5 minutes maximum delay

    def fetch_current_price(self) -> float:
        """Fetch the current SPY price.

        Returns:
            float: The current closing price of SPY.

        Raises:
            RuntimeError: If unable to fetch current price after retries.
        """
        for attempt in range(self._max_retries):
            try:
                spy = yf.Ticker("SPY")
                data = spy.history(period="1d")
                if data.empty or "Close" not in data.columns:
                    raise ValueError("No price data available")

                current_price = data["Close"].iloc[-1]
                return float(current_price)

            except (ValueError, IndexError, KeyError) as e:
                if attempt == self._max_retries - 1:
                    raise RuntimeError(f"Failed to fetch current price after {self._max_retries} attempts: {e}")
                delay = min(self._initial_delay * (2 ** attempt), self._max_delay)
                time.sleep(delay)

            except Exception as e:
                if attempt == self._max_retries - 1:
                    raise RuntimeError(f"Unexpected error fetching current price after {self._max_retries} attempts: {e}")
                delay = min(self._initial_delay * (2 ** attempt), self._max_delay)
                time.sleep(delay)

        raise RuntimeError("Failed to fetch current price due to unknown error")

    def fetch_historical_prices(self, days: int) -> List[PricePoint]:
        """Fetch historical SPY prices for the specified number of days.

        Args:
            days: Number of days of historical data to fetch. If less than 100,
                 it will be automatically increased to 100 to meet minimum requirements.

        Returns:
            List[PricePoint]: List of historical price points (at least 100 days).

        Raises:
            RuntimeError: If unable to fetch historical prices after retries.
        """
        # Ensure we always fetch at least 100 days
        days = max(100, days)

        # Check cache first
        if days in self._cache:
            cached = self._cache[days]
            if datetime.now() - cached.timestamp < self._cache_duration:
                return cached.data

        # If not in cache or cache expired, fetch fresh data
        for attempt in range(self._max_retries):
            try:
                spy = yf.Ticker("SPY")
                # Fetch extra days to account for weekends/holidays
                extra_days = max(20, int(days * 0.2))
                data = spy.history(period=f"{days + extra_days}d")

                if data.empty:
                    raise ValueError("No historical data available")

                # Convert to PricePoint objects
                price_points = []
                for timestamp, row in data.iterrows():
                    if "Close" in row:
                        price_points.append(PricePoint(
                            timestamp=timestamp.to_pydatetime(),
                            close=float(row["Close"])
                        ))

                # Ensure we have enough data points
                if len(price_points) < days:
                    # Try to fetch more data if we don't have enough
                    additional_days = days - len(price_points) + extra_days
                    if additional_days > 0:
                        more_data = spy.history(period=f"{additional_days}d")
                        for timestamp, row in more_data.iterrows():
                            if "Close" in row:
                                price_points.append(PricePoint(
                                    timestamp=timestamp.to_pydatetime(),
                                    close=float(row["Close"])
                                ))

                # Sort by timestamp (oldest first) and take the most recent 'days' points
                price_points.sort(key=lambda x: x.timestamp)
                price_points = price_points[-days:]

                # Validate the data
                if not self.validate_price_data(price_points):
                    raise ValueError("Invalid price data received")

                # Cache the result
                self._cache[days] = CachedData(
                    data=price_points,
                    timestamp=datetime.now()
                )

                return price_points

            except (ValueError, IndexError, KeyError) as e:
                if attempt == self._max_retries - 1:
                    raise RuntimeError(f"Failed to fetch historical prices after {self._max_retries} attempts: {e}")
                delay = min(self._initial_delay * (2 ** attempt), self._max_delay)
                time.sleep(delay)

            except Exception as e:
                if attempt == self._max_retries - 1:
                    raise RuntimeError(f"Unexpected error fetching historical prices after {self._max_retries} attempts: {e}")
                delay = min(self._initial_delay * (2 ** attempt), self._max_delay)
                time.sleep(delay)

        raise RuntimeError("Failed to fetch historical prices due to unknown error")

    def validate_price_data(self, data: List[PricePoint]) -> bool:
        """Validate price data for completeness and correctness.

        Args:
            data: List of PricePoint objects to validate.

        Returns:
            bool: True if data is valid, False otherwise.
        """
        if not data:
            return False

        for point in data:
            # Check timestamp is not None and not in the future
            if point.timestamp is None or point.timestamp > datetime.now():
                return False

            # Check close price is a positive number
            if point.close is None or point.close <= 0:
                return False

            # Check for NaN values
            if point.close != point.close:  # NaN check
                return False

        return True

    def clear_cache(self) -> None:
        """Clear the historical data cache."""
        self._cache.clear()