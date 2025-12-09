"""Price data service for the SPY SMA Alert Bot.

This module provides the PriceDataService class which handles fetching and validating
SPY price data from yfinance, with caching and error handling capabilities.
"""

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime, timedelta
import time
from typing import TYPE_CHECKING, Protocol, SupportsFloat, cast

import yfinance as yf

from spy_sma_alert_bot.models import PricePoint

if TYPE_CHECKING:
    from collections.abc import Callable


@dataclass
class CachedData:
    """Model for caching price data with timestamp."""

    data: list[PricePoint]
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

    def __init__(self) -> None:
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
                    raise RuntimeError(
                        f"Failed to fetch current price after {self._max_retries} attempts: {e}"
                    ) from e
                delay = min(self._initial_delay * (2**attempt), self._max_delay)
                time.sleep(delay)

        raise RuntimeError("Failed to fetch current price due to unknown error")

    def fetch_historical_prices(self, days: int) -> list[PricePoint]:
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

        for attempt in range(self._max_retries):
            try:
                spy = yf.Ticker("SPY")
                extra_days = max(20, int(days * 0.2))
                price_points = self._fetch_price_points(spy, days, extra_days)
                price_points.sort(key=lambda x: x.timestamp)
                price_points = price_points[-days:]

                if not self.validate_price_data(price_points):
                    raise ValueError("Invalid price data received")

                self._cache[days] = CachedData(
                    data=price_points, timestamp=datetime.now()
                )
                return price_points

            except (ValueError, IndexError, KeyError) as e:
                if attempt == self._max_retries - 1:
                    raise RuntimeError(
                        f"Failed to fetch historical prices after {self._max_retries} attempts: {e}"
                    ) from e
                delay = min(self._initial_delay * (2**attempt), self._max_delay)
                time.sleep(delay)

        raise RuntimeError("Failed to fetch historical prices due to unknown error")

    @staticmethod
    def _collect_points_from_history(data: "HistoryLike") -> list[PricePoint]:
        points: list[PricePoint] = []
        for ts, row in data.iterrows():
            if "Close" not in row:
                continue
            to_py_func = cast(
                "Callable[[], datetime] | None", getattr(ts, "to_pydatetime", None)
            )
            ts_dt: datetime = (
                to_py_func() if to_py_func is not None else cast("datetime", ts)
            )
            points.append(PricePoint(timestamp=ts_dt, close=float(row["Close"])))
        return points

    def _fetch_price_points(
        self, spy: yf.Ticker, days: int, extra_days: int
    ) -> list[PricePoint]:
        data = spy.history(period=f"{days + extra_days}d")
        if getattr(data, "empty", False):
            raise ValueError("No historical data available")

        price_points = self._collect_points_from_history(data)

        if len(price_points) < days:
            additional_days = days - len(price_points) + extra_days
            if additional_days > 0:
                more_data = spy.history(period=f"{additional_days}d")
                price_points.extend(self._collect_points_from_history(more_data))

        return price_points

    @staticmethod
    def validate_price_data(data: list[PricePoint]) -> bool:
        if not data:
            return False

        # Get a timezone-aware current time if needed, based on the first data point
        first_tz = data[0].timestamp.tzinfo
        now = datetime.now(first_tz) if first_tz else datetime.now()

        for point in data:
            if point.timestamp is None or point.timestamp > now:
                return False
            if point.close is None:
                return False
            if point.close <= 0:
                return False
            if point.close != point.close:
                return False
        return True

    def clear_cache(self) -> None:
        self._cache.clear()


class RowLike(Protocol):
    def __contains__(self, __key: str) -> bool: ...
    def __getitem__(self, __key: str) -> SupportsFloat: ...


class ColumnsLike(Protocol):
    def __contains__(self, __key: str) -> bool: ...


class HistoryLike(Protocol):
    def iterrows(self) -> Iterable[tuple[object, RowLike]]: ...
