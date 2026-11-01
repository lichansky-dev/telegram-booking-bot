# Telegram Booking Bot for Barbershops & Salons

A Telegram bot that lets clients book appointments in under a minute, with no calls and no app to install.
Built for barbershops, beauty salons, nail studios, massage therapists, tutors and any business that works by appointment.

## Features

**For clients**
- 4-step booking: services (pick one or several, total price shown) → day & time → name → phone
- Only free time slots are shown; double booking is impossible
- Phone number shared with one tap
- "My bookings" with one-tap cancellation
- Automatic reminder 2 hours before the visit
- Services & prices, contacts and working hours

**For the business owner**
- Instant notification about every new booking and cancellation
- `/admin` shows all bookings for the next 7 days, grouped by day
- Cancel any booking from Telegram; the client is notified automatically
- Several admins supported

**Configurable**: services, prices, working hours, slot length, days off, booking horizon, reminder time, timezone.

## Tech stack

Python 3.12 · aiogram 3 · SQLite (aiosqlite) · asyncio

## Quick start

1. Create a bot with [@BotFather](https://t.me/BotFather) and copy the token.
2. Install and configure:
   ```bash
   python -m venv .venv
   .venv\Scripts\activate          # Windows  (Linux/macOS: source .venv/bin/activate)
   pip install -r requirements.txt
   copy .env.example .env          # Linux/macOS: cp .env.example .env
   ```
3. Put your token into `.env` as `BOT_TOKEN=...`.
4. Run `python bot.py`, send `/myid` to the bot and put that ID into `ADMIN_IDS` in `.env`.
5. Restart the bot and you're live.

Services and schedule are configured in `app/config.py`, all texts are in `app/texts.py`.

## Project structure

```
bot.py                 entry point
app/config.py          settings: services, schedule, business info
app/db.py              SQLite storage
app/slots.py           free slot calculation
app/handlers_user.py   client booking flow
app/handlers_admin.py  admin panel
app/reminders.py       reminder background task
app/keyboards.py       buttons
app/texts.py           all bot messages
```

## Possible extensions

Multiple masters, Google Calendar sync, online prepayment, Ukrainian/Russian interface, Google Sheets export, web admin panel.
