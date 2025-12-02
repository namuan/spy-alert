"""ChartGenerator for the SPY SMA Alert Bot.

This module provides the ChartGenerator class which handles generating price charts
with SMA overlays, formatted for Telegram delivery, with visual styling for clarity.

Feature: spy-sma-alert-bot, Requirements 7.2 (100 days), 7.3 (distinguishable lines), 7.4 (legend).
"""

from typing import List, Dict, Optional
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
from datetime import datetime
from io import BytesIO

from ..models import PricePoint
from .sma_calculator import SMACalculator


class ChartGenerator:
    """Chart Generation Service.

    Responsibilities: Generate price charts with SMA overlays, format charts for Telegram delivery,
    apply visual styling for clarity.
    """

    def generate_chart(
        self, prices: List[PricePoint], sma_periods: List[int] = [25, 50, 75, 100]
    ) -> bytes:
        """Generate a chart of SPY closing prices with SMA overlays.

        Input: List[PricePoint] (historical prices, at least 100 days), optional sma_periods.
        Compute historical SMAs for each period using a sliding window.
        Plot closing prices as a line, overlay SMA lines for each period.
        Use different distinguishable colors: 25-day: blue, 50-day: orange, 75-day: green, 100-day: red.
        Display last 100 trading days.
        X-axis: dates, Y-axis: price.
        Include legend identifying 'SPY Close', 'SMA 25', 'SMA 50', 'SMA 75', 'SMA 100'.
        Title: 'SPY Price with SMA Overlays'.
        Export as PNG bytes using BytesIO.

        Args:
            prices: Historical prices (oldest first).
            sma_periods: SMA periods to plot.

        Returns:
            PNG bytes of the chart.

        Raises:
            ValueError: If fewer than 100 price points provided.
        """
        if len(prices) < 100:
            raise ValueError("Insufficient historical data: need at least 100 days")

        # Truncate to display last 100 trading days
        prices = prices[-100:]
        dates = [p.timestamp for p in prices]
        closes = [p.close for p in prices]

        # Compute historical SMAs using SMACalculator
        sma_history: Dict[int, List[Optional[float]]] = {}
        for period in sma_periods:
            early_padding = [np.nan] * (period - 1)
            historical_smas = [
                SMACalculator.calculate_sma([prices[j].close for j in range(i + 1)], period)
                for i in range(period - 1, len(prices))
            ]
            sma_history[period] = early_padding + historical_smas

        # Plot
        fig, ax = plt.subplots(figsize=(12, 6))
        fig.patch.set_facecolor('white')
        fig.patch.set_alpha(1.0)
        ax.set_facecolor('white')
        ax.plot(dates, closes, label="SPY Close", color="black", linewidth=1.5)

        colors = ["blue", "orange", "green", "red"]
        for period, color in zip(sma_periods, colors):
            sma_vals = sma_history[period]
            ax.plot(dates, sma_vals, label=f"SMA {period}", color=color, linewidth=1.5)

        # Formatting
        ax.set_title("SPY Price with SMA Overlays")
        ax.set_xlabel("Date")
        ax.set_ylabel("Price ($)")
        ax.legend()
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
        fig.autofmt_xdate()
        plt.tight_layout()

        # Export to PNG bytes
        buf = BytesIO()
        fig.savefig(buf, format="png", dpi=150, bbox_inches="tight", facecolor="white", transparent=False)
        buf.seek(0)
        plt.close('all')
        return buf.read()