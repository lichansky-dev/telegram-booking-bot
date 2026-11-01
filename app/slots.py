from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from . import config, db

TZ = ZoneInfo(config.TIMEZONE)


def now() -> datetime:
    """Current local business time, naive (that's how times are stored in the DB)."""
    return datetime.now(TZ).replace(tzinfo=None, second=0, microsecond=0)


def day_slots(day: date) -> list[datetime]:
    step = timedelta(minutes=config.SLOT_MINUTES)
    cur = datetime.combine(day, time(config.WORK_START))
    end = datetime.combine(day, time(config.WORK_END))
    slots = []
    while cur + step <= end:
        slots.append(cur)
        cur += step
    return slots


async def free_slots(day: date) -> list[datetime]:
    if day.weekday() in config.CLOSED_WEEKDAYS:
        return []
    busy = await db.busy_slots(day)
    earliest = now() + timedelta(minutes=config.MIN_LEAD_MINUTES)
    return [s for s in day_slots(day) if s >= earliest and s.strftime(db.FMT) not in busy]


async def available_days() -> list[date]:
    today = now().date()
    days = [today + timedelta(days=i) for i in range(config.DAYS_AHEAD)]
    return [d for d in days if await free_slots(d)]
