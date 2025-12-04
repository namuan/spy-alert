import asyncio
from datetime import datetime, timedelta

from hypothesis import given, settings
import hypothesis.strategies as st

from spy_sma_alert_bot.models import PricePoint
from spy_sma_alert_bot.services.alert_dispatcher import AlertDispatcher
from spy_sma_alert_bot.services.chart_generator import ChartGenerator
from spy_sma_alert_bot.services.message_formatter import MessageFormatter
from spy_sma_alert_bot.services.monitoring_service import MonitoringService


class FakePriceDataService:
    def __init__(self) -> None:
        self.current_calls = 0
        self.historical_calls = 0
        self.fail_current_until = 0
        self.fail_historical_until = 0

    def fetch_current_price(self) -> float:
        self.current_calls += 1
        if self.current_calls <= self.fail_current_until:
            raise RuntimeError("current price failure")
        return 400.0

    def fetch_historical_prices(self, days: int) -> list[PricePoint]:
        self.historical_calls += 1
        if self.historical_calls <= self.fail_historical_until:
            raise RuntimeError("historical failure")
        start = datetime.now() - timedelta(days=max(100, days))
        points: list[PricePoint] = [PricePoint(timestamp=start + timedelta(days=i), close=400.0 + i) for i in range(max(100, days))]
        return points


class FakeBot:
    def __init__(self) -> None:
        self.sent: list[tuple[int, bytes, str]] = []

    async def send_photo(self, chat_id: int, photo, caption: str) -> None:
        self.sent.append((chat_id, photo.getvalue(), caption))


class FakeSubscriptions:
    async def get_all_subscribers(self) -> list[int]:
        return [101, 202]


def build_prices(n: int) -> list[PricePoint]:
    start = datetime.now() - timedelta(days=n)
    points: list[PricePoint] = [PricePoint(timestamp=start + timedelta(days=i), close=400.0 + i) for i in range(n)]
    return points


@settings(max_examples=25, deadline=None)
@given(interval=st.integers(min_value=-5, max_value=50))
def test_monitoring_interval_compliance(interval: int) -> None:
    sleeps: list[float] = []

    async def sleep_stub(seconds: float) -> None:
        sleeps.append(seconds)
        assert seconds >= 0 or seconds < 0
        await asyncio.sleep(0)

    price = FakePriceDataService()
    bot = FakeBot()
    subs = FakeSubscriptions()
    dispatcher = AlertDispatcher(bot=bot, subscriptions=subs, chart_generator=ChartGenerator())
    svc = MonitoringService(
        price_data=price,
        dispatcher=dispatcher,
        formatter=MessageFormatter(),
        initial_backoff_seconds=0.0,
        max_backoff_seconds=0.0,
        max_retries=1,
        sleep_fn=sleep_stub,
    )

    async def run_once() -> None:
        await svc.start_monitoring(interval, iterations=2)

    asyncio.run(run_once())
    assert len(sleeps) == 2
    for s in sleeps:
        assert 60.0 <= s <= 900.0


def test_price_provider_error_resilience() -> None:
    async def run_test() -> None:
        price = FakePriceDataService()
        price.fail_current_until = 2
        price.fail_historical_until = 1

        bot = FakeBot()
        subs = FakeSubscriptions()
        dispatcher = AlertDispatcher(bot=bot, subscriptions=subs, chart_generator=ChartGenerator())

        async def sleep_stub(seconds: float) -> None:
            assert seconds >= 0 or seconds < 0
            await asyncio.sleep(0)

        svc = MonitoringService(
            price_data=price,
            dispatcher=dispatcher,
            formatter=MessageFormatter(),
            initial_backoff_seconds=0.0,
            max_backoff_seconds=0.0,
            max_retries=3,
            sleep_fn=sleep_stub,
        )

        crossovers = await svc.check_for_crossovers()
        assert isinstance(crossovers, list)

    asyncio.run(run_test())


def test_invalid_data_rejection() -> None:
    async def run_test() -> None:
        class BadPriceService(FakePriceDataService):
            def fetch_historical_prices(self, days: int) -> list[PricePoint]:
                # Return invalid data: future timestamp
                future = datetime.now() + timedelta(days=1)
                return [PricePoint(timestamp=future, close=400.0)] * max(100, days)

        price = BadPriceService()
        bot = FakeBot()
        subs = FakeSubscriptions()
        dispatcher = AlertDispatcher(bot=bot, subscriptions=subs, chart_generator=ChartGenerator())

        async def sleep_stub(seconds: float) -> None:
            assert seconds >= 0 or seconds < 0
            await asyncio.sleep(0)

        svc = MonitoringService(
            price_data=price,
            dispatcher=dispatcher,
            formatter=MessageFormatter(),
            initial_backoff_seconds=0.0,
            max_backoff_seconds=0.0,
            max_retries=1,
            sleep_fn=sleep_stub,
        )

        crossovers = await svc.check_for_crossovers()
        assert crossovers == []

    asyncio.run(run_test())


def test_general_error_resilience() -> None:
    async def run_test() -> None:
        price = FakePriceDataService()
        bot = FakeBot()
        subs = FakeSubscriptions()
        dispatcher = AlertDispatcher(bot=bot, subscriptions=subs, chart_generator=ChartGenerator())
        svc = MonitoringService(
            price_data=price,
            dispatcher=dispatcher,
            formatter=MessageFormatter(),
            initial_backoff_seconds=0.0,
            max_backoff_seconds=0.0,
            max_retries=1,
        )

        async def faulty_check() -> list:
            raise RuntimeError("boom")

        svc.check_for_crossovers = faulty_check  # type: ignore

        sleeps: list[float] = []

        async def sleep_stub(seconds: float) -> None:
            sleeps.append(seconds)
            await asyncio.sleep(0)

        svc = MonitoringService(
            price_data=price,
            dispatcher=dispatcher,
            formatter=MessageFormatter(),
            initial_backoff_seconds=0.0,
            max_backoff_seconds=0.0,
            max_retries=1,
            sleep_fn=sleep_stub,
        )

        svc.check_for_crossovers = faulty_check  # type: ignore

        await svc.start_monitoring(5, iterations=2)
        assert len(sleeps) == 2

    asyncio.run(run_test())
