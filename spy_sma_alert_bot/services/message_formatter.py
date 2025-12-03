from datetime import datetime
from typing import Literal


class MessageFormatter:
    @staticmethod
    def format_crossover_message(
        direction: Literal["above", "below"],
        sma_period: int,
        price: float,
        sma_value: float,
        timestamp: datetime,
    ) -> str:
        dir_text = "above" if direction == "above" else "below"
        ts = timestamp.strftime("%Y-%m-%d %H:%M:%S")
        return (
            f"SPY crossed {dir_text} the {sma_period}-day SMA "
            f"at {ts}. Price: ${price:.2f}, SMA {sma_period}: ${sma_value:.2f}"
        )

    @staticmethod
    def format_status_message(
        subscribed: bool,
        current_price: float,
        smas: dict[int, float | None],
    ) -> str:
        status = "Subscribed" if subscribed else "Unsubscribed"
        parts: list[str] = [f"Status: {status}", f"Current SPY Price: ${current_price:.2f}"]
        for period in [25, 50, 75, 100]:
            val = smas.get(period)
            val_text = f"${val:.2f}" if isinstance(val, float) else "N/A"
            parts.append(f"SMA {period}: {val_text}")
        return "; ".join(parts)

    @staticmethod
    def format_subscribe_confirmation() -> str:
        return "You are now subscribed to SPY SMA alerts."

    @staticmethod
    def format_unsubscribe_confirmation() -> str:
        return "You have unsubscribed from SPY SMA alerts."

