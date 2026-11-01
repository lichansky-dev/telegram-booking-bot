from datetime import timedelta

from aiogram import Bot, Router
from aiogram.exceptions import TelegramAPIError
from aiogram.filters import BaseFilter, Command
from aiogram.types import CallbackQuery, Message, TelegramObject

from . import config, db, slots, texts
from . import keyboards as kb


class IsAdmin(BaseFilter):
    async def __call__(self, event: TelegramObject) -> bool:
        return event.from_user is not None and event.from_user.id in config.ADMIN_IDS


router = Router()
router.message.filter(IsAdmin())
router.callback_query.filter(IsAdmin())


async def _upcoming() -> list[db.Booking]:
    now = slots.now()
    return await db.upcoming(now, now + timedelta(days=config.DAYS_AHEAD))


@router.message(Command("admin"))
async def admin_panel(message: Message) -> None:
    bookings = await _upcoming()
    await message.answer(texts.admin_list(bookings), reply_markup=kb.admin_bookings(bookings))


@router.callback_query(kb.AdminCancelCb.filter())
async def admin_cancel(call: CallbackQuery, callback_data: kb.AdminCancelCb, bot: Bot) -> None:
    booking = await db.get(callback_data.id)
    if not booking or not await db.cancel(booking.id):
        await call.answer(texts.NOT_FOUND, show_alert=True)
        return
    try:
        await bot.send_message(booking.user_id, texts.cancelled_by_admin(booking))
    except TelegramAPIError:
        pass  # client blocked the bot; the booking is cancelled anyway
    await call.answer(f"Booking #{booking.id} cancelled, client notified.", show_alert=True)
    bookings = await _upcoming()
    await call.message.edit_text(texts.admin_list(bookings), reply_markup=kb.admin_bookings(bookings))
