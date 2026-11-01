from dataclasses import dataclass
from datetime import date, datetime

import aiosqlite

from . import config

FMT = "%Y-%m-%d %H:%M"

SCHEMA = """
CREATE TABLE IF NOT EXISTS bookings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    username TEXT,
    name TEXT NOT NULL,
    phone TEXT NOT NULL,
    service_id TEXT NOT NULL,
    start_at TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'active',
    reminded INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE UNIQUE INDEX IF NOT EXISTS uniq_active_slot ON bookings(start_at) WHERE status = 'active';
"""


@dataclass
class Booking:
    id: int
    user_id: int
    username: str | None
    name: str
    phone: str
    service_id: str
    start_at: datetime
    status: str

    @property
    def service(self) -> config.Service:
        return config.combine(self.service_id)

    @classmethod
    def from_row(cls, row: aiosqlite.Row) -> "Booking":
        return cls(
            id=row["id"],
            user_id=row["user_id"],
            username=row["username"],
            name=row["name"],
            phone=row["phone"],
            service_id=row["service_id"],
            start_at=datetime.strptime(row["start_at"], FMT),
            status=row["status"],
        )


async def init() -> None:
    async with aiosqlite.connect(config.DB_PATH) as conn:
        await conn.executescript(SCHEMA)
        await conn.commit()


async def _fetch(query: str, *args) -> list[Booking]:
    async with aiosqlite.connect(config.DB_PATH) as conn:
        conn.row_factory = aiosqlite.Row
        async with conn.execute(query, args) as cur:
            return [Booking.from_row(r) for r in await cur.fetchall()]


async def _execute(query: str, *args) -> int:
    async with aiosqlite.connect(config.DB_PATH) as conn:
        cur = await conn.execute(query, args)
        await conn.commit()
        return cur.rowcount


async def add_booking(
    user_id: int, username: str | None, name: str, phone: str,
    service_id: str, start_at: datetime, reminded: bool,
) -> int | None:
    """Returns the new booking id, or None if the slot was taken in the meantime."""
    try:
        async with aiosqlite.connect(config.DB_PATH) as conn:
            cur = await conn.execute(
                "INSERT INTO bookings (user_id, username, name, phone, service_id, start_at, reminded)"
                " VALUES (?, ?, ?, ?, ?, ?, ?)",
                (user_id, username, name, phone, service_id, start_at.strftime(FMT), int(reminded)),
            )
            await conn.commit()
            return cur.lastrowid
    except aiosqlite.IntegrityError:
        return None


async def busy_slots(day: date) -> set[str]:
    async with aiosqlite.connect(config.DB_PATH) as conn:
        async with conn.execute(
            "SELECT start_at FROM bookings WHERE status = 'active' AND start_at LIKE ?",
            (day.isoformat() + "%",),
        ) as cur:
            return {row[0] for row in await cur.fetchall()}


async def get(booking_id: int) -> Booking | None:
    rows = await _fetch("SELECT * FROM bookings WHERE id = ?", booking_id)
    return rows[0] if rows else None


async def user_bookings(user_id: int, since: datetime) -> list[Booking]:
    return await _fetch(
        "SELECT * FROM bookings WHERE user_id = ? AND status = 'active' AND start_at >= ? ORDER BY start_at",
        user_id, since.strftime(FMT),
    )


async def upcoming(since: datetime, until: datetime) -> list[Booking]:
    return await _fetch(
        "SELECT * FROM bookings WHERE status = 'active' AND start_at >= ? AND start_at < ? ORDER BY start_at",
        since.strftime(FMT), until.strftime(FMT),
    )


async def cancel(booking_id: int) -> bool:
    return await _execute(
        "UPDATE bookings SET status = 'cancelled' WHERE id = ? AND status = 'active'", booking_id
    ) > 0


async def due_reminders(now: datetime, until: datetime) -> list[Booking]:
    return await _fetch(
        "SELECT * FROM bookings WHERE status = 'active' AND reminded = 0 AND start_at > ? AND start_at <= ?",
        now.strftime(FMT), until.strftime(FMT),
    )


async def mark_reminded(booking_id: int) -> None:
    await _execute("UPDATE bookings SET reminded = 1 WHERE id = ?", booking_id)
