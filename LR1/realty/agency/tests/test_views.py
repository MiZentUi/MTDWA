from decimal import Decimal
from unittest.mock import patch

from django.urls import reverse

from agency.models import Review

from .base import BaseDataMixin


class ViewTests(BaseDataMixin):
    def test_home_page_loads_latest_article(self):
        response = self.client.get(reverse("realty:home"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.article.title)
        self.assertContains(response, "Компании-партнёры")
        self.assertContains(response, self.partner.name)

    def test_news_detail_page_loads(self):
        response = self.client.get(reverse("realty:news-detail", args=[self.article.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.article.title)
        self.assertContains(response, self.article.body)

    def test_property_list_filters_by_search(self):
        response = self.client.get(reverse("realty:property-list"), {"q": "Светлая"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.property.title)

    @patch("agency.views.fetch_exchange_rates")
    @patch("agency.views.fetch_weather")
    @patch("agency.views.geocode_address")
    def test_property_detail_uses_external_api_data(
        self,
        mocked_geocode,
        mocked_weather,
        mocked_rates,
    ):
        mocked_geocode.return_value = {
            "lat": 53.9,
            "lon": 27.56,
            "display_name": "Минск",
        }
        mocked_weather.return_value = {"temperature": 20, "wind_speed": 4, "time": "2026-05-07"}
        mocked_rates.return_value = {
            "USD": {"rate": Decimal("3.20"), "scale": 1},
            "EUR": {"rate": Decimal("3.45"), "scale": 1},
        }

        response = self.client.get(reverse("realty:property-detail", args=[self.property.slug]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Температура: 20")
        self.assertContains(response, "USD")
        self.assertContains(response, "Добавить в корзину")

    def test_add_to_cart_and_open_cart_page(self):
        response = self.client.post(reverse("realty:property-add-to-cart", args=[self.property.slug]))
        self.assertEqual(response.status_code, 302)
        cart_response = self.client.get(reverse("realty:cart"))
        self.assertEqual(cart_response.status_code, 200)
        self.assertContains(cart_response, self.property.title)
        self.assertContains(cart_response, "Оплатить")

    def test_payment_page_accepts_valid_form(self):
        session = self.client.session
        session["cart"] = {str(self.property.pk): 1}
        session.save()
        response = self.client.post(
            reverse("realty:payment"),
            {
                "full_name": "Иван Иванов",
                "email": "buyer@example.com",
                "phone": "+375 (29) 111-11-11",
                "delivery_date": "2026-09-13",
                "payment_method": "card",
                "promo_code": "",
                "contact_time": "10:30",
                "need_call": "on",
                "agree_terms": "on",
                "comment": "Позвоните утром.",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Оплата оформлена")

    def test_about_page_contains_certificate_and_iframe(self):
        response = self.client.get(reverse("realty:about"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Сертификат")
        self.assertContains(response, "Видео о компании")

    def test_test_page_loads_and_shows_semantic_tags(self):
        response = self.client.get(reverse("realty:test"))
        self.assertEqual(response.status_code, 200)
        for fragment in (
            "Пример листинга",
            "Четверостишие",
            "Адаптивные изображения",
            "Видео и аудио",
            "Таблица с объединением ячеек",
            "Глобальные атрибуты",
        ):
            self.assertContains(response, fragment)

    def test_review_create_requires_login(self):
        response = self.client.get(reverse("realty:review-add"))
        self.assertEqual(response.status_code, 302)

    def test_client_can_create_review(self):
        self.client.force_login(self.client_user)
        response = self.client.post(
            reverse("realty:review-add"),
            {"rating": 4, "text": "Новый отзыв."},
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Review.objects.count(), 2)

    def test_employee_can_access_property_create(self):
        self.client.force_login(self.employee_user)
        response = self.client.get(reverse("realty:property-add"))
        self.assertEqual(response.status_code, 200)

    def test_client_cannot_access_property_create(self):
        self.client.force_login(self.client_user)
        response = self.client.get(reverse("realty:property-add"))
        self.assertEqual(response.status_code, 403)

    @patch("agency.views.fetch_exchange_rates", return_value={})
    def test_dashboard_for_client_shows_own_deals(self, mocked_rates):
        self.client.force_login(self.client_user)
        response = self.client.get(reverse("realty:dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.property.title)
        self.assertContains(response, "data:image/png;base64")

    def test_deal_api_requires_login(self):
        response = self.client.get(reverse("realty:api-deal-stats"))
        self.assertEqual(response.status_code, 302)

    def test_deal_api_returns_scoped_stats_for_client(self):
        self.client.force_login(self.client_user)
        response = self.client.get(reverse("realty:api-deal-stats"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["total_count"], 1)

    def test_property_summary_api_requires_login(self):
        response = self.client.get(reverse("realty:api-property-summary"))
        self.assertEqual(response.status_code, 302)

    def test_analytics_page_loads_for_employee(self):
        self.client.force_login(self.employee_user)
        response = self.client.get(reverse("realty:analytics"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Статистические показатели")
        self.assertContains(response, "data:image/png;base64")
