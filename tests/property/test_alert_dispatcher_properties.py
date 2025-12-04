import asyncio
from datetime import datetime, timedelta
import io

from hypothesis import given, settings
import hypothesis.strategies as st

from spy_sma_alert_bot.models import PricePoint
from spy_sma_alert_bot.services.alert_dispatcher import AlertDispatcher
from spy_sma_alert_bot.services.chart_generator import ChartGenerator
from spy_sma_alert_bot.services.message_formatter import MessageFormatter
from spy_sma_alert_bot.services.user_subscription_manager import (
    UserSubscriptionManager,
)


class FakeBot:
    def __init__(self) -> None:
        self.sent: list[tuple[int, bytes, str]] = []
        self.fail_for: set[int] = set()

    async def send_photo(self, chat_id: int, photo: io.BytesIO, caption: str) -> None:
        if chat_id in self.fail_for:
            raise RuntimeError("send_photo failure")
        self.sent.append((chat_id, photo.getvalue(), caption))


def build_prices(n: int) -> list[PricePoint]:
    start = datetime.now() - timedelta(days=n)
    points: list[PricePoint] = [
        PricePoint(timestamp=start + timedelta(days=i), close=400.0 + i)
        for i in range(n)
    ]
    return points


# Feature: spy-sma-alert-bot, Property 18: Chart image inclusion in crossover alerts
@settings(max_examples=25, deadline=None)
@given(
    direction=st.sampled_from(["above", "below"]),
    sma_period=st.sampled_from([25, 50, 75, 100]),
    price=st.floats(
        min_value=300.0, max_value=700.0, allow_nan=False, allow_infinity=False
    ),
    sma_value=st.floats(
        min_value=300.0, max_value=700.0, allow_nan=False, allow_infinity=False
    ),
)
def test_chart_image_inclusion_in_crossover_alerts(
    direction: str, sma_period: int, price: float, sma_value: float
) -> None:
    async def run_test() -> None:
        bot = FakeBot()
        subs = UserSubscriptionManager()
        await subs.subscribe_user(9999)

        dispatcher = AlertDispatcher(
            bot=bot,
            subscriptions=subs,
            chart_generator=ChartGenerator(),
        )

        caption = MessageFormatter.format_crossover_message(
            direction=direction,
            sma_period=sma_period,
            price=price,
            sma_value=sma_value,
            timestamp=datetime.now(),
        )
        prices = build_prices(120)

        ok = await dispatcher.send_alert(9999, caption, prices)
        assert ok is True
        assert len(bot.sent) == 1
        chat_id, photo_bytes, sent_caption = bot.sent[0]
        assert chat_id == 9999
        assert photo_bytes.startswith(b"\x89PNG")
        assert len(photo_bytes) > 5000
        assert sent_caption == caption

    asyncio.run(run_test())


# Feature: spy-sma-alert-bot, Property 15: Telegram API error resilience
def test_telegram_api_error_resilience() -> None:
    async def run_test() -> None:
        bot = FakeBot()
        failing_id = 1111
        bot.fail_for.add(failing_id)

        subs = UserSubscriptionManager()
        # Subscribe three users, one will fail
        for cid in [failing_id, 2222, 3333]:
            await subs.subscribe_user(cid)

        dispatcher = AlertDispatcher(
            bot=bot,
            subscriptions=subs,
            chart_generator=ChartGenerator(),
            max_retries=2,
            retry_delay_seconds=0.0,
        )

        caption = "Test alert"
        prices = build_prices(120)

        results = await dispatcher.send_alert_to_all_subscribers(caption, prices)
        assert results[failing_id] is False
        assert results[2222] is True
        assert results[3333] is True
        # Ensure successful sends are recorded
        sent_chat_ids = [cid for cid, _, _ in bot.sent]
        assert 2222 in sent_chat_ids and 3333 in sent_chat_ids

    asyncio.run(run_test())
