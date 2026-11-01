import logging

from aiogram import Bot
from aiogram.exceptions import TelegramAPIError

from . import config


async def admins(bot: Bot, text: str) -> None:
    for admin_id in config.ADMIN_IDS:
        try:
            await bot.send_message(admin_id, text)
        except TelegramAPIError:
            logging.exception("Failed to notify admin %s", admin_id)
