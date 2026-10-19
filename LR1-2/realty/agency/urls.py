from django.urls import path, re_path

from . import views


app_name = "realty"

urlpatterns = [
    path("", views.HomeView.as_view(), name="home"),
    path("about/", views.AboutView.as_view(), name="about"),
    path("news/", views.NewsListView.as_view(), name="news"),
    path("news/<int:pk>/", views.NewsDetailView.as_view(), name="news-detail"),
    path("faq/", views.FAQListView.as_view(), name="faq"),
    path("contacts/", views.ContactListView.as_view(), name="contacts"),
    path("privacy/", views.PrivacyView.as_view(), name="privacy"),
    path("test/", views.TestView.as_view(), name="test"),
    path("vacancies/", views.VacancyListView.as_view(), name="vacancies"),
    path("reviews/", views.ReviewListView.as_view(), name="reviews"),
    path("reviews/add/", views.ReviewCreateView.as_view(), name="review-add"),
    path("promocodes/", views.PromoListView.as_view(), name="promocodes"),
    path("register/", views.RegisterView.as_view(), name="register"),
    path("dashboard/", views.DashboardView.as_view(), name="dashboard"),
    path("cart/", views.CartView.as_view(), name="cart"),
    path("payment/", views.PaymentView.as_view(), name="payment"),
    path("properties/", views.PropertyListView.as_view(), name="property-list"),
    path("properties/add/", views.PropertyCreateView.as_view(), name="property-add"),
    re_path(
        r"^properties/(?P<slug>[-a-z0-9]+)/$",
        views.PropertyDetailView.as_view(),
        name="property-detail",
    ),
    re_path(
        r"^properties/(?P<slug>[-a-z0-9]+)/add-to-cart/$",
        views.PropertyCartAddView.as_view(),
        name="property-add-to-cart",
    ),
    re_path(
        r"^properties/(?P<slug>[-a-z0-9]+)/edit/$",
        views.PropertyUpdateView.as_view(),
        name="property-edit",
    ),
    re_path(
        r"^properties/(?P<slug>[-a-z0-9]+)/delete/$",
        views.PropertyDeleteView.as_view(),
        name="property-delete",
    ),
    path("cart/<int:pk>/update/", views.CartUpdateView.as_view(), name="cart-update"),
    path("deals/", views.DealListView.as_view(), name="deal-list"),
    path("deals/add/", views.DealCreateView.as_view(), name="deal-add"),
    re_path(r"^deals/(?P<pk>\d+)/$", views.DealDetailView.as_view(), name="deal-detail"),
    re_path(r"^deals/(?P<pk>\d+)/edit/$", views.DealUpdateView.as_view(), name="deal-edit"),
    re_path(
        r"^deals/(?P<pk>\d+)/delete/$",
        views.DealDeleteView.as_view(),
        name="deal-delete",
    ),
    path("analytics/", views.AnalyticsView.as_view(), name="analytics"),
    path(
        "api/property-summary/",
        views.PropertySummaryApiView.as_view(),
        name="api-property-summary",
    ),
    path("api/deal-stats/", views.DealStatsApiView.as_view(), name="api-deal-stats"),
]
