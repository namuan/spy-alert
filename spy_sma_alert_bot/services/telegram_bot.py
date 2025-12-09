import asyncio
import contextlib
from io import BytesIO
import logging
from typing import Final

from telegram import Update
from telegram.ext import Application, ApplicationBuilder, CommandHandler, ContextTypes

from .chart_generator import ChartGenerator
from .message_formatter import MessageFormatter
from .price_data import PriceDataService
from .sma_calculator import SMACalculator
from .user_subscription_manager import UserSubscriptionManager


class TelegramBot:
    def __init__(
        self,
        token: str,
        subscriptions: UserSubscriptionManager,
        formatter: MessageFormatter,
        price_service: PriceDataService,
        chart_generator: ChartGenerator,
    ) -> None:
        self._token: Final[str] = token
        self._subscriptions = subscriptions
        self._formatter = formatter
        self._price_service = price_service
        self._chart_generator = chart_generator
        self._logger = logging.getLogger(__name__)

    def build_application(self) -> Application:
        app = ApplicationBuilder().token(self._token).build()
        app.add_handler(CommandHandler("start", self.handle_start))
        app.add_handler(CommandHandler("stop", self.handle_stop))
        app.add_handler(CommandHandler("status", self.handle_status))
        return app

    async def handle_start(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        chat = update.effective_chat
        if chat is None:
            return

        try:
            await self._subscriptions.subscribe_user(chat.id)
            await context.bot.send_message(
                chat_id=chat.id, text=self._formatter.format_subscribe_confirmation()
            )
            await self._send_status_chart(chat.id, context)
        except Exception:
            self._logger.error("Error in handle_start", exc_info=True)
            with contextlib.suppress(Exception):
                await context.bot.send_message(
                    chat_id=chat.id,
                    text="An error occurred while starting the bot. Please try again later.",
                )

    async def handle_stop(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        chat = update.effective_chat
        if chat is None:
            return
        await self._subscriptions.unsubscribe_user(chat.id)
        await context.bot.send_message(
            chat_id=chat.id, text=self._formatter.format_unsubscribe_confirmation()
        )

    async def handle_status(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        chat = update.effective_chat
        if chat is None:
            return
        try:
            await self._send_status_chart(chat.id, context)
        except Exception:
            self._logger.error("Error in handle_status", exc_info=True)
            await context.bot.send_message(
                chat_id=chat.id, text="Unable to retrieve status at this time."
            )

    async def _send_status_chart(
        self, chat_id: int, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        subscribed = await self._subscriptions.is_subscribed(chat_id)

        # Run blocking operations in a separate thread
        current_price = await asyncio.to_thread(self._price_service.fetch_current_price)

        prices = await asyncio.to_thread(
            self._price_service.fetch_historical_prices, 100
        )

        closes = [p.close for p in prices]
        smas = SMACalculator.calculate_all_smas(closes)

        caption = self._formatter.format_status_message(
            subscribed=subscribed, current_price=current_price, smas=smas
        )
        img_bytes = self._chart_generator.generate_chart(prices)

        await context.bot.send_photo(
            chat_id=chat_id, photo=BytesIO(img_bytes), caption=caption
        )


__all__ = ["TelegramBot"]
