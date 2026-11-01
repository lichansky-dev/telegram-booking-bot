from datetime import date, datetime

from aiogram.filters.callback_data import CallbackData
from aiogram.types import (
    InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder

from . import config, texts
from .db import Booking


class ServiceCb(CallbackData, prefix="svc"):
    id: str


class DateCb(CallbackData, prefix="day"):
    d: str  # ISO date


class TimeCb(CallbackData, prefix="time"):
    t: str  # HHMM (":" is reserved by CallbackData)


class NavCb(CallbackData, prefix="nav"):
    to: str  # services | next | dates | cancel


class ConfirmCb(CallbackData, prefix="confirm"):
    action: str  # yes | no


class CancelCb(CallbackData, prefix="ucancel"):
    id: int


class AdminCancelCb(CallbackData, prefix="acancel"):
    id: int


def main_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=texts.BTN_BOOK)],
            [KeyboardButton(text=texts.BTN_MY), KeyboardButton(text=texts.BTN_SERVICES)],
            [KeyboardButton(text=texts.BTN_CONTACTS)],
        ],
        resize_keyboard=True,
    )


def phone() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=texts.BTN_SHARE_PHONE, request_contact=True)]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def _nav(text: str, to: str) -> InlineKeyboardButton:
    return InlineKeyboardButton(text=text, callback_data=NavCb(to=to).pack())


def services(service_ids: str = "") -> InlineKeyboardMarkup:
    selected = set(service_ids.split(","))
    b = InlineKeyboardBuilder()
    for s in config.SERVICES.values():
        b.button(text=texts.service_label(s, s.id in selected), callback_data=ServiceCb(id=s.id))
    b.adjust(1)
    b.row(_nav(texts.BTN_CANCEL, "cancel"), _nav(texts.BTN_NEXT, "next"))
    return b.as_markup()


def dates(days: list[date]) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    for d in days:
        b.button(text=texts.fmt_day(d), callback_data=DateCb(d=d.isoformat()))
    b.adjust(2)
    b.row(_nav(texts.BTN_BACK, "services"), _nav(texts.BTN_CANCEL, "cancel"))
    return b.as_markup()


def times(slots: list[datetime]) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    for s in slots:
        b.button(text=s.strftime("%H:%M"), callback_data=TimeCb(t=s.strftime("%H%M")))
    b.adjust(4)
    b.row(_nav(texts.BTN_BACK, "dates"), _nav(texts.BTN_CANCEL, "cancel"))
    return b.as_markup()


def confirm() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text=texts.BTN_CONFIRM, callback_data=ConfirmCb(action="yes"))
    b.button(text=texts.BTN_CANCEL, callback_data=ConfirmCb(action="no"))
    return b.as_markup()


def user_bookings(bookings: list[Booking]) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    for item in bookings:
        b.button(text=f"❌ Cancel {item.start_at:%d %b %H:%M}", callback_data=CancelCb(id=item.id))
    b.adjust(1)
    return b.as_markup()


def admin_bookings(bookings: list[Booking]) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    for item in bookings:
        b.button(
            text=f"❌ #{item.id} {item.start_at:%d %b %H:%M} {item.name[:15]}",
            callback_data=AdminCancelCb(id=item.id),
        )
    b.adjust(1)
    return b.as_markup()
