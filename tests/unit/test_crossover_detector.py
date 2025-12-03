"""Unit tests for CrossoverDetector class."""

from spy_sma_alert_bot.services.crossover_detector import CrossoverDetector


def test_detect_crossovers_price_crosses_above_sma() -> None:
    """Test detection of price crossing above SMA."""
    current_price = 102.0
    smas = {25: 100.0, 50: 95.0}
    previous_states = {25: "below", 50: "above"}

    crossovers = CrossoverDetector.detect_crossovers(
        current_price, smas, previous_states
    )

    assert len(crossovers) == 1
    assert crossovers[0].sma_period == 25
    assert crossovers[0].direction == "above"
    assert crossovers[0].price == 102.0
    assert crossovers[0].sma_value == 100.0


def test_detect_crossovers_price_crosses_below_sma() -> None:
    """Test detection of price crossing below SMA."""
    current_price = 98.0
    smas = {25: 100.0, 50: 105.0}
    previous_states = {25: "above", 50: "below"}

    crossovers = CrossoverDetector.detect_crossovers(
        current_price, smas, previous_states
    )

    assert len(crossovers) == 1
    assert crossovers[0].sma_period == 25
    assert crossovers[0].direction == "below"
    assert crossovers[0].price == 98.0
    assert crossovers[0].sma_value == 100.0


def test_detect_crossovers_no_crossover() -> None:
    """Test when no crossover occurs."""
    current_price = 102.0
    smas = {25: 100.0, 50: 95.0}
    previous_states = {25: "above", 50: "above"}

    crossovers = CrossoverDetector.detect_crossovers(
        current_price, smas, previous_states
    )

    assert len(crossovers) == 0


def test_detect_crossovers_unknown_previous_state() -> None:
    """Test when previous state is unknown."""
    current_price = 102.0
    smas = {25: 100.0}
    previous_states = {25: "unknown"}

    crossovers = CrossoverDetector.detect_crossovers(
        current_price, smas, previous_states
    )

    assert len(crossovers) == 0


def test_detect_crossovers_multiple_smas() -> None:
    """Test detection with multiple SMAs."""
    current_price = 105.0
    smas = {25: 100.0, 50: 110.0, 75: 90.0}
    previous_states = {25: "below", 50: "below", 75: "above"}

    crossovers = CrossoverDetector.detect_crossovers(
        current_price, smas, previous_states
    )

    assert len(crossovers) == 2
    sma_periods = {c.sma_period for c in crossovers}
    assert sma_periods == {25, 50}

    crossover_25 = next(c for c in crossovers if c.sma_period == 25)
    assert crossover_25.direction == "above"
    assert crossover_25.price == 105.0
    assert crossover_25.sma_value == 100.0


def test_update_crossover_state() -> None:
    """Test updating crossover state based on current price."""
    smas = {25: 100.0, 50: 105.0, 75: 95.0}
    current_price = 102.0

    new_states = CrossoverDetector.update_crossover_state(smas, current_price)

    assert new_states == {25: "above", 50: "below", 75: "above"}


def test_update_crossover_state_unknown() -> None:
    """Test when price equals SMA value."""
    smas = {25: 100.0, 50: 105.0}
    current_price = 105.0

    new_states = CrossoverDetector.update_crossover_state(smas, current_price)

    assert new_states == {25: "below", 50: "unknown"}


def test_detect_crossovers_edge_cases() -> None:
    """Test edge cases in crossover detection."""
    crossovers = CrossoverDetector.detect_crossovers(100.0, {}, {})
    assert len(crossovers) == 0

    crossovers = CrossoverDetector.detect_crossovers(100.0, {25: 95.0}, {})
    assert len(crossovers) == 0
