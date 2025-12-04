import asyncio
from collections.abc import Callable
from datetime import datetime
import logging

from spy_sma_alert_bot.models import Crossover, PricePoint

from .alert_dispatcher import AlertDispatcher
from .crossover_detector import CrossoverDetector
from .message_formatter import MessageFormatter
from .price_data import PriceDataService
from .sma_calculator import SMACalculator

logger = logging.getLogger(__name__)


class MonitoringService:
    def __init__(
        self,
        price_data: PriceDataService,
        dispatcher: AlertDispatcher,
        formatter: MessageFormatter,
        *,
        initial_backoff_seconds: float = 30.0,
        max_backoff_seconds: float = 300.0,
        max_retries: int = 5,
        sleep_fn: Callable[[float], object] | None = None,
    ) -> None:
        self._price_data = price_data
        self._dispatcher = dispatcher
        self._formatter = formatter
        self._previous_states: dict[int, str] = {}
        self._last_prices: list[PricePoint] = []
        self._initial_backoff_seconds = initial_backoff_seconds
        self._max_backoff_seconds = max_backoff_seconds
        self._max_retries = max_retries
        self._sleep = sleep_fn or asyncio.sleep

    async def _fetch_current_price_with_backoff(self) -> float:
        delay = self._initial_backoff_seconds
        for attempt in range(1, self._max_retries + 1):
            try:
                return self._price_data.fetch_current_price()
            except Exception as e:
                logger.warning(
                    f"Price provider error fetching current price (attempt {attempt}/{self._max_retries}): {e}"
                )
                if attempt == self._max_retries:
                    raise
                delay = min(delay * 2, self._max_backoff_seconds)
                await self._sleep(delay)

        raise RuntimeError("Failed to fetch current price after retries")

    async def _fetch_historical_with_backoff(self, days: int) -> list[PricePoint]:
        delay = self._initial_backoff_seconds
        for attempt in range(1, self._max_retries + 1):
            try:
                return self._price_data.fetch_historical_prices(days)
            except Exception as e:
                logger.warning(
                    f"Price provider error fetching historical prices (attempt {attempt}/{self._max_retries}): {e}"
                )
                if attempt == self._max_retries:
                    raise
                delay = min(delay * 2, self._max_backoff_seconds)
                await self._sleep(delay)

        raise RuntimeError("Failed to fetch historical prices after retries")

    async def check_for_crossovers(self) -> list[Crossover]:
        try:
            current_price = await self._fetch_current_price_with_backoff()
            prices = await self._fetch_historical_with_backoff(100)
        except Exception as e:
            logger.error(f"Error fetching price data: {e}")
            return []

        if not PriceDataService.validate_price_data(prices):
            logger.warning("Invalid or incomplete price data received; skipping check")
            return []

        closes = [p.close for p in prices]
        smas_all = SMACalculator.calculate_all_smas(closes)
        smas: dict[int, float] = {
            period: val for period, val in smas_all.items() if isinstance(val, float)
        }

        crossovers = CrossoverDetector.detect_crossovers(
            current_price, smas, self._previous_states
        )

        self._previous_states = CrossoverDetector.update_crossover_state(
            smas, current_price
        )
        self._last_prices = prices

        if crossovers:
            logger.info(f"Detected {len(crossovers)} crossover(s)")

        return crossovers

    async def process_crossovers(self, crossovers: list[Crossover]) -> dict[int, bool]:
        if not crossovers:
            return {}

        results: dict[int, bool] = {}
        prices = self._last_prices or await self._fetch_historical_with_backoff(100)

        for co in crossovers:
            caption = self._formatter.format_crossover_message(
                direction=co.direction,
                sma_period=co.sma_period,
                price=co.price,
                sma_value=co.sma_value,
                timestamp=datetime.now(),
            )
            try:
                dispatch_results = await self._dispatcher.send_alert_to_all_subscribers(
                    caption, prices
                )
                results.update(dict(dispatch_results.items()))
            except Exception as e:
                logger.error(f"Error dispatching alerts: {e}")

        return results

    async def start_monitoring(
        self, interval_minutes: int, *, iterations: int | None = None
    ) -> None:
        interval_minutes = max(1, min(15, interval_minutes))
        i = 0
        while iterations is None or i < iterations:
            try:
                crossovers = await self.check_for_crossovers()
                await self.process_crossovers(crossovers)
            except Exception as e:
                logger.error(f"Unexpected error during monitoring: {e}")
            finally:
                i += 1
                await self._sleep(interval_minutes * 60)


__all__ = ["MonitoringService"]
