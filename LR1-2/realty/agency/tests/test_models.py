from datetime import date, timedelta
from decimal import Decimal

from django.core.exceptions import ValidationError

from agency.models import Deal, PromoCode, Property, UserProfile

from .base import BaseDataMixin


class ModelTests(BaseDataMixin):
    def test_underage_profile_rejected(self):
        self.client_profile.birth_date = date.today() - timedelta(days=365 * 17)
        with self.assertRaises(ValidationError):
            self.client_profile.full_clean()

    def test_property_slug_generated(self):
        self.assertTrue(self.property.slug)
        self.assertIn("svetlaya-kvartira", self.property.slug)

    def test_closed_deal_updates_property_status(self):
        self.deal.status = Deal.STATUS_CLOSED
        self.deal.closing_date = date.today()
        self.deal.save()
        self.property.refresh_from_db()
        self.assertEqual(self.property.status, Property.STATUS_SOLD)

    def test_promo_is_current(self):
        self.assertTrue(self.promo.is_current)

    def test_deal_rejects_employee_as_client(self):
        self.deal.client = self.employee_profile
        with self.assertRaises(ValidationError):
            self.deal.full_clean()

    def test_discount_amount_is_calculated(self):
        self.assertEqual(self.deal.discount_amount, Decimal("10000.00"))

    def test_superuser_profile_role_is_superuser(self):
        self.assertEqual(self.superuser.profile.role, UserProfile.ROLE_SUPERUSER)
