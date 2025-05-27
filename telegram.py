#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Version: 4.0.20241208

import asyncio
import logging
from telegram import Bot
from telegram.error import RetryAfter

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)


class BotTelegramSender:
    def __init__(self, bot_token, group_chat_ids):
        self.bot = Bot(token=bot_token)
        self.group_chat_ids = group_chat_ids

    async def send_message(self, message):
        """Send a message to all group chats."""
        for group_chat_id in self.group_chat_ids:
            await self._attempt_send_message(group_chat_id, message)

    async def _attempt_send_message(self, group_chat_id, message):
        """Attempt to send a message to a single chat ID."""
        while True:
            try:
                logger.info(f"Sending message to {group_chat_id}: {message}")
                await self.bot.send_message(chat_id=group_chat_id, text=message, parse_mode="Markdown")
                break  # Exit loop after successful send
            except RetryAfter as e:
                retry_in = e.retry_after  # Time to wait in seconds
                logger.error(f"Flood control exceeded for chat {group_chat_id}. Retrying in {retry_in} seconds.")
                await asyncio.sleep(retry_in)


async def send_messages_with_bot(bot_token, group_chat_ids, messages):
    """Send a list of messages using the bot."""
    bot_sender = BotTelegramSender(bot_token, group_chat_ids)

    for message in messages:
        await bot_sender.send_message(message)
        await asyncio.sleep(1)  # Add delay between messages to prevent flood control

