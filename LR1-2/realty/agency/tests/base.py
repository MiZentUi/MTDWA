from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone

from agency.models import (
    CompanyInfo,
    Deal,
    FAQEntry,
    NewsArticle,
    Owner,
    PartnerCompany,
    PromoCode,
    Property,
    PropertyType,
    Review,
    UserProfile,
    Vacancy,
)


class BaseDataMixin(TestCase):
    def setUp(self):
        super().setUp()
        CompanyInfo.objects.create(
            company_name="realty",
            slogan="Недвижимость без лишней бюрократии",
            about_text="Демо-описание компании.",
            history="2018 — старт\n2020 — рост",
            requisites="УНП 123456789",
            logo_path="agency/img/logo.jpg",
            certificate_html="<section><h3>Сертификат</h3><p>Текст сертификата.</p></section>",
            video_url="https://www.youtube.com/embed/dQw4w9WgXcQ",
            audio_path="agency/media/company-audio.mp3",
            document_path="agency/docs/company-profile.txt",
        )
        self.partner = PartnerCompany.objects.create(
            name="DomMarket",
            website_url="https://example.com/dommarket",
            logo_path="agency/img/partner-1.svg",
            description="Партнёр по новостройкам.",
            sort_order=1,
        )
        self.property_type = PropertyType.objects.create(name="Квартира")
        self.owner = Owner.objects.create(
            full_name="Собственник",
            phone="+375 (29) 123-45-67",
            email="owner@example.com",
        )
        self.employee_user = User.objects.create_user(
            username="employee",
            password="StrongPass123!",
            first_name="Анна",
            last_name="Петрова",
            email="employee@example.com",
        )
        self.employee_profile = self.employee_user.profile
        self.employee_profile.role = UserProfile.ROLE_EMPLOYEE
        self.employee_profile.phone = "+375 (29) 111-11-11"
        self.employee_profile.birth_date = date(1990, 1, 1)
        self.employee_profile.position = "Риэлтор"
        self.employee_profile.save()

        self.client_user = User.objects.create_user(
            username="client",
            password="StrongPass123!",
            first_name="Мария",
            last_name="Орлова",
            email="client@example.com",
        )
        self.client_profile = self.client_user.profile
        self.client_profile.role = UserProfile.ROLE_CLIENT
        self.client_profile.phone = "+375 (29) 222-22-22"
        self.client_profile.birth_date = date(1991, 2, 2)
        self.client_profile.save()

        self.superuser = User.objects.create_superuser(
            username="admin",
            password="StrongPass123!",
            email="admin@example.com",
        )
        self.superuser.profile.phone = "+375 (29) 333-33-33"
        self.superuser.profile.birth_date = date(1985, 3, 3)
        self.superuser.profile.save()

        self.property = Property.objects.create(
            title="Светлая квартира",
            property_type=self.property_type,
            owner=self.owner,
            deal_kind=Property.DEAL_SALE,
            status=Property.STATUS_AVAILABLE,
            city="Минск",
            address="ул. Тестовая, 1",
            description="Тестовый объект.",
            rooms=2,
            area_sqm=Decimal("55.00"),
            price=Decimal("100000.00"),
            published_at=timezone.now(),
        )
        self.property.agents.add(self.employee_profile)

        self.promo = PromoCode.objects.create(
            code="TEST10",
            description="Тестовая скидка",
            discount_percent=10,
            starts_at=timezone.localdate() - timedelta(days=2),
            ends_at=timezone.localdate() + timedelta(days=2),
        )
        self.deal = Deal.objects.create(
            property=self.property,
            client=self.client_profile,
            manager=self.employee_profile,
            promo_code=self.promo,
            status=Deal.STATUS_NEW,
            amount=Decimal("100000.00"),
            commission_percent=Decimal("3.00"),
            agreement_date=timezone.localdate(),
        )
        self.article = NewsArticle.objects.create(
            title="Рынок стабилизируется",
            summary="Краткая сводка по рынку.",
            body="Подробная аналитика рынка недвижимости.",
            image_path="agency/img/news-1.svg",
        )
        FAQEntry.objects.create(question="Как купить квартиру?", answer="Оставьте заявку.")
        Vacancy.objects.create(title="Менеджер", description="Описание вакансии.")
        Review.objects.create(author=self.client_user, rating=5, text="Все понравилось.")
