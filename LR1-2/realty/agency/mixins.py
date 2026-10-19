import calendar
from datetime import timezone as dt_timezone

from django.conf import settings
from django.contrib.auth.mixins import UserPassesTestMixin
from django.utils import timezone

from .models import CompanyInfo, UserProfile
from .timezones import get_timezone


class SiteContextMixin:
    def get_user_profile(self):
        user = getattr(self.request, "user", None)
        if user and user.is_authenticated:
            return getattr(user, "profile", None)
        return None

    def get_timezone_name(self):
        profile = self.get_user_profile()
        if profile and profile.timezone:
            return profile.timezone
        return settings.TIME_ZONE

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        timezone_name = self.get_timezone_name()
        user_timezone = get_timezone(timezone_name)
        timezone_name = user_timezone.key

        utc_now = timezone.now().astimezone(dt_timezone.utc)
        local_now = utc_now.astimezone(user_timezone)
        context.update(
            {
                "company_info": CompanyInfo.objects.first(),
                "user_profile": self.get_user_profile(),
                "user_timezone": timezone_name,
                "current_datetime_local": local_now,
                "current_datetime_utc": utc_now,
                "current_date_local": local_now.strftime("%d/%m/%Y"),
                "current_calendar": calendar.TextCalendar(firstweekday=0).formatmonth(
                    local_now.year,
                    local_now.month,
                ),
                "role_employee": UserProfile.ROLE_EMPLOYEE,
                "role_client": UserProfile.ROLE_CLIENT,
            }
        )
        return context


class RoleRequiredMixin(UserPassesTestMixin):
    allowed_roles = ()

    def test_func(self):
        user = self.request.user
        if not user.is_authenticated:
            return False
        if user.is_superuser:
            return True
        profile = getattr(user, "profile", None)
        return bool(profile and profile.role in self.allowed_roles)


class EmployeeRequiredMixin(RoleRequiredMixin):
    allowed_roles = (UserProfile.ROLE_EMPLOYEE, UserProfile.ROLE_SUPERUSER)
