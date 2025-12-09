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
        self.sent_photos: list[tuple[int, bytes, str]] = []
        self.sent_messages: list[tuple[int, str]] = []

    async def send_photo(self, chat_id: int, photo: io.BytesIO, caption: str) -> None:
        self.sent_photos.append((chat_id, photo.getvalue(), caption))

    async def send_message(self, chat_id: int, text: str) -> None:
        self.sent_messages.append((chat_id, text))


@dataclass
class FakeContext:
    bot: FakeBot


@dataclass
class FakeChat:
    id: int


class FakeUpdate:
    def __init__(self, chat_id: int) -> None:
        self.effective_chat = FakeChat(chat_id)


@settings(max_examples=20, deadline=None)
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
def test_start_command_sends_chart_and_price(
    current_price: float, prices: list[PricePoint]
) -> None:
    async def run_test() -> None:
        subs = UserSubscriptionManager()

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
        update = FakeUpdate(9999)

        # Ensure user is not subscribed initially
        assert not await subs.is_subscribed(9999)

        await bot.handle_start(update, context)  # type: ignore[arg-type]

        # Check subscription
        assert await subs.is_subscribed(9999)

        # Check messages
        assert len(fake_bot.sent_messages) == 1
        assert fake_bot.sent_messages[0][0] == 9999
        assert "subscribed" in fake_bot.sent_messages[0][1].lower()

        # Check chart/status
        assert len(fake_bot.sent_photos) == 1
        chat_id, photo_bytes, caption = fake_bot.sent_photos[0]
        assert chat_id == 9999
        assert photo_bytes.startswith(b"\x89PNG")
        assert f"${current_price:.2f}" in caption
        assert "SMA 25:" in caption
        assert "SMA 50:" in caption
        assert "SMA 75:" in caption
        assert "SMA 100:" in caption
        assert "Status: Subscribed" in caption

    asyncio.run(run_test())
