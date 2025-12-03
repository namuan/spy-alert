"""User subscription management for the SPY SMA Alert Bot.

This module provides functionality to manage user subscriptions for receiving
Telegram alerts when SPY price crosses above or below key Simple Moving Averages.
"""

import asyncio
import logging

logger = logging.getLogger(__name__)


class UserSubscriptionManager:
    """Manages user subscriptions for the SPY SMA Alert Bot.

    This class provides thread-safe operations for subscribing and unsubscribing
    users, checking subscription status, and retrieving all subscribers.
    It uses asyncio.Lock to ensure thread safety in concurrent environments.

    Attributes:
        _subscribers (Set[int]): Set of subscribed user chat IDs
        _lock (asyncio.Lock): Lock for thread-safe operations
    """

    def __init__(self) -> None:
        """Initialize the UserSubscriptionManager with empty subscriber set."""
        self._subscribers: set[int] = set()
        self._lock = asyncio.Lock()

    async def subscribe_user(self, chat_id: int) -> bool:
        """Subscribe a user to receive alerts.

        Args:
            chat_id: The Telegram chat ID of the user to subscribe

        Returns:
            bool: True if user was successfully subscribed, False if already subscribed

        Raises:
            ValueError: If chat_id is not a positive integer
        """
        if not isinstance(chat_id, int) or chat_id <= 0:
            raise ValueError(f"Invalid chat_id: {chat_id}. Must be a positive integer.")

        async with self._lock:
            if chat_id in self._subscribers:
                logger.debug(f"User {chat_id} is already subscribed")
                return False

            self._subscribers.add(chat_id)
            logger.info(f"User {chat_id} subscribed to alerts")
            return True

    async def unsubscribe_user(self, chat_id: int) -> bool:
        """Unsubscribe a user from receiving alerts.

        Args:
            chat_id: The Telegram chat ID of the user to unsubscribe

        Returns:
            bool: True if user was successfully unsubscribed, False if not subscribed

        Raises:
            ValueError: If chat_id is not a positive integer
        """
        if not isinstance(chat_id, int) or chat_id <= 0:
            raise ValueError(f"Invalid chat_id: {chat_id}. Must be a positive integer.")

        async with self._lock:
            if chat_id not in self._subscribers:
                logger.debug(f"User {chat_id} is not subscribed")
                return False

            self._subscribers.remove(chat_id)
            logger.info(f"User {chat_id} unsubscribed from alerts")
            return True

    async def is_subscribed(self, chat_id: int) -> bool:
        """Check if a user is subscribed to receive alerts.

        Args:
            chat_id: The Telegram chat ID to check

        Returns:
            bool: True if user is subscribed, False otherwise

        Raises:
            ValueError: If chat_id is not a positive integer
        """
        if not isinstance(chat_id, int) or chat_id <= 0:
            raise ValueError(f"Invalid chat_id: {chat_id}. Must be a positive integer.")

        async with self._lock:
            return chat_id in self._subscribers

    async def get_all_subscribers(self) -> list[int]:
        """Get a list of all subscribed user chat IDs.

        Returns:
            List[int]: List of all subscribed chat IDs
        """
        async with self._lock:
            return list(self._subscribers)

    async def get_subscriber_count(self) -> int:
        """Get the total number of subscribed users.

        Returns:
            int: Number of subscribed users
        """
        async with self._lock:
            return len(self._subscribers)

    async def clear_subscriptions(self) -> None:
        """Clear all subscriptions (useful for testing or emergency scenarios).

        This method removes all subscribers from the system.
        """
        async with self._lock:
            if self._subscribers:
                logger.warning(f"Clearing {len(self._subscribers)} subscriptions")
                self._subscribers.clear()
            else:
                logger.debug("No subscriptions to clear")
