import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand

from app import config, db, handlers_admin, handlers_user, reminders


async def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    if not config.BOT_TOKEN:
        raise SystemExit("BOT_TOKEN is not set. Copy .env.example to .env and fill it in.")

    await db.init()
    bot = Bot(config.BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher(storage=MemoryStorage())
    # Admin router first: the user router ends with a catch-all for stale buttons
    dp.include_routers(handlers_admin.router, handlers_user.router)

    await bot.set_my_commands([
        BotCommand(command="start", description="Main menu"),
        BotCommand(command="book", description="Book an appointment"),
        BotCommand(command="my", description="My bookings"),
    ])
    reminder_task = asyncio.create_task(reminders.reminder_loop(bot))
    try:
        await dp.start_polling(bot)
    finally:
        reminder_task.cancel()


if __name__ == "__main__":
    asyncio.run(main())
