# app/utils/timeutils.py
from datetime import datetime, timedelta, timezone
import zoneinfo

APP_TZ = zoneinfo.ZoneInfo("America/New_York")  # change if needed

def utcnow():
    # Always work in UTC internally
    return datetime.now(timezone.utc)

def last_24h_window(now_utc: datetime | None = None) -> tuple[datetime, datetime]:
    """
    Returns (start_utc, end_utc) spanning the last 24 hours ending at now_utc.
    """
    if now_utc is None:
        now_utc = utcnow()
    start_utc = now_utc - timedelta(hours=24)
    return start_utc, now_utc

def local_day_bounds(now_utc: datetime | None = None, tz: zoneinfo.ZoneInfo | None = None) -> tuple[datetime, datetime]:
    """
    Calendar-day bounds for *reports*, using local time (e.g., America/New_York).
    Returns (start_utc, end_utc).
    """
    if tz is None:
        tz = APP_TZ
    if now_utc is None:
        now_utc = utcnow()

    now_local = now_utc.astimezone(tz)
    start_local = now_local.replace(hour=0, minute=0, second=0, microsecond=0)
    end_local = start_local + timedelta(days=1)
    # Convert back to UTC for querying the DB
    return start_local.astimezone(timezone.utc), end_local.astimezone(timezone.utc)
