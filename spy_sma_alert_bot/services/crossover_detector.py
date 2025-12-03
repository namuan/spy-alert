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
        smas: dict[int, float],
        previous_states: dict[int, str],
    ) -> list[Crossover]:
        """Identifies crossovers between current and previous price/SMA states.

        Args:
            current_price: The current SPY price
            smas: Dictionary of SMA periods to their current values
            previous_states: Dictionary of SMA periods to their previous position states

        Returns:
            List of Crossover objects representing detected crossover events
        """
        crossovers: list[Crossover] = []

        for sma_period, sma_value in smas.items():
            previous_state = previous_states.get(sma_period, "unknown")

            # Determine current position
            if current_price > sma_value:
                current_position = "above"
            elif current_price < sma_value:
                current_position = "below"
            else:
                current_position = "unknown"

            # Check for crossover events
            if previous_state == "unknown":
                # No previous state, cannot determine crossover
                continue

            if previous_state == "above" and current_position == "below":
                # Price crossed below SMA
                crossovers.append(
                    Crossover(
                        sma_period=sma_period,
                        direction="below",
                        price=current_price,
                        sma_value=sma_value,
                        timestamp=None,  # Will be set by caller
                    )
                )
            elif previous_state == "below" and current_position == "above":
                # Price crossed above SMA
                crossovers.append(
                    Crossover(
                        sma_period=sma_period,
                        direction="above",
                        price=current_price,
                        sma_value=sma_value,
                        timestamp=None,  # Will be set by caller
                    )
                )
            # If positions are the same, no crossover occurred

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
