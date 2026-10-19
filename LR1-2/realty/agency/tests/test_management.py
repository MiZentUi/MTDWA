from django.contrib.auth.models import User
from django.core.management import call_command

from agency.models import CompanyInfo, PartnerCompany, Property

from .base import BaseDataMixin


class ManagementCommandTests(BaseDataMixin):
    def test_seed_demo_creates_admin_and_properties(self):
        Property.objects.all().delete()
        PartnerCompany.objects.all().delete()
        call_command("seed_demo")
        self.assertTrue(User.objects.filter(username="admin").exists())
        self.assertGreaterEqual(Property.objects.count(), 10)
        self.assertTrue(CompanyInfo.objects.exists())
        self.assertGreaterEqual(PartnerCompany.objects.count(), 3)
