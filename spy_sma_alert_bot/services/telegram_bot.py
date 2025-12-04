from io import BytesIO
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
        await self._subscriptions.subscribe_user(chat.id)
        await context.bot.send_message(
            chat_id=chat.id, text=self._formatter.format_subscribe_confirmation()
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

        subscribed = await self._subscriptions.is_subscribed(chat.id)
        current_price = self._price_service.fetch_current_price()
        prices = self._price_service.fetch_historical_prices(100)
        closes = [p.close for p in prices]
        smas = SMACalculator.calculate_all_smas(closes)

        caption = self._formatter.format_status_message(
            subscribed=subscribed, current_price=current_price, smas=smas
        )
        img_bytes = self._chart_generator.generate_chart(prices)
        await context.bot.send_photo(
            chat_id=chat.id, photo=BytesIO(img_bytes), caption=caption
        )


__all__ = ["TelegramBot"]
