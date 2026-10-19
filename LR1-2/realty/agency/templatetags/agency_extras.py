from django import template
from django.utils import timezone

from agency.timezones import UTC_TIMEZONE_NAME, get_timezone


register = template.Library()


@register.filter
def local_datetime(value, timezone_name):
    if not value:
        return ""
    if timezone.is_naive(value):
        value = timezone.make_aware(value, timezone.get_current_timezone())
    user_timezone = get_timezone(timezone_name)
    return value.astimezone(user_timezone).strftime("%d/%m/%Y %H:%M")


@register.filter
def utc_datetime(value):
    if not value:
        return ""
    if timezone.is_naive(value):
        value = timezone.make_aware(value, timezone.get_current_timezone())
    return value.astimezone(get_timezone(UTC_TIMEZONE_NAME)).strftime("%d/%m/%Y %H:%M")
