from django.contrib import admin

from .models import (
    Amenity,
    CompanyInfo,
    Deal,
    FAQEntry,
    NewsArticle,
    Owner,
    PromoCode,
    Property,
    PropertyType,
    Review,
    UserProfile,
    Vacancy,
)


class DealInline(admin.TabularInline):
    model = Deal
    extra = 0
    autocomplete_fields = ("client", "manager", "promo_code")


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("full_name", "role", "phone", "timezone", "updated_at")
    list_filter = ("role", "timezone")
    search_fields = ("user__username", "user__first_name", "user__last_name", "phone")


@admin.register(CompanyInfo)
class CompanyInfoAdmin(admin.ModelAdmin):
    list_display = ("company_name", "updated_at")


@admin.register(NewsArticle)
class NewsArticleAdmin(admin.ModelAdmin):
    list_display = ("title", "published_at", "is_published")
    list_filter = ("is_published",)
    search_fields = ("title", "summary", "body")


@admin.register(FAQEntry)
class FAQEntryAdmin(admin.ModelAdmin):
    list_display = ("question", "created_at")
    search_fields = ("question", "answer")


@admin.register(PropertyType)
class PropertyTypeAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


@admin.register(Amenity)
class AmenityAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


@admin.register(Owner)
class OwnerAdmin(admin.ModelAdmin):
    list_display = ("full_name", "phone", "email")
    search_fields = ("full_name", "phone", "email")


@admin.register(Property)
class PropertyAdmin(admin.ModelAdmin):
    list_display = ("title", "property_type", "city", "deal_kind", "status", "price")
    list_filter = ("property_type", "deal_kind", "status", "city")
    search_fields = ("title", "city", "address", "owner__full_name")
    prepopulated_fields = {"slug": ("title",)}
    filter_horizontal = ("agents", "amenities")
    inlines = (DealInline,)


@admin.register(PromoCode)
class PromoCodeAdmin(admin.ModelAdmin):
    list_display = ("code", "discount_percent", "starts_at", "ends_at")
    list_filter = ("starts_at", "ends_at")
    search_fields = ("code", "description")


@admin.register(Deal)
class DealAdmin(admin.ModelAdmin):
    list_display = ("property", "client", "manager", "status", "amount", "agreement_date")
    list_filter = ("status", "agreement_date")
    search_fields = (
        "property__title",
        "client__user__first_name",
        "client__user__last_name",
        "manager__user__first_name",
        "manager__user__last_name",
    )
    autocomplete_fields = ("property", "client", "manager", "promo_code")


@admin.register(Vacancy)
class VacancyAdmin(admin.ModelAdmin):
    list_display = ("title", "salary_from", "salary_to", "is_active")
    list_filter = ("is_active",)
    search_fields = ("title", "description")


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ("author", "rating", "approved", "created_at")
    list_filter = ("approved", "rating")
    search_fields = ("author__username", "text")


admin.site.site_header = "Администрирование realty"
admin.site.site_title = "realty"
