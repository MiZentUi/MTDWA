from agency.forms import DealForm, SignUpForm
from agency.models import UserProfile

from .base import BaseDataMixin


class FormTests(BaseDataMixin):
    def test_signup_form_saves_client_profile(self):
        form = SignUpForm(
            data={
                "username": "newclient",
                "first_name": "Иван",
                "last_name": "Новиков",
                "email": "newclient@example.com",
                "phone": "+375 (29) 444-44-44",
                "birth_date": "1990-01-01",
                "timezone": "Europe/Minsk",
                "password1": "StrongPass123!",
                "password2": "StrongPass123!",
            }
        )
        self.assertTrue(form.is_valid(), form.errors)
        user = form.save()
        self.assertEqual(user.profile.role, UserProfile.ROLE_CLIENT)
        self.assertEqual(user.profile.phone, "+375 (29) 444-44-44")

    def test_signup_form_rejects_invalid_phone(self):
        form = SignUpForm(
            data={
                "username": "badclient",
                "first_name": "Иван",
                "last_name": "Новиков",
                "email": "badclient@example.com",
                "phone": "123",
                "birth_date": "1990-01-01",
                "timezone": "Europe/Minsk",
                "password1": "StrongPass123!",
                "password2": "StrongPass123!",
            }
        )
        self.assertFalse(form.is_valid())
        self.assertIn("phone", form.errors)

    def test_deal_form_limits_manager_queryset_for_employee(self):
        form = DealForm(user=self.employee_user)
        self.assertEqual(list(form.fields["manager"].queryset), [self.employee_profile])
