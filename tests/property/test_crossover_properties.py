"""Property tests for CrossoverDetector.

This module contains property-based tests for the CrossoverDetector class,
verifying universal properties across many randomly generated inputs.
"""

from typing import Dict, List
import math
from datetime import datetime

from hypothesis import given, settings, strategies as st
import pytest

from spy_sma_alert_bot.models import Crossover
from spy_sma_alert_bot.services.crossover_detector import CrossoverDetector

# Feature: spy-sma-alert-bot, Property 1: Upward crossover detection and notification
@settings(max_examples=100, deadline=None)
@given(
    sma_period=st.sampled_from([25, 50, 75, 100]),
    previous_price=st.floats(min_value=50.0, max_value=200.0),
    sma_value=st.floats(min_value=50.0, max_value=200.0),
    price_increment=st.floats(min_value=0.1, max_value=20.0)
)
def test_upward_crossover_detection(
    sma_period: int,
    previous_price: float,
    sma_value: float,
    price_increment: float
) -> None:
    """Property test for upward crossover detection and notification.

    For any price sequence where the current price crosses above any SMA (25, 50, 75, or 100-day),
    the detector should identify the upward crossover with the correct SMA period.

    Validates: Requirements 1.1, 1.3, 1.5, 1.7
    """
    # Ensure we have an upward crossover scenario
    # Previous price should be below SMA, current price should be above SMA
    if previous_price >= sma_value:
        # Adjust previous price to be below SMA
        previous_price = sma_value - abs(price_increment)

    current_price = sma_value + abs(price_increment)

    # Handle edge case where price equals SMA exactly
    if math.isclose(current_price, sma_value, rel_tol=1e-9):
        current_price = sma_value + 0.01

    # Create SMAs dictionary with the selected period
    smas = {sma_period: sma_value}

    # Set previous state to "below" to create upward crossover scenario
    previous_states = {sma_period: "below"}

    # Detect crossovers
    crossovers = CrossoverDetector.detect_crossovers(
        current_price, previous_price, smas, previous_states
    )

    # Verify exactly one crossover was detected
    assert len(crossovers) == 1, f"Expected exactly 1 crossover, got {len(crossovers)}"

    # Get the detected crossover
    crossover = crossovers[0]

    # Verify the crossover has the correct SMA period
    assert crossover.sma_period == sma_period, (
        f"Expected SMA period {sma_period}, got {crossover.sma_period}"
    )

    # Verify the crossover has direction="above"
    assert crossover.direction == "above", (
        f"Expected direction 'above', got '{crossover.direction}'"
    )

    # Verify the crossover contains the correct price
    assert math.isclose(crossover.price, current_price, rel_tol=1e-9), (
        f"Expected price {current_price}, got {crossover.price}"
    )

    # Verify the crossover contains the correct SMA value
    assert math.isclose(crossover.sma_value, sma_value, rel_tol=1e-9), (
        f"Expected SMA value {sma_value}, got {crossover.sma_value}"
    )

    # Verify the timestamp is None (as per detector implementation)
    assert crossover.timestamp is None, (
        f"Expected timestamp to be None, got {crossover.timestamp}"
    )

@settings(max_examples=50, deadline=None)
@given(
    sma_period=st.sampled_from([25, 50, 75, 100]),
    price=st.floats(min_value=50.0, max_value=200.0),
    sma_value=st.floats(min_value=50.0, max_value=200.0)
)
def test_upward_crossover_edge_cases(
    sma_period: int,
    price: float,
    sma_value: float
) -> None:
    """Test edge cases for upward crossover detection."""
    # Test case 1: Price exactly equals SMA (should not trigger crossover)
    smas = {sma_period: sma_value}
    previous_states = {sma_period: "below"}

    # Use a small epsilon to handle floating point precision
    epsilon = 0.0001
    crossovers = CrossoverDetector.detect_crossovers(
        sma_value + epsilon, sma_value - epsilon, smas, previous_states
    )

    assert len(crossovers) == 1, "Should detect crossover when price crosses SMA"

    # Test case 2: No crossover when previous state is unknown
    previous_states = {sma_period: "unknown"}
    crossovers = CrossoverDetector.detect_crossovers(
        price, price - 1.0, smas, previous_states
    )

    assert len(crossovers) == 0, "Should not detect crossover with unknown previous state"

    # Test case 3: No crossover when price stays below SMA
    previous_states = {sma_period: "below"}
    crossovers = CrossoverDetector.detect_crossovers(
        sma_value - 0.1, sma_value - 0.2, smas, previous_states
    )

    assert len(crossovers) == 0, "Should not detect crossover when price stays below SMA"

# Feature: spy-sma-alert-bot, Property 2: Downward crossover detection and notification
@settings(max_examples=100, deadline=None)
@given(
    sma_period=st.sampled_from([25, 50, 75, 100]),
    previous_price=st.floats(min_value=50.0, max_value=200.0),
    sma_value=st.floats(min_value=50.0, max_value=200.0),
    price_decrement=st.floats(min_value=0.1, max_value=20.0)
)
def test_downward_crossover_detection(
    sma_period: int,
    previous_price: float,
    sma_value: float,
    price_decrement: float
) -> None:
    """Property test for downward crossover detection and notification.

    For any price sequence where the current price crosses below any SMA (25, 50, 75, or 100-day),
    the detector should identify the downward crossover with the correct SMA period.

    Validates: Requirements 1.2, 1.4, 1.6, 1.8
    """
    # Ensure we have a downward crossover scenario
    # Previous price should be above SMA, current price should be below SMA
    if previous_price <= sma_value:
        # Adjust previous price to be above SMA
        previous_price = sma_value + abs(price_decrement)

    current_price = sma_value - abs(price_decrement)

    # Handle edge case where price equals SMA exactly
    if math.isclose(current_price, sma_value, rel_tol=1e-9):
        current_price = sma_value - 0.01

    # Create SMAs dictionary with the selected period
    smas = {sma_period: sma_value}

    # Set previous state to "above" to create downward crossover scenario
    previous_states = {sma_period: "above"}

    # Detect crossovers
    crossovers = CrossoverDetector.detect_crossovers(
        current_price, previous_price, smas, previous_states
    )

    # Verify exactly one crossover was detected
    assert len(crossovers) == 1, f"Expected exactly 1 crossover, got {len(crossovers)}"

    # Get the detected crossover
    crossover = crossovers[0]

    # Verify the crossover has the correct SMA period
    assert crossover.sma_period == sma_period, (
        f"Expected SMA period {sma_period}, got {crossover.sma_period}"
    )

    # Verify the crossover has direction="below"
    assert crossover.direction == "below", (
        f"Expected direction 'below', got '{crossover.direction}'"
    )

    # Verify the crossover contains the correct price
    assert math.isclose(crossover.price, current_price, rel_tol=1e-9), (
        f"Expected price {current_price}, got {crossover.price}"
    )

    # Verify the crossover contains the correct SMA value
    assert math.isclose(crossover.sma_value, sma_value, rel_tol=1e-9), (
        f"Expected SMA value {sma_value}, got {crossover.sma_value}"
    )

    # Verify the timestamp is None (as per detector implementation)
    assert crossover.timestamp is None, (
        f"Expected timestamp to be None, got {crossover.timestamp}"
    )

@settings(max_examples=50, deadline=None)
@given(
    sma_period=st.sampled_from([25, 50, 75, 100]),
    price=st.floats(min_value=50.0, max_value=200.0),
    sma_value=st.floats(min_value=50.0, max_value=200.0)
)
def test_downward_crossover_edge_cases(
    sma_period: int,
    price: float,
    sma_value: float
) -> None:
    """Test edge cases for downward crossover detection."""
    # Test case 1: Price exactly equals SMA (should not trigger crossover)
    smas = {sma_period: sma_value}
    previous_states = {sma_period: "above"}

    # Use a small epsilon to handle floating point precision
    epsilon = 0.0001
    crossovers = CrossoverDetector.detect_crossovers(
        sma_value - epsilon, sma_value + epsilon, smas, previous_states
    )

    assert len(crossovers) == 1, "Should detect crossover when price crosses SMA"

    # Test case 2: No crossover when previous state is unknown
    previous_states = {sma_period: "unknown"}
    crossovers = CrossoverDetector.detect_crossovers(
        price, price + 1.0, smas, previous_states
    )

    assert len(crossovers) == 0, "Should not detect crossover with unknown previous state"

    # Test case 3: No crossover when price stays above SMA
    previous_states = {sma_period: "above"}
    crossovers = CrossoverDetector.detect_crossovers(
        sma_value + 0.1, sma_value + 0.2, smas, previous_states
    )

    assert len(crossovers) == 0, "Should not detect crossover when price stays above SMA"

# Feature: spy-sma-alert-bot, Property 11: Crossover detection accuracy
@settings(max_examples=100, deadline=None)
@given(
    sma_period=st.sampled_from([25, 50, 75, 100]),
    previous_price=st.floats(min_value=50.0, max_value=200.0),
    sma_value=st.floats(min_value=50.0, max_value=200.0),
    price_movement=st.floats(min_value=-20.0, max_value=20.0),
    previous_state=st.sampled_from(["above", "below", "unknown"])
)
def test_crossover_detection_accuracy(
    sma_period: int,
    previous_price: float,
    sma_value: float,
    price_movement: float,
    previous_state: str
) -> None:
    """Property test for crossover detection accuracy.

    For any two consecutive price checks, a crossover should only be detected when
    the price position relative to an SMA changes from one side to the other
    (above to below or below to above).

    Validates: Requirement 4.3
    """
    # Calculate current price based on movement
    current_price = previous_price + price_movement

    # Create SMAs dictionary with the selected period
    smas = {sma_period: sma_value}

    # Set previous state - this should match the actual previous position
    # to create valid test scenarios
    if previous_state == "above":
        # Ensure previous price is actually above SMA
        if previous_price <= sma_value:
            previous_price = sma_value + abs(price_movement) + 0.1
    elif previous_state == "below":
        # Ensure previous price is actually below SMA
        if previous_price >= sma_value:
            previous_price = sma_value - abs(price_movement) - 0.1

    # Recalculate current price after adjusting previous price
    current_price = previous_price + price_movement

    # Set previous states
    previous_states = {sma_period: previous_state}

    # Detect crossovers
    crossovers = CrossoverDetector.detect_crossovers(
        current_price, previous_price, smas, previous_states
    )

    # Determine current position
    if current_price > sma_value:
        current_position = "above"
    elif current_price < sma_value:
        current_position = "below"
    else:
        current_position = "unknown"

    # Check for price equal to SMA (no crossover)
    price_equals_sma = math.isclose(current_price, sma_value, rel_tol=1e-9)

    # Verify crossover detection accuracy
    if previous_state == "unknown":
        # No crossover should be detected when previous state is unknown
        assert len(crossovers) == 0, (
            f"No crossover should be detected when previous state is unknown. "
            f"Previous state: {previous_state}, Current position: {current_position}, "
            f"Crossovers: {len(crossovers)}"
        )
    elif price_equals_sma:
        # No crossover should be detected when price equals SMA
        assert len(crossovers) == 0, (
            f"No crossover should be detected when price equals SMA. "
            f"Previous state: {previous_state}, Previous price: {previous_price}, "
            f"Current price: {current_price}, SMA: {sma_value}, Crossovers: {len(crossovers)}"
        )
    elif previous_state == current_position:
        # No crossover should be detected when price stays on the same side
        assert len(crossovers) == 0, (
            f"No crossover should be detected when price stays on the same side. "
            f"Previous state: {previous_state}, Current position: {current_position}, "
            f"Crossovers: {len(crossovers)}"
        )
    elif previous_state != current_position and current_position != "unknown":
        # Crossover should be detected when price position changes
        assert len(crossovers) == 1, (
            f"Exactly one crossover should be detected when price position changes. "
            f"Previous state: {previous_state}, Current position: {current_position}, "
            f"Crossovers: {len(crossovers)}"
        )

        # Verify the detected crossover
        crossover = crossovers[0]

        # Verify the crossover has the correct SMA period
        assert crossover.sma_period == sma_period, (
            f"Expected SMA period {sma_period}, got {crossover.sma_period}"
        )

        # Verify the correct crossover direction is detected
        if previous_state == "below" and current_position == "above":
            assert crossover.direction == "above", (
                f"Expected direction 'above' for upward crossover, got '{crossover.direction}'"
            )
        elif previous_state == "above" and current_position == "below":
            assert crossover.direction == "below", (
                f"Expected direction 'below' for downward crossover, got '{crossover.direction}'"
            )

        # Verify the crossover contains the correct price
        assert math.isclose(crossover.price, current_price, rel_tol=1e-9), (
            f"Expected price {current_price}, got {crossover.price}"
        )

        # Verify the crossover contains the correct SMA value
        assert math.isclose(crossover.sma_value, sma_value, rel_tol=1e-9), (
            f"Expected SMA value {sma_value}, got {crossover.sma_value}"
        )

        # Verify the timestamp is None (as per detector implementation)
        assert crossover.timestamp is None, (
            f"Expected timestamp to be None, got {crossover.timestamp}"
        )
    else:
        # No crossover should be detected in other cases
        assert len(crossovers) == 0, (
            f"No crossover should be detected in this scenario. "
            f"Previous state: {previous_state}, Current position: {current_position}, "
            f"Crossovers: {len(crossovers)}"
        )
# Feature: spy-sma-alert-bot, Property 10: Duplicate alert prevention (idempotence)
@settings(max_examples=100, deadline=None)
@given(
    sma_period=st.sampled_from([25, 50, 75, 100]),
    sma_value=st.floats(min_value=50.0, max_value=200.0),
    first_direction=st.sampled_from(["above", "below"]),
    num_duplicates=st.integers(min_value=1, max_value=5),
    cross_back=st.booleans(),
    initial_distance=st.floats(min_value=0.01, max_value=10.0),
    noise=st.floats(min_value=-0.3, max_value=0.3),
    cross_delta=st.floats(min_value=0.01, max_value=10.0),
)
def test_duplicate_alert_prevention(
    sma_period: int,
    sma_value: float,
    first_direction: str,
    num_duplicates: int,
    cross_back: bool,
    initial_distance: float,
    noise: float,
    cross_delta: float,
) -> None:
    """Property test for duplicate alert prevention (idempotence).

    For any crossover event, detecting the same crossover multiple times without an
    intervening price change should result in only one notification being sent.
    Subsequent detections with price changes that maintain the same position relative
    to SMA should not trigger alerts. New crossovers (price changes position) do
    generate alerts.

    Validates: Requirement 4.2
    """
    smas: Dict[int, float] = {sma_period: sma_value}

    # Initial previous state opposite to create first crossover
    initial_previous_state: str = "below" if first_direction == "above" else "above"
    previous_states: Dict[int, str] = {sma_period: initial_previous_state}

    # Arbitrary initial previous price (not used in detection logic)
    previous_price: float = sma_value

    # First crossover price
    sign: int = 1 if first_direction == "above" else -1
    current_price: float = sma_value + sign * initial_distance

    # First detection: expect exactly one crossover
    crossovers = CrossoverDetector.detect_crossovers(
        current_price, previous_price, smas, previous_states
    )
    assert len(crossovers) == 1, f"Expected 1 crossover, got {len(crossovers)}"
    crossover = crossovers[0]
    assert crossover.sma_period == sma_period
    assert crossover.direction == first_direction
    assert math.isclose(crossover.price, current_price, rel_tol=1e-9)
    assert math.isclose(crossover.sma_value, sma_value, rel_tol=1e-9)
    assert crossover.timestamp is None

    # Update states after first detection
    previous_states = CrossoverDetector.update_crossover_state(smas, current_price)
    previous_price = current_price

    # Multiple duplicate detections with noise (same side)
    current_position = first_direction  # "above" or "below"
    for _ in range(num_duplicates):
        detect_price = current_price + noise
        # Clamp to ensure same side (no accidental crossover)
        if current_position == "above":
            detect_price = max(sma_value + 0.001, detect_price)
        else:  # below
            detect_price = min(sma_value - 0.001, detect_price)

        # Should not detect duplicate crossover
        crossovers = CrossoverDetector.detect_crossovers(
            detect_price, previous_price, smas, previous_states
        )
        assert len(crossovers) == 0, "No duplicate alerts on same-side price changes"

        # Update states
        previous_states = CrossoverDetector.update_crossover_state(smas, detect_price)
        previous_price = detect_price
        current_price = detect_price

    # Test cross back to opposite side if requested
    if cross_back:
        new_sign = -sign
        new_direction = "below" if first_direction == "above" else "above"
        cross_price = sma_value + new_sign * cross_delta

        # Should detect new crossover
        crossovers = CrossoverDetector.detect_crossovers(
            cross_price, previous_price, smas, previous_states
        )
        assert len(crossovers) == 1, f"Expected 1 new crossover, got {len(crossovers)}"
        crossover = crossovers[0]
        assert crossover.sma_period == sma_period
        assert crossover.direction == new_direction
        assert math.isclose(crossover.price, cross_price, rel_tol=1e-9)
        assert math.isclose(crossover.sma_value, sma_value, rel_tol=1e-9)
        assert crossover.timestamp is None