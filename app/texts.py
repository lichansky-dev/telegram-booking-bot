from datetime import date, datetime
from html import escape

from . import config
from .db import Booking

BTN_BOOK = "📅 Book appointment"
BTN_MY = "🗂 My bookings"
BTN_SERVICES = "💈 Services & prices"
BTN_CONTACTS = "📍 Contacts"
BTN_SHARE_PHONE = "📱 Share my phone number"
BTN_BACK = "⬅️ Back"
BTN_CANCEL = "✖️ Cancel"
BTN_CONFIRM = "✅ Confirm"
BTN_NEXT = "Next ➡️"

CHOOSE_DATE = "<b>Step 2/4.</b> Choose a day:"
NO_SLOTS = "This day is fully booked, please choose another one."
ASK_NAME = "<b>Step 3/4.</b> What is your name?"
BAD_NAME = "Please send a name between 2 and 50 characters."
ASK_PHONE = "<b>Step 4/4.</b> Tap the button below to share your phone number, or type it in."
BAD_PHONE = "That doesn't look like a phone number. Example: +380501234567"
ALMOST_DONE = "Almost done!"
FLOW_CANCELLED = "Booking cancelled. Use the menu below whenever you're ready."
SLOT_TAKEN = "😔 Someone has just taken this time. Please choose another day:"
NO_BOOKINGS = "You have no upcoming bookings."
PICK_SERVICE = "Please choose at least one service."
EXPIRED = "This button is no longer active. Please start again from the menu."
NOT_FOUND = "Booking not found or already cancelled."


def welcome(first_name: str) -> str:
    return (
        f"Hi, {escape(first_name)}! 👋\n"
        f"Welcome to <b>{escape(config.BUSINESS_NAME)}</b>.\n\n"
        "Book a visit in under a minute, no calls needed."
    )


def no_days() -> str:
    return f"Sorry, there are no free slots in the next few days. Please call us: {escape(config.BUSINESS_PHONE)}"


def fmt_day(d: date) -> str:
    return d.strftime("%a, %d %b")


def fmt_dt(dt: datetime) -> str:
    return dt.strftime("%a, %d %b at %H:%M")


def service_label(s: config.Service, selected: bool = False) -> str:
    return f"{'✅' if selected else '▫️'} {s.title} · {config.CURRENCY}{s.price}"


def choose_service(service_ids: str) -> str:
    text = "<b>Step 1/4.</b> Choose one or more services, then tap Next:"
    chosen = config.combine(service_ids)
    if chosen.id:
        text += f"\n\nSelected: {chosen.title} — <b>{config.CURRENCY}{chosen.price}</b> ({chosen.minutes} min)"
    return text


def too_long(minutes: int) -> str:
    return (
        f"These services take {minutes} min, longer than one {config.SLOT_MINUTES}-min slot. "
        "Please remove one, or call us to book a longer visit."
    )


def services_list() -> str:
    lines = [f"<b>{escape(config.BUSINESS_NAME)} — services</b>\n"]
    for s in config.SERVICES.values():
        lines.append(f"• {s.title} — {config.CURRENCY}{s.price} ({s.minutes} min)")
    return "\n".join(lines)


def contacts() -> str:
    return (
        f"<b>{escape(config.BUSINESS_NAME)}</b>\n"
        f"📍 {escape(config.BUSINESS_ADDRESS)}\n"
        f"📞 {escape(config.BUSINESS_PHONE)}\n"
        f"🕙 {config.WORK_START:02d}:00–{config.WORK_END:02d}:00"
    )


def choose_time(day: date) -> str:
    return f"<b>Step 2/4.</b> Choose a time on {fmt_day(day)}:"


def summary(service: config.Service, start: datetime, name: str, phone: str) -> str:
    return (
        "<b>Please check your booking:</b>\n\n"
        f"💈 {service.title} — {config.CURRENCY}{service.price}\n"
        f"🗓 {fmt_dt(start)}\n"
        f"👤 {escape(name)}\n"
        f"📞 {escape(phone)}"
    )


def booked(b: Booking) -> str:
    return (
        "✅ <b>You're booked!</b>\n\n"
        f"💈 {b.service.title}\n"
        f"🗓 {fmt_dt(b.start_at)}\n"
        f"📍 {escape(config.BUSINESS_ADDRESS)}\n\n"
        f"We'll remind you {config.REMIND_BEFORE_HOURS} hours before. "
        f"Need to change plans? Open '{BTN_MY}'."
    )


def my_bookings(bookings: list[Booking]) -> str:
    lines = ["<b>Your upcoming bookings:</b>\n"]
    for b in bookings:
        lines.append(f"• {fmt_dt(b.start_at)} — {b.service.title}")
    return "\n".join(lines)


def cancelled_by_user(b: Booking) -> str:
    return f"Your booking for {fmt_dt(b.start_at)} has been cancelled."


def cancelled_by_admin(b: Booking) -> str:
    return (
        f"⚠️ Unfortunately, your booking for {fmt_dt(b.start_at)} ({b.service.title}) was cancelled.\n"
        f"Please book another time or call us: {escape(config.BUSINESS_PHONE)}"
    )


def reminder(b: Booking) -> str:
    return (
        f"⏰ Reminder: {b.service.title} today at <b>{b.start_at:%H:%M}</b>.\n"
        f"📍 {escape(config.BUSINESS_ADDRESS)}\n"
        "See you soon!"
    )


def _client(b: Booking) -> str:
    user = f" (@{escape(b.username)})" if b.username else ""
    return f"{escape(b.name)}{user}, {escape(b.phone)}"


def admin_new(b: Booking) -> str:
    return f"🆕 <b>New booking #{b.id}</b>\n{fmt_dt(b.start_at)} — {b.service.title}\n{_client(b)}"


def admin_cancelled(b: Booking) -> str:
    return f"❌ <b>Client cancelled #{b.id}</b>\n{fmt_dt(b.start_at)} — {b.service.title}\n{_client(b)}"


def admin_list(bookings: list[Booking]) -> str:
    if not bookings:
        return f"No bookings for the next {config.DAYS_AHEAD} days."
    lines = [f"<b>Bookings for the next {config.DAYS_AHEAD} days ({len(bookings)}):</b>"]
    day = None
    for b in bookings:
        if b.start_at.date() != day:
            day = b.start_at.date()
            lines.append(f"\n<b>{fmt_day(day)}</b>")
        lines.append(f"{b.start_at:%H:%M} — {b.service.title} — {_client(b)}")
    return "\n".join(lines)
