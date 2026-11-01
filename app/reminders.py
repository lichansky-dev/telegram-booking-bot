import asyncio
import logging
from datetime import timedelta

from aiogram import Bot
from aiogram.exceptions import TelegramAPIError

from . import config, db, slots, texts


async def reminder_loop(bot: Bot) -> None:
    while True:
        try:
            now = slots.now()
            due = await db.due_reminders(now, now + timedelta(hours=config.REMIND_BEFORE_HOURS))
            for booking in due:
                try:
                    await bot.send_message(booking.user_id, texts.reminder(booking))
                except TelegramAPIError:
                    logging.warning("Could not remind user %s", booking.user_id)
                await db.mark_reminded(booking.id)
        except Exception:
            logging.exception("Reminder loop failed")
        await asyncio.sleep(60)
