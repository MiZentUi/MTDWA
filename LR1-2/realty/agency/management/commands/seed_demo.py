from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.utils import timezone

from agency.models import (
    Amenity,
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


class Command(BaseCommand):
    help = "Заполняет проект демонстрационными данными для лабораторной работы."

    def handle(self, *args, **options):
        self.stdout.write("Создание демонстрационных данных...")

        CompanyInfo.objects.update_or_create(
            company_name="realty",
            defaults={
                "slogan": "Надежная продажа и аренда недвижимости",
                "about_text": (
                    "Агентство помогает подбирать квартиры, дома и коммерческие объекты, "
                    "сопровождает сделки и консультирует по рынку недвижимости."
                ),
                "history": (
                    "2018 — запуск компании\n"
                    "2020 — первая база партнерских новостроек\n"
                    "2022 — запуск дистанционных консультаций\n"
                    "2024 — расширение каталога коммерческой недвижимости"
                ),
                "requisites": (
                    "ООО «realty»\n"
                    "УНП 123456789\n"
                    "р/с BY00REAL00000000000000000000\n"
                    "Адрес: г. Минск, ул. Демонстрационная, 10"
                ),
                "logo_path": "agency/img/logo.jpg",
                "certificate_html": (
                    "<section>"
                    "<h4>Сертификат партнёра</h4>"
                    "<p><strong>Настоящим подтверждается</strong>, что агентство <em>realty</em> "
                    "в 2026 году прошло внутреннюю аттестацию по сопровождению сделок с недвижимостью.</p>"
                    "<p>Сфера действия: консультации, проверка документов, сопровождение договоров.</p>"
                    "<p>Номер сертификата: CERT-2026-001.</p>"
                    "</section>"
                ),
                "video_url": "https://www.youtube.com/embed/dQw4w9WgXcQ",
                "audio_path": "agency/media/company-audio.mp3",
                "document_path": "agency/docs/company-profile.txt",
            },
        )

        for idx, (name, url, description) in enumerate(
            (
                ("DomMarket", "https://example.com/dommarket", "Партнёр по городским новостройкам."),
                ("OfficeHub", "https://example.com/officehub", "Партнёр по коммерческой недвижимости."),
                ("RentLine", "https://example.com/rentline", "Партнёр по краткосрочной аренде."),
            ),
            start=1,
        ):
            PartnerCompany.objects.update_or_create(
                name=name,
                defaults={
                    "website_url": url,
                    "logo_path": f"agency/img/partner-{idx}.svg",
                    "description": description,
                    "sort_order": idx,
                },
            )

        property_types = {}
        for name, description in (
            ("Квартира", "Городские квартиры для покупки и аренды."),
            ("Дом", "Частные дома и коттеджи."),
            ("Офис", "Коммерческая недвижимость для бизнеса."),
        ):
            property_types[name], _ = PropertyType.objects.get_or_create(
                name=name,
                defaults={"description": description},
            )

        amenities = []
        for name in ("Балкон", "Парковка", "Лифт", "Мебель", "Охрана", "Терраса"):
            amenity, _ = Amenity.objects.get_or_create(name=name)
            amenities.append(amenity)

        owners = []
        for idx in range(1, 6):
            owner, _ = Owner.objects.get_or_create(
                email=f"owner{idx}@example.com",
                defaults={
                    "full_name": f"Владелец {idx}",
                    "phone": f"+375 (29) 555-1{idx}-0{idx}",
                    "notes": "Собственник объекта.",
                },
            )
            owners.append(owner)

        admin_user = self._create_user(
            username="admin",
            password="Admin12345!",
            role=UserProfile.ROLE_SUPERUSER,
            first_name="System",
            last_name="Admin",
            email="admin@example.com",
            is_staff=True,
            is_superuser=True,
            position="Владелец агентства",
        )
        employee_1 = self._create_user(
            username="agent1",
            password="Agent12345!",
            role=UserProfile.ROLE_EMPLOYEE,
            first_name="Анна",
            last_name="Петрова",
            email="agent1@example.com",
            is_staff=True,
            position="Риэлтор",
            responsibilities="Работа с покупателями и сопровождение сделок.",
        )
        employee_2 = self._create_user(
            username="agent2",
            password="Agent12345!",
            role=UserProfile.ROLE_EMPLOYEE,
            first_name="Илья",
            last_name="Соколов",
            email="agent2@example.com",
            is_staff=True,
            position="Менеджер по аренде",
            responsibilities="Подбор арендных объектов и переговоры с владельцами.",
        )
        client_1 = self._create_user(
            username="client1",
            password="Client12345!",
            role=UserProfile.ROLE_CLIENT,
            first_name="Мария",
            last_name="Коваленко",
            email="client1@example.com",
        )
        client_2 = self._create_user(
            username="client2",
            password="Client12345!",
            role=UserProfile.ROLE_CLIENT,
            first_name="Дмитрий",
            last_name="Орлов",
            email="client2@example.com",
        )

        cities = [
            "Минск",
            "Брест",
            "Гродно",
            "Витебск",
            "Гомель",
            "Могилев",
            "Минск",
            "Брест",
            "Гродно",
            "Витебск",
        ]
        created_properties = []
        for idx in range(10):
            property_obj, created = Property.objects.get_or_create(
                title=f"Объект {idx + 1}",
                city=cities[idx],
                address=f"ул. Примерная, д. {idx + 3}",
                defaults={
                    "property_type": property_types["Квартира" if idx < 4 else "Дом" if idx < 7 else "Офис"],
                    "owner": owners[idx % len(owners)],
                    "deal_kind": Property.DEAL_SALE if idx % 2 == 0 else Property.DEAL_RENT,
                    "status": Property.STATUS_AVAILABLE,
                    "description": (
                        "Ухоженный объект с развитой инфраструктурой, удобной логистикой и "
                        "возможностью быстрого выхода на сделку."
                    ),
                    "rooms": 1 + idx % 4,
                    "area_sqm": Decimal("42.50") + idx * Decimal("6.10"),
                    "price": Decimal("85000.00") + idx * Decimal("12500.00"),
                    "published_at": timezone.now() - timedelta(days=idx),
                },
            )
            property_obj.agents.set([employee_1.profile if idx % 2 == 0 else employee_2.profile])
            property_obj.amenities.set(amenities[: 2 + idx % 4])
            created_properties.append(property_obj)
            if created:
                self.stdout.write(f"Добавлен объект: {property_obj.title}")

        today = timezone.localdate()
        promo_active, _ = PromoCode.objects.get_or_create(
            code="SALE10",
            defaults={
                "description": "Скидка 10% на сопровождение сделки.",
                "discount_percent": 10,
                "starts_at": today - timedelta(days=10),
                "ends_at": today + timedelta(days=20),
            },
        )
        PromoCode.objects.get_or_create(
            code="RENT5",
            defaults={
                "description": "Скидка 5% на услуги аренды.",
                "discount_percent": 5,
                "starts_at": today - timedelta(days=5),
                "ends_at": today + timedelta(days=5),
            },
        )
        PromoCode.objects.get_or_create(
            code="ARCHIVE7",
            defaults={
                "description": "Архивный промокод для демонстрации.",
                "discount_percent": 7,
                "starts_at": today - timedelta(days=40),
                "ends_at": today - timedelta(days=5),
            },
        )

        Deal.objects.get_or_create(
            property=created_properties[0],
            client=client_1.profile,
            manager=employee_1.profile,
            defaults={
                "promo_code": promo_active,
                "status": Deal.STATUS_CLOSED,
                "amount": Decimal("98000.00"),
                "commission_percent": Decimal("3.50"),
                "agreement_date": today - timedelta(days=12),
                "closing_date": today - timedelta(days=2),
                "notes": "Сделка успешно закрыта.",
            },
        )
        Deal.objects.get_or_create(
            property=created_properties[1],
            client=client_2.profile,
            manager=employee_2.profile,
            defaults={
                "status": Deal.STATUS_IN_PROGRESS,
                "amount": Decimal("2200.00"),
                "commission_percent": Decimal("5.00"),
                "agreement_date": today - timedelta(days=4),
                "notes": "Аренда согласовывается.",
            },
        )
        Deal.objects.get_or_create(
            property=created_properties[2],
            client=client_1.profile,
            manager=employee_1.profile,
            defaults={
                "status": Deal.STATUS_NEW,
                "amount": Decimal("135000.00"),
                "commission_percent": Decimal("3.00"),
                "agreement_date": today - timedelta(days=1),
            },
        )

        for idx in range(1, 4):
            NewsArticle.objects.get_or_create(
                title=f"Новость {idx}",
                defaults={
                    "summary": f"Краткое описание новости {idx} в одно предложение.",
                    "body": (
                        "Подробная статья о рынке недвижимости, ценах, спросе, юридических нюансах "
                        "и практических советах для клиентов агентства."
                    ),
                    "image_path": f"agency/img/news-{idx}.svg",
                    "published_at": timezone.now() - timedelta(days=idx),
                },
            )

        for question, answer in (
            ("Что входит в сопровождение сделки?", "Проверка документов, переговоры и оформление."),
            ("Как быстро найти арендатора?", "Подготовить качественное описание и актуальные фотографии."),
            ("Можно ли использовать промокод?", "Да, если он активен на дату оформления услуги."),
        ):
            FAQEntry.objects.get_or_create(question=question, defaults={"answer": answer})

        for title in ("Риэлтор по новостройкам", "Специалист по аренде", "Юрист по сделкам"):
            Vacancy.objects.get_or_create(
                title=title,
                defaults={
                    "description": "Работа с клиентами, документами и сопровождением объектов.",
                    "salary_from": 1800,
                    "salary_to": 3200,
                    "is_active": True,
                },
            )

        Review.objects.get_or_create(
            author=client_1,
            text="Сделку закрыли быстро, всё объяснили понятным языком.",
            defaults={"rating": 5, "approved": True},
        )
        Review.objects.get_or_create(
            author=client_2,
            text="Удобный подбор объектов и подробные консультации.",
            defaults={"rating": 4, "approved": True},
        )

        self.stdout.write(
            self.style.SUCCESS(
                "Демонстрационные данные готовы. Логины: admin / agent1 / agent2 / client1 / client2"
            )
        )

    def _create_user(
        self,
        *,
        username,
        password,
        role,
        first_name,
        last_name,
        email,
        is_staff=False,
        is_superuser=False,
        position="",
        responsibilities="",
    ):
        user, created = User.objects.get_or_create(
            username=username,
            defaults={
                "first_name": first_name,
                "last_name": last_name,
                "email": email,
                "is_staff": is_staff,
                "is_superuser": is_superuser,
            },
        )
        if created:
            user.set_password(password)
            user.save()
        else:
            user.first_name = first_name
            user.last_name = last_name
            user.email = email
            user.is_staff = is_staff
            user.is_superuser = is_superuser
            user.set_password(password)
            user.save()

        profile = user.profile
        profile.role = role
        profile.phone = "+375 (29) 111-11-11" if username.endswith("1") else "+375 (29) 222-22-22"
        profile.birth_date = date(1990, 1, 1)
        profile.position = position
        profile.responsibilities = responsibilities
        profile.bio = "Демо-профиль для лабораторной работы."
        profile.photo_url = ""
        profile.save()
        return user
