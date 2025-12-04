import asyncio
from dataclasses import dataclass
from datetime import datetime
import io
import os

from hypothesis import given, settings
import hypothesis.strategies as st

from spy_sma_alert_bot.models import PricePoint
from spy_sma_alert_bot.services.chart_generator import ChartGenerator
from spy_sma_alert_bot.services.message_formatter import MessageFormatter
from spy_sma_alert_bot.services.telegram_bot import TelegramBot
from spy_sma_alert_bot.services.user_subscription_manager import UserSubscriptionManager


class FakePriceDataService:
    def __init__(self, current_price: float, prices: list[PricePoint]) -> None:
        self._current_price = current_price
        self._prices = prices

    def fetch_current_price(self) -> float:
        return self._current_price

    def fetch_historical_prices(self, days: int) -> list[PricePoint]:
        return sorted(self._prices, key=lambda p: p.timestamp)[-max(100, days) :]


class FakeBot:
    def __init__(self) -> None:
        self.sent: list[tuple[int, bytes, str]] = []

    async def send_photo(self, chat_id: int, photo: io.BytesIO, caption: str) -> None:
        self.sent.append((chat_id, photo.getvalue(), caption))


@dataclass
class FakeContext:
    bot: FakeBot


@dataclass
class FakeChat:
    id: int


class FakeUpdate:
    def __init__(self, chat_id: int) -> None:
        self.effective_chat = FakeChat(chat_id)


# Feature: spy-sma-alert-bot, Property 5: Status command completeness
@settings(max_examples=50, deadline=None)
@given(
    subscribed=st.booleans(),
    current_price=st.floats(
        min_value=300.0, max_value=700.0, allow_nan=False, allow_infinity=False
    ),
    prices=st.lists(
        st.builds(
            PricePoint,
            timestamp=st.datetimes(
                min_value=datetime(2024, 1, 1), max_value=datetime(2030, 1, 1)
            ),
            close=st.floats(
                min_value=300.0, max_value=700.0, allow_nan=False, allow_infinity=False
            ),
        ),
        min_size=100,
        max_size=200,
    ),
)
def test_status_command_completeness(
    subscribed: bool, current_price: float, prices: list[PricePoint]
) -> None:
    async def run_test() -> None:
        subs = UserSubscriptionManager()
        if subscribed:
            await subs.subscribe_user(1234)

        price_service = FakePriceDataService(current_price, prices)
        bot = TelegramBot(
            token=os.getenv("TEST_TELEGRAM_TOKEN", ""),
            subscriptions=subs,
            formatter=MessageFormatter(),
            price_service=price_service,
            chart_generator=ChartGenerator(),
        )

        fake_bot = FakeBot()
        context = FakeContext(fake_bot)
        update = FakeUpdate(1234)

        await bot.handle_status(update, context)  # type: ignore[arg-type]

        assert len(fake_bot.sent) == 1
        chat_id, photo_bytes, caption = fake_bot.sent[0]
        assert chat_id == 1234
        assert caption.count("SMA 25:") == 1
        assert caption.count("SMA 50:") == 1
        assert caption.count("SMA 75:") == 1
        assert caption.count("SMA 100:") == 1
        assert f"${current_price:.2f}" in caption
        assert ("Status: Subscribed" in caption) or ("Status: Unsubscribed" in caption)
        assert photo_bytes.startswith(b"\x89PNG")

    asyncio.run(run_test())


# Feature: spy-sma-alert-bot, Property 22: Chart inclusion in status response
@settings(max_examples=50, deadline=None)
@given(
    current_price=st.floats(
        min_value=300.0, max_value=700.0, allow_nan=False, allow_infinity=False
    ),
    prices=st.lists(
        st.builds(
            PricePoint,
            timestamp=st.datetimes(
                min_value=datetime(2024, 1, 1), max_value=datetime(2030, 1, 1)
            ),
            close=st.floats(
                min_value=300.0, max_value=700.0, allow_nan=False, allow_infinity=False
            ),
        ),
        min_size=100,
        max_size=200,
    ),
)
def test_chart_inclusion_in_status_response(
    current_price: float, prices: list[PricePoint]
) -> None:
    async def run_test() -> None:
        subs = UserSubscriptionManager()
        await subs.subscribe_user(5678)

        price_service = FakePriceDataService(current_price, prices)
        bot = TelegramBot(
            token=os.getenv("TEST_TELEGRAM_TOKEN", ""),
            subscriptions=subs,
            formatter=MessageFormatter(),
            price_service=price_service,
            chart_generator=ChartGenerator(),
        )

        fake_bot = FakeBot()
        context = FakeContext(fake_bot)
        update = FakeUpdate(5678)

        await bot.handle_status(update, context)  # type: ignore[arg-type]

        assert len(fake_bot.sent) == 1
        _, photo_bytes, caption = fake_bot.sent[0]
        assert photo_bytes.startswith(b"\x89PNG")
        assert len(photo_bytes) > 5000
        assert (
            "SMA 25:" in caption
            and "SMA 50:" in caption
            and "SMA 75:" in caption
            and "SMA 100:" in caption
        )

    asyncio.run(run_test())
