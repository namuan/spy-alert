import asyncio
import contextlib
import logging
import signal
import sys

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
    load_dotenv()
    try:
        config = load_config()
    except Exception as e:  # noqa: BLE001
        # Use basic print since logging is not configured yet
        print(f"Error loading config: {e}", file=sys.stderr)  # noqa: T201
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

    await app.initialize()
    await app.start()
    if app.updater is None:
        raise RuntimeError("Updater is None")

    await app.updater.start_polling()

    dispatcher = AlertDispatcher(app.bot, subscriptions, chart_generator)
    monitoring = MonitoringService(price_service, dispatcher, formatter)

    interval_minutes = max(1, min(15, config.monitoring_interval))
    monitor_task = asyncio.create_task(monitoring.start_monitoring(interval_minutes))

    stop_event = asyncio.Event()
    loop = asyncio.get_running_loop()
    try:
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(sig, stop_event.set)
    except NotImplementedError:
        pass

    await stop_event.wait()

    monitor_task.cancel()
    with contextlib.suppress(asyncio.CancelledError):
        await monitor_task

    await app.updater.stop()
    await app.stop()
    await app.shutdown()


def main() -> None:
    asyncio.run(_run())


if __name__ == "__main__":
    main()
