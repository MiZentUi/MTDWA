from datetime import timezone as dt_timezone

from django.conf import settings
from django.utils import timezone

from .timezones import get_timezone


def site_time(request):
    profile = getattr(getattr(request, "user", None), "profile", None)
    timezone_name = profile.timezone if profile and profile.timezone else settings.TIME_ZONE
    user_timezone = get_timezone(timezone_name)
    utc_now = timezone.now().astimezone(dt_timezone.utc)
    local_now = utc_now.astimezone(user_timezone)
    return {
        "user_timezone": user_timezone.key,
        "current_datetime_local": local_now,
        "current_datetime_utc": utc_now,
    }
