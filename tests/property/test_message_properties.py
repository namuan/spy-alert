from datetime import datetime, timedelta

from hypothesis import given, settings
import hypothesis.strategies as st

from spy_sma_alert_bot.services.message_formatter import MessageFormatter


# Feature: spy-sma-alert-bot, Property 12: Crossover message completeness
@settings(max_examples=50, deadline=None)
@given(
    direction=st.sampled_from(["above", "below"]),
    period=st.sampled_from([25, 50, 75, 100]),
    price=st.floats(
        min_value=300.0, max_value=700.0, allow_nan=False, allow_infinity=False
    ),
    sma_value=st.floats(
        min_value=300.0, max_value=700.0, allow_nan=False, allow_infinity=False
    ),
    ts=st.datetimes(
        min_value=datetime(2020, 1, 1),
        max_value=datetime.now() + timedelta(days=1),
    ),
)
def test_crossover_message_completeness(
    direction: str, period: int, price: float, sma_value: float, ts: datetime
) -> None:
    msg = MessageFormatter.format_crossover_message(
        direction, period, price, sma_value, ts
    )
    assert direction in msg
    assert f"{period}-day SMA" in msg
    assert f"{price:.2f}" in msg
    assert f"{sma_value:.2f}" in msg
    assert ts.strftime("%Y-%m-%d") in msg


# Feature: spy-sma-alert-bot, Property 13: Status message SMA display
@settings(max_examples=50, deadline=None)
@given(
    data=st.tuples(
        st.booleans(),
        st.floats(
            min_value=300.0, max_value=700.0, allow_nan=False, allow_infinity=False
        ),
        st.one_of(
            st.none(),
            st.floats(
                min_value=300.0, max_value=700.0, allow_nan=False, allow_infinity=False
            ),
        ),
        st.one_of(
            st.none(),
            st.floats(
                min_value=300.0, max_value=700.0, allow_nan=False, allow_infinity=False
            ),
        ),
        st.one_of(
            st.none(),
            st.floats(
                min_value=300.0, max_value=700.0, allow_nan=False, allow_infinity=False
            ),
        ),
        st.one_of(
            st.none(),
            st.floats(
                min_value=300.0, max_value=700.0, allow_nan=False, allow_infinity=False
            ),
        ),
    )
)
def test_status_message_sma_display(
    data: tuple[bool, float, float | None, float | None, float | None, float | None],
) -> None:
    subscribed, current_price, sma25, sma50, sma75, sma100 = data
    smas = {25: sma25, 50: sma50, 75: sma75, 100: sma100}
    msg = MessageFormatter.format_status_message(
        subscribed=subscribed, current_price=current_price, smas=smas
    )
    assert f"${current_price:.2f}" in msg
    for period, val in smas.items():
        assert f"SMA {period}:" in msg
        if val is None:
            assert "N/A" in msg
        else:
            assert f"${float(val):.2f}" in msg
