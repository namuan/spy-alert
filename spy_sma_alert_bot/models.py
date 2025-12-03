"""Data models for the SPY SMA Alert Bot.

This module contains dataclasses that represent core data structures used in the
SPY SMA Alert Bot application, including price points, crossover events, and
state tracking for SMA crossovers.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Literal


@dataclass
class PricePoint:
    """Represents a single price point with timestamp and closing price.

    Attributes:
        timestamp: The datetime when this price point was recorded
        close: The closing price at the given timestamp
    """

    timestamp: datetime
    close: float


@dataclass
class Crossover:
    """Represents a crossover event between price and SMA.

    A crossover occurs when the price moves above or below a Simple Moving Average
    (SMA) of a specific period.

    Attributes:
        sma_period: The period of the SMA (25, 50, 75, or 100)
        direction: The direction of the crossover ("above" or "below")
        price: The price at which the crossover occurred
        sma_value: The value of the SMA at the time of crossover
        timestamp: The datetime when the crossover occurred
    """

    sma_period: int
    direction: Literal["above", "below"]
    price: float
    sma_value: float
    timestamp: datetime | None


@dataclass
class CrossoverState:
    """Tracks the current position of price relative to a specific SMA.

    This class maintains the state of whether the price is currently above,
    below, or in an unknown position relative to a specific SMA period.

    Attributes:
        sma_period: The period of the SMA being tracked
        position: The current position of price relative to SMA
                 ("above", "below", or "unknown")
    """

    sma_period: int
    position: Literal["above", "below", "unknown"]
