import logging
from decimal import Decimal
from statistics import StatisticsError, mean, median, mode

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Avg, Count, Q, Sum
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.views import View
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    TemplateView,
    UpdateView,
)

from .charts import collect_property_type_stats, render_property_type_chart
from .forms import DealForm, PaymentForm, PropertyForm, ReviewForm, SignUpForm
from .mixins import EmployeeRequiredMixin, SiteContextMixin
from .models import (
    Deal,
    FAQEntry,
    NewsArticle,
    PartnerCompany,
    PromoCode,
    Property,
    PropertyType,
    Review,
    UserProfile,
    Vacancy,
    employee_profiles_queryset,
)
from .services import ExternalAPIError, fetch_exchange_rates, fetch_weather, geocode_address


logger = logging.getLogger("realty")


class HomeView(SiteContextMixin, TemplateView):
    template_name = "agency/home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "latest_article": NewsArticle.objects.filter(is_published=True).first(),
                "featured_properties": Property.objects.select_related(
                    "property_type",
                    "owner",
                ).prefetch_related("agents")[:6],
                "total_properties": Property.objects.count(),
                "total_deals": Deal.objects.count(),
                "employee_count": employee_profiles_queryset().count(),
                "partners": PartnerCompany.objects.all(),
                "banner_images": [
                    "agency/img/banner-1.svg",
                    "agency/img/banner-2.svg",
                    "agency/img/banner-3.svg",
                ],
            }
        )
        return context


class AboutView(SiteContextMixin, TemplateView):
    template_name = "agency/about.html"


class NewsListView(SiteContextMixin, ListView):
    template_name = "agency/news_list.html"
    context_object_name = "articles"
    queryset = NewsArticle.objects.filter(is_published=True)


class NewsDetailView(SiteContextMixin, DetailView):
    template_name = "agency/news_detail.html"
    context_object_name = "article"
    queryset = NewsArticle.objects.filter(is_published=True)


class FAQListView(SiteContextMixin, ListView):
    template_name = "agency/faq_list.html"
    context_object_name = "entries"
    queryset = FAQEntry.objects.all()


class ContactListView(SiteContextMixin, ListView):
    template_name = "agency/contact_list.html"
    context_object_name = "employees"

    def get_queryset(self):
        return employee_profiles_queryset()


class PrivacyView(SiteContextMixin, TemplateView):
    template_name = "agency/privacy.html"


class TestView(SiteContextMixin, TemplateView):
    template_name = "agency/test.html"


class VacancyListView(SiteContextMixin, ListView):
    template_name = "agency/vacancy_list.html"
    context_object_name = "vacancies"

    def get_queryset(self):
        return Vacancy.objects.filter(is_active=True)


class ReviewListView(SiteContextMixin, ListView):
    template_name = "agency/review_list.html"
    context_object_name = "reviews"
    queryset = Review.objects.filter(approved=True).select_related("author")


class PromoListView(SiteContextMixin, TemplateView):
    template_name = "agency/promo_list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        promos = PromoCode.objects.all()
        context.update(
            {
                "active_promos": [promo for promo in promos if promo.is_current],
                "archived_promos": [promo for promo in promos if not promo.is_current],
            }
        )
        return context


class ReviewCreateView(LoginRequiredMixin, SiteContextMixin, CreateView):
    template_name = "agency/review_form.html"
    form_class = ReviewForm
    success_url = reverse_lazy("realty:reviews")

    def form_valid(self, form):
        form.instance.author = self.request.user
        messages.success(self.request, "Отзыв сохранён.")
        logger.info("Review created by user=%s", self.request.user.username)
        return super().form_valid(form)


class RegisterView(SiteContextMixin, CreateView):
    template_name = "registration/register.html"
    form_class = SignUpForm
    success_url = reverse_lazy("realty:dashboard")

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect("realty:dashboard")
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        response = super().form_valid(form)
        login(self.request, self.object)
        messages.success(self.request, "Регистрация завершена. Добро пожаловать!")
        logger.info("User registered: %s", self.object.username)
        return response


class DashboardView(LoginRequiredMixin, SiteContextMixin, TemplateView):
    template_name = "agency/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        profile = self.request.user.profile
        deals = Deal.objects.select_related(
            "property",
            "client__user",
            "manager__user",
            "promo_code",
        )
        properties = Property.objects.select_related("property_type", "owner").prefetch_related(
            "agents"
        )

        if self.request.user.is_superuser:
            scoped_deals = deals
            scoped_properties = properties
        elif profile.role == UserProfile.ROLE_EMPLOYEE:
            scoped_deals = deals.filter(Q(manager=profile) | Q(property__agents=profile)).distinct()
            scoped_properties = properties.filter(agents=profile).distinct()
        else:
            scoped_deals = deals.filter(client=profile)
            scoped_properties = properties.filter(deals__client=profile).distinct()
        scoped_deals_list = list(scoped_deals)

        exchange_rates = None
        api_errors = []
        try:
            exchange_rates = fetch_exchange_rates()
        except ExternalAPIError as exc:
            api_errors.append(f"Курсы валют временно недоступны: {exc}")

        context.update(
            {
                "profile": profile,
                "deals": scoped_deals_list[:8],
                "properties": scoped_properties[:6],
                "exchange_rates": exchange_rates,
                "api_errors": api_errors,
                "property_type_chart_uri": render_property_type_chart(
                    collect_property_type_stats(scoped_deals_list)
                ),
            }
        )
        return context


class PropertyListView(SiteContextMixin, ListView):
    template_name = "agency/property_list.html"
    context_object_name = "properties"
    paginate_by = 8

    def get_queryset(self):
        queryset = (
            Property.objects.select_related("property_type", "owner")
            .prefetch_related("agents", "amenities")
            .all()
        )
        profile = getattr(self.request.user, "profile", None)
        if not self.request.user.is_authenticated or (profile and profile.role == UserProfile.ROLE_CLIENT):
            queryset = queryset.exclude(status__in=[Property.STATUS_SOLD, Property.STATUS_RENTED])

        query = self.request.GET.get("q", "").strip()
        property_type = self.request.GET.get("property_type", "").strip()
        deal_kind = self.request.GET.get("deal_kind", "").strip()
        min_price = self.request.GET.get("min_price", "").strip()
        max_price = self.request.GET.get("max_price", "").strip()
        sort = self.request.GET.get("sort", "-published_at")

        if query:
            queryset = queryset.filter(
                Q(title__icontains=query)
                | Q(city__icontains=query)
                | Q(address__icontains=query)
                | Q(description__icontains=query)
                | Q(property_type__name__icontains=query)
                | Q(owner__full_name__icontains=query)
            )
        if property_type:
            queryset = queryset.filter(property_type_id=property_type)
        if deal_kind:
            queryset = queryset.filter(deal_kind=deal_kind)
        if min_price:
            queryset = queryset.filter(price__gte=min_price)
        if max_price:
            queryset = queryset.filter(price__lte=max_price)

        sort_map = {
            "price": "price",
            "-price": "-price",
            "rooms": "rooms",
            "-rooms": "-rooms",
            "area": "area_sqm",
            "-area": "-area_sqm",
            "city": "city",
            "-published_at": "-published_at",
        }
        return queryset.order_by(sort_map.get(sort, "-published_at"))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "property_types": PropertyType.objects.all(),
                "current_filters": self.request.GET,
            }
        )
        return context


class PropertyDetailView(SiteContextMixin, DetailView):
    template_name = "agency/property_detail.html"
    context_object_name = "property"
    slug_field = "slug"
    slug_url_kwarg = "slug"
    queryset = Property.objects.select_related("property_type", "owner").prefetch_related(
        "agents",
        "amenities",
    )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        property_obj = self.object
        geocode = None
        weather = None
        exchange_rates = None
        price_conversions = {}
        api_errors = []

        try:
            geocode = geocode_address(f"{property_obj.city}, {property_obj.address}")
            if geocode:
                weather = fetch_weather(geocode["lat"], geocode["lon"])
        except ExternalAPIError as exc:
            api_errors.append(f"Адрес или погода временно недоступны: {exc}")

        try:
            exchange_rates = fetch_exchange_rates()
            for code, payload in exchange_rates.items():
                price_conversions[code] = (
                    property_obj.price / payload["rate"] * Decimal(payload["scale"])
                ).quantize(Decimal("0.01"))
        except ExternalAPIError as exc:
            api_errors.append(f"Курсы валют временно недоступны: {exc}")

        context.update(
            {
                "geocode": geocode,
                "weather": weather,
                "exchange_rates": exchange_rates,
                "price_conversions": price_conversions,
                "api_errors": api_errors,
                "in_cart": str(property_obj.pk) in self.request.session.get("cart", {}),
            }
        )
        return context


class PropertyCartAddView(View):
    def post(self, request, slug, *args, **kwargs):
        property_obj = get_object_or_404(Property, slug=slug)
        cart = request.session.get("cart", {})
        key = str(property_obj.pk)
        cart[key] = cart.get(key, 0) + 1
        request.session["cart"] = cart
        messages.success(request, "Объект добавлен в корзину.")
        return redirect("realty:cart")


class PropertyCreateView(EmployeeRequiredMixin, SiteContextMixin, CreateView):
    template_name = "agency/property_form.html"
    form_class = PropertyForm

    def form_valid(self, form):
        response = super().form_valid(form)
        logger.info("Property created: %s", self.object.title)
        messages.success(self.request, "Объект недвижимости создан.")
        return response


class PropertyUpdateView(EmployeeRequiredMixin, SiteContextMixin, UpdateView):
    template_name = "agency/property_form.html"
    form_class = PropertyForm
    model = Property
    slug_field = "slug"
    slug_url_kwarg = "slug"

    def get_queryset(self):
        queryset = Property.objects.all()
        if self.request.user.is_superuser:
            return queryset
        return queryset.filter(agents=self.request.user.profile)

    def form_valid(self, form):
        response = super().form_valid(form)
        logger.info("Property updated: %s", self.object.title)
        messages.success(self.request, "Объект недвижимости обновлён.")
        return response


class PropertyDeleteView(EmployeeRequiredMixin, SiteContextMixin, DeleteView):
    template_name = "agency/confirm_delete.html"
    model = Property
    slug_field = "slug"
    slug_url_kwarg = "slug"
    success_url = reverse_lazy("realty:property-list")

    def get_queryset(self):
        queryset = Property.objects.all()
        if self.request.user.is_superuser:
            return queryset
        return queryset.filter(agents=self.request.user.profile)

    def form_valid(self, form):
        logger.info("Property deleted by user=%s slug=%s", self.request.user.username, self.object.slug)
        messages.success(self.request, "Объект недвижимости удалён.")
        return super().form_valid(form)


class CartView(SiteContextMixin, TemplateView):
    template_name = "agency/cart.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        cart = self.request.session.get("cart", {})
        property_ids = [int(pk) for pk in cart.keys()]
        properties = Property.objects.filter(pk__in=property_ids).select_related("property_type", "owner")
        items = []
        total = Decimal("0.00")
        for property_obj in properties:
            quantity = int(cart.get(str(property_obj.pk), 0))
            subtotal = property_obj.price * quantity
            total += subtotal
            items.append(
                {
                    "property": property_obj,
                    "quantity": quantity,
                    "subtotal": subtotal,
                }
            )
        context.update({"cart_items": items, "cart_total": total})
        return context


class CartUpdateView(View):
    def post(self, request, pk, *args, **kwargs):
        get_object_or_404(Property, pk=pk)
        action = request.POST.get("action")
        cart = request.session.get("cart", {})
        key = str(pk)
        quantity = int(cart.get(key, 0))

        if action == "increase":
            cart[key] = quantity + 1 if quantity else 1
        elif action == "decrease":
            if quantity > 1:
                cart[key] = quantity - 1
            else:
                cart.pop(key, None)
        elif action == "remove":
            cart.pop(key, None)

        request.session["cart"] = cart
        return redirect("realty:cart")


class PaymentView(SiteContextMixin, TemplateView):
    template_name = "agency/payment.html"

    def dispatch(self, request, *args, **kwargs):
        if not request.session.get("cart"):
            messages.info(request, "Корзина пуста.")
            return redirect("realty:cart")
        return super().dispatch(request, *args, **kwargs)

    def get_form(self):
        if self.request.method == "POST":
            return PaymentForm(self.request.POST)
        initial = {}
        if self.request.user.is_authenticated:
            initial["full_name"] = self.request.user.get_full_name() or self.request.user.username
            initial["email"] = self.request.user.email
            if hasattr(self.request.user, "profile"):
                initial["phone"] = self.request.user.profile.phone
        return PaymentForm(initial=initial)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        cart = self.request.session.get("cart", {})
        property_ids = [int(pk) for pk in cart.keys()]
        properties = Property.objects.filter(pk__in=property_ids)
        total = Decimal("0.00")
        items = []
        for property_obj in properties:
            quantity = int(cart.get(str(property_obj.pk), 0))
            subtotal = property_obj.price * quantity
            total += subtotal
            items.append({"property": property_obj, "quantity": quantity, "subtotal": subtotal})
        context.update(
            {
                "form": kwargs.get("form") or self.get_form(),
                "cart_items": items,
                "cart_total": total,
                "payment_success": kwargs.get("payment_success", False),
            }
        )
        return context

    def post(self, request, *args, **kwargs):
        form = self.get_form()
        if form.is_valid():
            payment_data = {}
            for key, value in form.cleaned_data.items():
                payment_data[key] = value.isoformat() if hasattr(value, "isoformat") else value
            request.session["last_payment"] = payment_data
            request.session["cart"] = {}
            messages.success(request, "Оплата оформлена.")
            return self.render_to_response(self.get_context_data(payment_success=True, form=PaymentForm()))
        return self.render_to_response(self.get_context_data(form=form))


class DealListView(LoginRequiredMixin, SiteContextMixin, ListView):
    template_name = "agency/deal_list.html"
    context_object_name = "deals"
    paginate_by = 10

    def get_queryset(self):
        queryset = Deal.objects.select_related(
            "property__property_type",
            "client__user",
            "manager__user",
            "promo_code",
        )
        profile = self.request.user.profile
        if self.request.user.is_superuser:
            scoped = queryset
        elif profile.role == UserProfile.ROLE_EMPLOYEE:
            scoped = queryset.filter(Q(manager=profile) | Q(property__agents=profile)).distinct()
        else:
            scoped = queryset.filter(client=profile)

        query = self.request.GET.get("q", "").strip()
        sort = self.request.GET.get("sort", "-agreement_date")
        if query:
            scoped = scoped.filter(
                Q(property__title__icontains=query)
                | Q(client__user__first_name__icontains=query)
                | Q(client__user__last_name__icontains=query)
                | Q(manager__user__first_name__icontains=query)
                | Q(manager__user__last_name__icontains=query)
                | Q(status__icontains=query)
            )

        sort_map = {
            "amount": "amount",
            "-amount": "-amount",
            "status": "status",
            "-agreement_date": "-agreement_date",
            "agreement_date": "agreement_date",
        }
        return scoped.order_by(sort_map.get(sort, "-agreement_date"))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["current_filters"] = self.request.GET
        return context


class DealDetailView(LoginRequiredMixin, SiteContextMixin, DetailView):
    template_name = "agency/deal_detail.html"
    context_object_name = "deal"

    def get_queryset(self):
        queryset = Deal.objects.select_related(
            "property__property_type",
            "client__user",
            "manager__user",
            "promo_code",
        )
        profile = self.request.user.profile
        if self.request.user.is_superuser:
            return queryset
        if profile.role == UserProfile.ROLE_EMPLOYEE:
            return queryset.filter(Q(manager=profile) | Q(property__agents=profile)).distinct()
        return queryset.filter(client=profile)


class DealCreateView(EmployeeRequiredMixin, SiteContextMixin, CreateView):
    template_name = "agency/deal_form.html"
    form_class = DealForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        response = super().form_valid(form)
        logger.info("Deal created: id=%s", self.object.pk)
        messages.success(self.request, "Сделка сохранена.")
        return response


class DealUpdateView(EmployeeRequiredMixin, SiteContextMixin, UpdateView):
    template_name = "agency/deal_form.html"
    form_class = DealForm
    model = Deal

    def get_queryset(self):
        queryset = Deal.objects.all()
        if self.request.user.is_superuser:
            return queryset
        return queryset.filter(manager=self.request.user.profile)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        response = super().form_valid(form)
        logger.info("Deal updated: id=%s", self.object.pk)
        messages.success(self.request, "Сделка обновлена.")
        return response


class DealDeleteView(EmployeeRequiredMixin, SiteContextMixin, DeleteView):
    template_name = "agency/confirm_delete.html"
    model = Deal
    success_url = reverse_lazy("realty:deal-list")

    def get_queryset(self):
        queryset = Deal.objects.all()
        if self.request.user.is_superuser:
            return queryset
        return queryset.filter(manager=self.request.user.profile)

    def form_valid(self, form):
        logger.info("Deal deleted by user=%s id=%s", self.request.user.username, self.object.pk)
        messages.success(self.request, "Сделка удалена.")
        return super().form_valid(form)


class AnalyticsView(LoginRequiredMixin, SiteContextMixin, TemplateView):
    template_name = "agency/analytics.html"

    def get_scoped_deals(self):
        queryset = Deal.objects.select_related("property__property_type", "client__user", "manager__user")
        profile = self.request.user.profile
        if self.request.user.is_superuser:
            return queryset
        if profile.role == UserProfile.ROLE_EMPLOYEE:
            return queryset.filter(Q(manager=profile) | Q(property__agents=profile)).distinct()
        return queryset.filter(client=profile)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        deals = list(self.get_scoped_deals())
        amounts = [float(deal.amount) for deal in deals]
        total_amount = sum((deal.amount for deal in deals), Decimal("0.00"))

        average_amount = round(mean(amounts), 2) if amounts else 0
        median_amount = round(median(amounts), 2) if amounts else 0
        try:
            mode_amount = round(mode(amounts), 2) if amounts else 0
        except StatisticsError:
            mode_amount = "нет уникальной моды"

        sorted_types = collect_property_type_stats(deals)

        popular_type = sorted_types[0][0] if sorted_types else "нет данных"
        profitable_type = (
            max(sorted_types, key=lambda item: item[1]["total"])[0] if sorted_types else "нет данных"
        )

        client_list = (
            UserProfile.objects.filter(role=UserProfile.ROLE_CLIENT)
            .select_related("user")
            .order_by("user__last_name", "user__first_name")
        )
        if not (self.request.user.is_superuser or self.request.user.profile.role == UserProfile.ROLE_EMPLOYEE):
            client_list = client_list.filter(pk=self.request.user.profile.pk)

        context.update(
            {
                "deals": deals,
                "alphabetical_clients": client_list[:20],
                "total_amount": total_amount,
                "average_amount": average_amount,
                "median_amount": median_amount,
                "mode_amount": mode_amount,
                "popular_type": popular_type,
                "profitable_type": profitable_type,
                "property_type_chart_uri": render_property_type_chart(sorted_types),
                "status_summary": self.get_scoped_deals().values("status").annotate(total=Count("id")),
            }
        )
        return context


class PropertySummaryApiView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        data = list(
            PropertyType.objects.annotate(total=Count("properties")).values("name", "total").order_by("name")
        )
        return JsonResponse({"results": data})


class DealStatsApiView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        profile = request.user.profile
        queryset = Deal.objects.all()
        if not request.user.is_superuser:
            if profile.role == UserProfile.ROLE_EMPLOYEE:
                queryset = queryset.filter(Q(manager=profile) | Q(property__agents=profile)).distinct()
            else:
                queryset = queryset.filter(client=profile)
        aggregate = queryset.aggregate(
            total_amount=Sum("amount"),
            total_count=Count("id"),
            average_amount=Avg("amount"),
        )
        return JsonResponse(
            {
                "total_count": aggregate["total_count"] or 0,
                "total_amount": str(aggregate["total_amount"] or Decimal("0.00")),
                "average_amount": str(aggregate["average_amount"] or Decimal("0.00")),
            }
        )
