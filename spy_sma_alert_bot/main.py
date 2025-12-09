import asyncio
import contextlib
import logging
import signal

from dotenv import load_dotenv

from spy_sma_alert_bot.config import load_config
from spy_sma_alert_bot.services.alert_dispatcher import AlertDispatcher
from spy_sma_alert_bot.services.chart_generator import ChartGenerator
from spy_sma_alert_bot.services.message_formatter import MessageFormatter
from spy_sma_alert_bot.services.monitoring_service import MonitoringService
from spy_sma_alert_bot.services.price_data import PriceDataService
from spy_sma_alert_bot.services.telegram_bot import TelegramBot
from spy_sma_alert_bot.services.user_subscription_manager import (
    UserSubscriptionManager,
)


async def _run() -> None:
    print("DEBUG: Starting main application...")
    load_dotenv()
    try:
        config = load_config()
        print("DEBUG: Config loaded successfully")
    except Exception as e:
        print(f"CRITICAL ERROR: Failed to load config: {e}")
        return

    logging.basicConfig(level=logging.DEBUG if config.debug else logging.INFO)

    subscriptions = UserSubscriptionManager()
    formatter = MessageFormatter()
    price_service = PriceDataService()
    chart_generator = ChartGenerator()

    bot = TelegramBot(
        token=config.telegram_token,
        subscriptions=subscriptions,
        formatter=formatter,
        price_service=price_service,
        chart_generator=chart_generator,
    )
    app = bot.build_application()

    print("DEBUG: Initializing application...")
    await app.initialize()
    await app.start()
    if app.updater is None:
        raise RuntimeError("Updater is None")
    
    print("DEBUG: Starting polling...")
    await app.updater.start_polling()

    dispatcher = AlertDispatcher(app.bot, subscriptions, chart_generator)
    monitoring = MonitoringService(price_service, dispatcher, formatter)

    interval_minutes = max(1, min(15, config.monitoring_interval))
    print(f"DEBUG: Starting monitoring service (interval={interval_minutes}m)...")
    monitor_task = asyncio.create_task(monitoring.start_monitoring(interval_minutes))

    stop_event = asyncio.Event()
    loop = asyncio.get_running_loop()
    try:
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(sig, stop_event.set)
    except NotImplementedError:
        pass
    
    print("DEBUG: Application running. Waiting for stop signal...")
    await stop_event.wait()

    print("DEBUG: Stopping application...")
    monitor_task.cancel()
    with contextlib.suppress(asyncio.CancelledError):
        await monitor_task

    print("DEBUG: Stopping Telegram bot...")
    await app.updater.stop()
    await app.stop()
    await app.shutdown()
    print("DEBUG: Application shutdown complete.")


def main() -> None:
    asyncio.run(_run())


if __name__ == "__main__":
    main()
