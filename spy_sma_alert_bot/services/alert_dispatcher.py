"""Alert dispatching for the SPY SMA Alert Bot.

This module provides the AlertDispatcher responsible for sending crossover
notifications with chart images to individual users or broadcasting to all
subscribed users. It implements error resilience and retry logic for
Telegram API operations.
"""

import asyncio
from io import BytesIO
import logging
from typing import Protocol

from spy_sma_alert_bot.models import PricePoint

from .chart_generator import ChartGenerator
from .user_subscription_manager import UserSubscriptionManager

logger = logging.getLogger(__name__)


class BotLike(Protocol):
    async def send_photo(self, chat_id: int, photo: BytesIO, caption: str) -> None: ...


class AlertDispatcher:
    """Dispatches alert messages with chart images to Telegram users.

    Responsibilities:
    - Send a single alert (caption + chart image) to a specific user
    - Broadcast alerts to all subscribed users
    - Handle Telegram API failures gracefully with retry logic
    """

    def __init__(
        self,
        bot: BotLike,
        subscriptions: UserSubscriptionManager,
        chart_generator: ChartGenerator,
        *,
        max_retries: int = 3,
        retry_delay_seconds: float = 0.1,
    ) -> None:
        self._bot = bot
        self._subscriptions = subscriptions
        self._charts = chart_generator
        self._max_retries = max_retries
        self._retry_delay_seconds = retry_delay_seconds

    async def send_alert(
        self, chat_id: int, caption: str, prices: list[PricePoint]
    ) -> bool:
        """Send an alert with chart image to a single user.

        Args:
            chat_id: Telegram chat ID of the recipient
            caption: Message caption describing the crossover
            prices: Historical prices used to generate chart (>=100 points)

        Returns:
            True if the alert was sent successfully, False otherwise.
        """
        try:
            chart_bytes = self._charts.generate_chart(prices)
        except Exception as e:  # noqa: BLE001
            logger.error(f"Failed to generate chart: {e}")
            return False

        photo = BytesIO(chart_bytes)

        for attempt in range(1, self._max_retries + 1):
            try:
                await self._bot.send_photo(
                    chat_id=chat_id, photo=photo, caption=caption
                )
                return True
            except Exception as e:  # noqa: BLE001
                logger.warning(
                    f"Telegram send_photo failed (attempt {attempt}/{self._max_retries}) for chat_id={chat_id}: {e}"
                )
                if attempt == self._max_retries:
                    logger.error(
                        f"Giving up sending alert to chat_id={chat_id} after {self._max_retries} attempts"
                    )
                    break
                # Reset buffer before retry
                photo.seek(0)
                await asyncio.sleep(self._retry_delay_seconds)

        return False

    async def send_alert_to_all_subscribers(
        self, caption: str, prices: list[PricePoint]
    ) -> dict[int, bool]:
        """Broadcast an alert with chart image to all subscribed users.

        Args:
            caption: Message caption describing the crossover
            prices: Historical prices used to generate chart (>=100 points)

        Returns:
            Mapping of chat_id to send success (True) or failure (False).
        """
        results: dict[int, bool] = {}
        chat_ids = await self._subscriptions.get_all_subscribers()

        for chat_id in chat_ids:
            ok = await self.send_alert(chat_id, caption, prices)
            results[chat_id] = ok

        return results


__all__ = ["AlertDispatcher"]
