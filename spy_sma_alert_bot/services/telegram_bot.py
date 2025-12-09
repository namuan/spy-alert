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
        print("DEBUG: Entered handle_start")
        chat = update.effective_chat
        if chat is None:
            print("DEBUG: chat is None")
            return
        
        try:
            print(f"DEBUG: Subscribing user {chat.id}")
            await self._subscriptions.subscribe_user(chat.id)
            print("DEBUG: User subscribed. Sending confirmation message.")
            await context.bot.send_message(
                chat_id=chat.id, text=self._formatter.format_subscribe_confirmation()
            )
            print("DEBUG: Confirmation sent. Calling _send_status_chart.")
            await self._send_status_chart(chat.id, context)
            print("DEBUG: _send_status_chart completed.")
        except Exception as e:
            import traceback
            # Log the error (in a real app, use logging)
            print(f"Error in handle_start: {e}")
            traceback.print_exc()
            try:
                await context.bot.send_message(
                    chat_id=chat.id, 
                    text="An error occurred while starting the bot. Please try again later."
                )
            except Exception as send_err:
                print(f"Error sending error message: {send_err}")

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
        print("DEBUG: Entered handle_status")
        chat = update.effective_chat
        if chat is None:
            return
        try:
            await self._send_status_chart(chat.id, context)
        except Exception as e:
            import traceback
            print(f"Error in handle_status: {e}")
            traceback.print_exc()
            await context.bot.send_message(
                chat_id=chat.id,
                text="Unable to retrieve status at this time."
            )

    async def _send_status_chart(
        self, chat_id: int, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        print(f"DEBUG: Entered _send_status_chart for {chat_id}")
        import asyncio
        
        subscribed = await self._subscriptions.is_subscribed(chat_id)
        
        # Run blocking operations in a separate thread
        print("DEBUG: Fetching current price (async)")
        current_price = await asyncio.to_thread(self._price_service.fetch_current_price)
        print(f"DEBUG: Current price fetched: {current_price}")
        
        print("DEBUG: Fetching historical prices (async)")
        prices = await asyncio.to_thread(self._price_service.fetch_historical_prices, 100)
        print(f"DEBUG: Historical prices fetched: {len(prices)} points")
        
        closes = [p.close for p in prices]
        print("DEBUG: Calculating SMAs")
        smas = SMACalculator.calculate_all_smas(closes)
        print("DEBUG: SMAs calculated")

        caption = self._formatter.format_status_message(
            subscribed=subscribed, current_price=current_price, smas=smas
        )
        print("DEBUG: Generating chart")
        img_bytes = self._chart_generator.generate_chart(prices)
        print(f"DEBUG: Chart generated ({len(img_bytes)} bytes)")
        
        print("DEBUG: Sending photo")
        await context.bot.send_photo(
            chat_id=chat_id, photo=BytesIO(img_bytes), caption=caption
        )
        print("DEBUG: Photo sent")


__all__ = ["TelegramBot"]
