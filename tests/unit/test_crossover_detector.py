"""Unit tests for CrossoverDetector class."""

import pytest
from datetime import datetime
from typing import Dict, List

from spy_sma_alert_bot.models import Crossover, CrossoverState
from spy_sma_alert_bot.services.crossover_detector import CrossoverDetector

class TestCrossoverDetector:
    """Test suite for CrossoverDetector class."""

    def test_detect_crossovers_price_crosses_above_sma(self):
        """Test detection of price crossing above SMA."""
        current_price = 102.0
        previous_price = 98.0
        smas = {25: 100.0, 50: 95.0}
        previous_states = {25: "below", 50: "above"}

        crossovers = CrossoverDetector.detect_crossovers(
            current_price, previous_price, smas, previous_states
        )

        assert len(crossovers) == 1
        assert crossovers[0].sma_period == 25
        assert crossovers[0].direction == "above"
        assert crossovers[0].price == 102.0
        assert crossovers[0].sma_value == 100.0

    def test_detect_crossovers_price_crosses_below_sma(self):
        """Test detection of price crossing below SMA."""
        current_price = 98.0
        previous_price = 102.0
        smas = {25: 100.0, 50: 105.0}
        previous_states = {25: "above", 50: "below"}

        crossovers = CrossoverDetector.detect_crossovers(
            current_price, previous_price, smas, previous_states
        )

        assert len(crossovers) == 1
        assert crossovers[0].sma_period == 25
        assert crossovers[0].direction == "below"
        assert crossovers[0].price == 98.0
        assert crossovers[0].sma_value == 100.0

    def test_detect_crossovers_no_crossover(self):
        """Test when no crossover occurs."""
        current_price = 102.0
        previous_price = 101.0
        smas = {25: 100.0, 50: 95.0}
        previous_states = {25: "above", 50: "above"}

        crossovers = CrossoverDetector.detect_crossovers(
            current_price, previous_price, smas, previous_states
        )

        assert len(crossovers) == 0

    def test_detect_crossovers_unknown_previous_state(self):
        """Test when previous state is unknown."""
        current_price = 102.0
        previous_price = 101.0
        smas = {25: 100.0}
        previous_states = {25: "unknown"}

        crossovers = CrossoverDetector.detect_crossovers(
            current_price, previous_price, smas, previous_states
        )

        assert len(crossovers) == 0

    def test_detect_crossovers_multiple_smas(self):
        """Test detection with multiple SMAs."""
        current_price = 105.0
        previous_price = 95.0
        smas = {25: 100.0, 50: 110.0, 75: 90.0}
        previous_states = {25: "below", 50: "below", 75: "above"}

        crossovers = CrossoverDetector.detect_crossovers(
            current_price, previous_price, smas, previous_states
        )

        assert len(crossovers) == 2
        sma_periods = {c.sma_period for c in crossovers}
        assert sma_periods == {25, 50}

        # Check 25-day SMA crossover (below -> above)
        crossover_25 = next(c for c in crossovers if c.sma_period == 25)
        assert crossover_25.direction == "above"
        assert crossover_25.price == 105.0
        assert crossover_25.sma_value == 100.0

        # Check 50-day SMA crossover (below -> below, no crossover)
        # Should not be in results

        # Check 75-day SMA (above -> above, no crossover)
        # Should not be in results

    def test_update_crossover_state(self):
        """Test updating crossover state based on current price."""
        smas = {25: 100.0, 50: 105.0, 75: 95.0}
        current_price = 102.0

        new_states = CrossoverDetector.update_crossover_state(smas, current_price)

        assert new_states == {
            25: "above",
            50: "below",
            75: "above"
        }

    def test_update_crossover_state_unknown(self):
        """Test when price equals SMA value."""
        smas = {25: 100.0, 50: 105.0}
        current_price = 105.0

        new_states = CrossoverDetector.update_crossover_state(smas, current_price)

        assert new_states == {
            25: "below",
            50: "unknown"
        }

    def test_detect_crossovers_edge_cases(self):
        """Test edge cases in crossover detection."""
        # Test with empty SMAs
        crossovers = CrossoverDetector.detect_crossovers(
            100.0, 99.0, {}, {}
        )
        assert len(crossovers) == 0

        # Test with SMA not in previous states
        crossovers = CrossoverDetector.detect_crossovers(
            100.0, 99.0, {25: 95.0}, {}
        )
        assert len(crossovers) == 0