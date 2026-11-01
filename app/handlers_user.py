import re
from datetime import date, datetime, time, timedelta

from aiogram import Bot, F, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message

from . import config, db, notify, slots, texts
from . import keyboards as kb

router = Router()

PHONE_RE = re.compile(r"^\+?[\d\s\-()]{9,20}$")


class BookingForm(StatesGroup):
    service = State()
    date = State()
    time = State()
    name = State()
    phone = State()
    confirm = State()


@router.message(CommandStart())
async def start(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(texts.welcome(message.from_user.first_name), reply_markup=kb.main_menu())


@router.message(Command("myid"))
async def my_id(message: Message) -> None:
    await message.answer(f"Your Telegram ID: <code>{message.from_user.id}</code>")


@router.message(F.text == texts.BTN_SERVICES)
async def show_services(message: Message) -> None:
    await message.answer(texts.services_list())


@router.message(F.text == texts.BTN_CONTACTS)
async def show_contacts(message: Message) -> None:
    await message.answer(texts.contacts())


# --- Booking flow ---

@router.message(F.text == texts.BTN_BOOK)
@router.message(Command("book"))
async def book(message: Message, state: FSMContext) -> None:
    await state.clear()
    await state.set_state(BookingForm.service)
    await message.answer(texts.choose_service(""), reply_markup=kb.services())


async def _show_dates(call: CallbackQuery, state: FSMContext) -> None:
    days = await slots.available_days()
    if not days:
        await state.clear()
        await call.message.edit_text(texts.no_days())
        return
    await state.set_state(BookingForm.date)
    await call.message.edit_text(texts.CHOOSE_DATE, reply_markup=kb.dates(days))


@router.callback_query(BookingForm.service, kb.ServiceCb.filter())
async def service_toggled(call: CallbackQuery, callback_data: kb.ServiceCb, state: FSMContext) -> None:
    if callback_data.id not in config.SERVICES:
        await call.answer(texts.EXPIRED, show_alert=True)
        return
    selected = [i for i in (await state.get_data()).get("service_id", "").split(",") if i]
    if callback_data.id in selected:
        selected.remove(callback_data.id)
    else:
        selected.append(callback_data.id)
    # Keep the order of the price list, not the order of taps
    service_ids = ",".join(i for i in config.SERVICES if i in selected)
    await state.update_data(service_id=service_ids)
    await call.message.edit_text(texts.choose_service(service_ids), reply_markup=kb.services(service_ids))
    await call.answer()


@router.callback_query(BookingForm.service, kb.NavCb.filter(F.to == "next"))
async def services_done(call: CallbackQuery, state: FSMContext) -> None:
    chosen = config.combine((await state.get_data()).get("service_id", ""))
    if not chosen.id:
        await call.answer(texts.PICK_SERVICE, show_alert=True)
        return
    if chosen.minutes > config.SLOT_MINUTES:
        await call.answer(texts.too_long(chosen.minutes), show_alert=True)
        return
    await _show_dates(call, state)
    await call.answer()


@router.callback_query(BookingForm.date, kb.DateCb.filter())
async def date_chosen(call: CallbackQuery, callback_data: kb.DateCb, state: FSMContext) -> None:
    day = date.fromisoformat(callback_data.d)
    free = await slots.free_slots(day)
    if not free:
        await call.answer(texts.NO_SLOTS, show_alert=True)
        return
    await state.update_data(day=callback_data.d)
    await state.set_state(BookingForm.time)
    await call.message.edit_text(texts.choose_time(day), reply_markup=kb.times(free))
    await call.answer()


@router.callback_query(BookingForm.time, kb.TimeCb.filter())
async def time_chosen(call: CallbackQuery, callback_data: kb.TimeCb, state: FSMContext) -> None:
    data = await state.get_data()
    t = callback_data.t
    start_at = datetime.combine(date.fromisoformat(data["day"]), time(int(t[:2]), int(t[2:])))
    await state.update_data(start_at=start_at.strftime(db.FMT))
    await state.set_state(BookingForm.name)
    service = config.combine(data["service_id"])
    await call.message.edit_text(f"💈 {service.title}\n🗓 {texts.fmt_dt(start_at)}")
    await call.message.answer(texts.ASK_NAME)
    await call.answer()


@router.callback_query(kb.NavCb.filter(F.to == "services"))
async def back_to_services(call: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(BookingForm.service)
    service_ids = (await state.get_data()).get("service_id", "")
    await call.message.edit_text(texts.choose_service(service_ids), reply_markup=kb.services(service_ids))
    await call.answer()


@router.callback_query(kb.NavCb.filter(F.to == "dates"))
async def back_to_dates(call: CallbackQuery, state: FSMContext) -> None:
    if "service_id" not in await state.get_data():
        await call.answer(texts.EXPIRED, show_alert=True)
        return
    await _show_dates(call, state)
    await call.answer()


@router.callback_query(kb.NavCb.filter(F.to == "cancel"))
async def cancel_flow(call: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await call.message.edit_text(texts.FLOW_CANCELLED)
    await call.answer()


@router.message(BookingForm.name, F.text)
async def name_entered(message: Message, state: FSMContext) -> None:
    name = message.text.strip()
    if not 2 <= len(name) <= 50:
        await message.answer(texts.BAD_NAME)
        return
    await state.update_data(name=name)
    await state.set_state(BookingForm.phone)
    await message.answer(texts.ASK_PHONE, reply_markup=kb.phone())


async def _ask_confirm(message: Message, state: FSMContext, phone: str) -> None:
    await state.update_data(phone=phone)
    await state.set_state(BookingForm.confirm)
    data = await state.get_data()
    start_at = datetime.strptime(data["start_at"], db.FMT)
    await message.answer(texts.ALMOST_DONE, reply_markup=kb.main_menu())
    await message.answer(
        texts.summary(config.combine(data["service_id"]), start_at, data["name"], phone),
        reply_markup=kb.confirm(),
    )


@router.message(BookingForm.phone, F.contact)
async def phone_shared(message: Message, state: FSMContext) -> None:
    phone = message.contact.phone_number
    await _ask_confirm(message, state, phone if phone.startswith("+") else "+" + phone)


@router.message(BookingForm.phone, F.text)
async def phone_typed(message: Message, state: FSMContext) -> None:
    phone = message.text.strip()
    if not PHONE_RE.match(phone):
        await message.answer(texts.BAD_PHONE)
        return
    await _ask_confirm(message, state, phone)


@router.callback_query(BookingForm.confirm, kb.ConfirmCb.filter(F.action == "no"))
async def confirm_no(call: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await call.message.edit_text(texts.FLOW_CANCELLED)
    await call.answer()


@router.callback_query(BookingForm.confirm, kb.ConfirmCb.filter(F.action == "yes"))
async def confirm_yes(call: CallbackQuery, state: FSMContext, bot: Bot) -> None:
    data = await state.get_data()
    start_at = datetime.strptime(data["start_at"], db.FMT)
    now = slots.now()
    booking_id = None
    if start_at >= now:
        # A booking made shortly before the visit doesn't need a separate reminder
        soon = start_at - now <= timedelta(hours=config.REMIND_BEFORE_HOURS)
        booking_id = await db.add_booking(
            call.from_user.id, call.from_user.username, data["name"], data["phone"],
            data["service_id"], start_at, reminded=soon,
        )
    if booking_id is None:
        days = await slots.available_days()
        await state.set_state(BookingForm.date)
        await call.message.edit_text(texts.SLOT_TAKEN, reply_markup=kb.dates(days))
        await call.answer()
        return

    await state.clear()
    booking = await db.get(booking_id)
    await call.message.edit_text(texts.booked(booking))
    await call.answer()
    await notify.admins(bot, texts.admin_new(booking))


# --- My bookings ---

@router.message(F.text == texts.BTN_MY)
@router.message(Command("my"))
async def my_bookings(message: Message) -> None:
    bookings = await db.user_bookings(message.from_user.id, slots.now())
    if not bookings:
        await message.answer(texts.NO_BOOKINGS)
        return
    await message.answer(texts.my_bookings(bookings), reply_markup=kb.user_bookings(bookings))


@router.callback_query(kb.CancelCb.filter())
async def cancel_booking(call: CallbackQuery, callback_data: kb.CancelCb, bot: Bot) -> None:
    booking = await db.get(callback_data.id)
    if not booking or booking.user_id != call.from_user.id or not await db.cancel(booking.id):
        await call.answer(texts.NOT_FOUND, show_alert=True)
        return
    await call.answer(texts.cancelled_by_user(booking), show_alert=True)
    bookings = await db.user_bookings(call.from_user.id, slots.now())
    if bookings:
        await call.message.edit_text(texts.my_bookings(bookings), reply_markup=kb.user_bookings(bookings))
    else:
        await call.message.edit_text(texts.NO_BOOKINGS)
    await notify.admins(bot, texts.admin_cancelled(booking))


@router.callback_query()
async def stale_button(call: CallbackQuery) -> None:
    await call.answer(texts.EXPIRED, show_alert=True)
