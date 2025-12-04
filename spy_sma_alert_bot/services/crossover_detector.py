"""Crossover Detector for SPY SMA Alert Bot.

This module contains the CrossoverDetector class which identifies when SPY price crosses
above or below Simple Moving Averages (SMAs) of various periods (25, 50, 75, 100-day).
It tracks previous states to prevent duplicate alerts for the same crossover event.
"""

from spy_sma_alert_bot.models import Crossover


class CrossoverDetector:
    """Detects price crossovers above or below SMAs and manages crossover state.

    This class provides functionality to detect when the SPY price crosses above or below
    various Simple Moving Averages (25, 50, 75, 100-day) and maintains state to prevent
    duplicate alerts for the same crossover event.
    """

    @staticmethod
    def detect_crossovers(
        current_price: float,
        previous_or_smas: float | dict[int, float],
        smas: dict[int, float] | None = None,
        previous_states: dict[int, str] | None = None,
    ) -> list[Crossover]:
        """Identifies crossovers between current and previous price/SMA states.

        Supports two calling conventions:
        - detect_crossovers(current_price, smas, previous_states)
        - detect_crossovers(current_price, previous_price, smas, previous_states)
        """
        if isinstance(previous_or_smas, dict):
            prev_price = None
            smas_dict = previous_or_smas
            prev_states = previous_states or {}
        else:
            prev_price = float(previous_or_smas)
            smas_dict = smas or {}
            prev_states = previous_states or {}

        crossovers: list[Crossover] = []

        for sma_period, sma_value in smas_dict.items():
            previous_state = CrossoverDetector._prev_state(
                sma_period, sma_value, prev_price, prev_states or {}
            )
            current_position = CrossoverDetector._curr_pos(current_price, sma_value)
            co = CrossoverDetector._mk_co(
                sma_period, current_price, sma_value, previous_state, current_position
            )
            if co is not None:
                crossovers.append(co)

        return crossovers

    @staticmethod
    def update_crossover_state(
        smas: dict[int, float], current_price: float
    ) -> dict[int, str]:
        """Updates the tracking state for each SMA based on current price.

        Args:
            smas: Dictionary of SMA periods to their current values
            current_price: The current SPY price

        Returns:
            Dictionary mapping SMA periods to their current position states
        """
        new_states: dict[int, str] = {}

        for sma_period, sma_value in smas.items():
            if current_price > sma_value:
                new_states[sma_period] = "above"
            elif current_price < sma_value:
                new_states[sma_period] = "below"
            else:
                new_states[sma_period] = "unknown"

        return new_states

    @staticmethod
    def _prev_state(
        period: int,
        sma_value: float,
        prev_price: float | None,
        prev_states: dict[int, str],
    ) -> str:
        if period in prev_states:
            return prev_states[period]
        if prev_price is None:
            return "unknown"
        if prev_price > sma_value:
            return "above"
        if prev_price < sma_value:
            return "below"
        return "unknown"

    @staticmethod
    def _curr_pos(current_price: float, sma_value: float) -> str:
        if current_price > sma_value:
            return "above"
        if current_price < sma_value:
            return "below"
        return "unknown"

    @staticmethod
    def _mk_co(
        period: int,
        price: float,
        sma_value: float,
        prev_state: str,
        curr_pos: str,
    ) -> Crossover | None:
        if prev_state == "unknown" or curr_pos == "unknown":
            return None
        if prev_state == "above" and curr_pos == "below":
            return Crossover(
                sma_period=period,
                direction="below",
                price=price,
                sma_value=sma_value,
                timestamp=None,
            )
        if prev_state == "below" and curr_pos == "above":
            return Crossover(
                sma_period=period,
                direction="above",
                price=price,
                sma_value=sma_value,
                timestamp=None,
            )
        return None
