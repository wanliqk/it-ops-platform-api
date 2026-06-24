from __future__ import annotations

from datetime import date, datetime
from zoneinfo import ZoneInfo

APP_TIMEZONE = ZoneInfo("Asia/Shanghai")
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
DATE_FORMAT = "%Y-%m-%d"


def local_now() -> datetime:
    return datetime.now(APP_TIMEZONE).replace(tzinfo=None)


def format_datetime(value: datetime) -> str:
    if value.tzinfo is not None:
        value = value.astimezone(APP_TIMEZONE).replace(tzinfo=None)
    return value.strftime(DATETIME_FORMAT)


def format_date(value: date) -> str:
    return value.strftime(DATE_FORMAT)
