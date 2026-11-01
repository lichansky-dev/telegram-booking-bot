import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Service:
    id: str
    title: str
    price: int
    minutes: int


BOT_TOKEN = os.getenv("BOT_TOKEN", "")
ADMIN_IDS = {int(x) for x in os.getenv("ADMIN_IDS", "").replace(" ", "").split(",") if x}
DB_PATH = os.getenv("DB_PATH", "bookings.db")
TIMEZONE = os.getenv("TIMEZONE", "Europe/Kyiv")

BUSINESS_NAME = os.getenv("BUSINESS_NAME", "Sharp Cuts Barbershop")
BUSINESS_ADDRESS = os.getenv("BUSINESS_ADDRESS", "12 Main Street, Kyiv")
BUSINESS_PHONE = os.getenv("BUSINESS_PHONE", "+380 00 000 0000")

CURRENCY = "$"
SERVICES = {
    s.id: s
    for s in [
        Service("haircut", "Men's haircut", 25, 40),
        Service("beard", "Beard trim", 15, 20),
        Service("styling", "Hair styling", 10, 15),
        Service("kids", "Kids haircut", 20, 40),
    ]
}


def combine(service_ids: str) -> Service:
    """Turn "haircut,beard" into one Service with the summed price and duration."""
    items = [SERVICES[i] for i in service_ids.split(",") if i in SERVICES]
    return Service(
        id=",".join(s.id for s in items),
        title=" + ".join(s.title for s in items),
        price=sum(s.price for s in items),
        minutes=sum(s.minutes for s in items),
    )

# Schedule: hourly slots from WORK_START to WORK_END, one client per slot
WORK_START = 10
WORK_END = 20
SLOT_MINUTES = 60
DAYS_AHEAD = 7
CLOSED_WEEKDAYS = {6}  # 0 = Monday ... 6 = Sunday
MIN_LEAD_MINUTES = 30  # earliest booking is 30 min from now
REMIND_BEFORE_HOURS = 2
