from functools import lru_cache
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError, available_timezones

from django.conf import settings


UTC_TIMEZONE_NAME = "UTC"


@lru_cache
def get_timezone_names():
    return tuple(sorted(available_timezones()))


@lru_cache
def get_timezone_choices():
    return tuple((timezone_name, timezone_name) for timezone_name in get_timezone_names())


def get_default_timezone_name():
    return getattr(settings, "TIME_ZONE", UTC_TIMEZONE_NAME)


def get_timezone(timezone_name=None):
    for candidate in (timezone_name, get_default_timezone_name(), UTC_TIMEZONE_NAME):
        if not candidate:
            continue
        try:
            return ZoneInfo(candidate)
        except (ZoneInfoNotFoundError, ValueError, TypeError):
            continue
    return ZoneInfo(UTC_TIMEZONE_NAME)
