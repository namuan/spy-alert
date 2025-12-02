"""SMA Calculator for the SPY SMA Alert Bot.

This module provides the SMACalculator class which handles the calculation of
Simple Moving Averages (SMAs) for SPY price data. It supports calculating individual
SMAs for specified periods as well as all four key SMAs (25, 50, 75, 100-day)
simultaneously.

Feature: spy-sma-alert-bot, Property 6: For any sequence of closing prices and any SMA period N,
the calculated SMA should equal the arithmetic mean of the last N closing prices.
"""

from typing import List, Dict, Optional

class SMACalculator:
    """Calculator for Simple Moving Averages (SMAs).

    This class provides methods to calculate SMAs for different periods based on
    historical price data. It handles edge cases such as insufficient data and
    provides efficient calculations for multiple SMAs.

    Attributes:
        DEFAULT_PERIODS: The default SMA periods to calculate (25, 50, 75, 100-day).
    """

    DEFAULT_PERIODS = [25, 50, 75, 100]

    @staticmethod
    def calculate_sma(prices: List[float], period: int) -> Optional[float]:
        """Calculate the Simple Moving Average for a given period.

        Args:
            prices: List of closing prices (most recent last).
            period: The period for the SMA calculation.

        Returns:
            The calculated SMA value, or None if there's insufficient data or invalid input.

        Raises:
            ValueError: If period is less than 1.
        """
        # Validate input period
        if period < 1:
            raise ValueError("Period must be at least 1")

        # Handle edge cases
        if not prices:
            return None

        if len(prices) < period:
            return None

        # Calculate arithmetic mean of the last 'period' prices
        window = prices[-period:]
        return sum(window) / period

    @classmethod
    def calculate_all_smas(cls, prices: List[float]) -> Dict[int, Optional[float]]:
        """Calculate all four default SMAs (25, 50, 75, 100-day).

        Args:
            prices: List of closing prices (most recent last).

        Returns:
            Dictionary mapping SMA periods to their calculated values.
            Values are None if there's insufficient data for a given period.
        """
        if not prices:
            return {period: None for period in cls.DEFAULT_PERIODS}

        return {
            period: cls.calculate_sma(prices, period)
            for period in cls.DEFAULT_PERIODS
        }