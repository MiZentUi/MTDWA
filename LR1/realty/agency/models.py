from builtins import property as builtin_property
from decimal import Decimal

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Q
from django.template.defaultfilters import slugify
from django.urls import reverse
from django.utils import timezone

from .timezones import get_default_timezone_name, get_timezone_choices
from .validators import phone_validator, validate_adult


CYRILLIC_TO_LATIN = str.maketrans(
    {
        "а": "a",
        "б": "b",
        "в": "v",
        "г": "g",
        "д": "d",
        "е": "e",
        "ё": "e",
        "ж": "zh",
        "з": "z",
        "и": "i",
        "й": "y",
        "к": "k",
        "л": "l",
        "м": "m",
        "н": "n",
        "о": "o",
        "п": "p",
        "р": "r",
        "с": "s",
        "т": "t",
        "у": "u",
        "ф": "f",
        "х": "h",
        "ц": "ts",
        "ч": "ch",
        "ш": "sh",
        "щ": "sch",
        "ъ": "",
        "ы": "y",
        "ь": "",
        "э": "e",
        "ю": "yu",
        "я": "ya",
    }
)


def transliterated_slug(value: str) -> str:
    return slugify(value.lower().translate(CYRILLIC_TO_LATIN))


class UserProfile(models.Model):
    ROLE_SUPERUSER = "superuser"
    ROLE_EMPLOYEE = "employee"
    ROLE_CLIENT = "client"
    ROLE_CHOICES = (
        (ROLE_SUPERUSER, "Superuser"),
        (ROLE_EMPLOYEE, "Сотрудник"),
        (ROLE_CLIENT, "Клиент"),
    )
    TIMEZONE_CHOICES = get_timezone_choices

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=ROLE_CLIENT)
    phone = models.CharField(max_length=19, validators=[phone_validator])
    birth_date = models.DateField(validators=[validate_adult])
    timezone = models.CharField(
        max_length=64,
        choices=TIMEZONE_CHOICES,
        default=get_default_timezone_name,
    )
    photo_url = models.URLField(blank=True)
    position = models.CharField(max_length=120, blank=True)
    responsibilities = models.TextField(blank=True)
    bio = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("user__last_name", "user__first_name", "user__username")
        verbose_name = "Профиль пользователя"
        verbose_name_plural = "Профили пользователей"

    def __str__(self):
        return self.full_name

    @property
    def full_name(self):
        full_name = self.user.get_full_name().strip()
        return full_name or self.user.username

    @property
    def is_employee(self):
        return self.role in {self.ROLE_EMPLOYEE, self.ROLE_SUPERUSER}

    @property
    def is_client(self):
        return self.role == self.ROLE_CLIENT


class CompanyInfo(models.Model):
    company_name = models.CharField(max_length=255)
    slogan = models.CharField(max_length=255, blank=True)
    about_text = models.TextField()
    history = models.TextField(blank=True)
    requisites = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Информация о компании"
        verbose_name_plural = "Информация о компании"

    def __str__(self):
        return self.company_name


class NewsArticle(models.Model):
    title = models.CharField(max_length=200)
    summary = models.CharField(max_length=255)
    body = models.TextField()
    image_url = models.URLField(blank=True)
    published_at = models.DateTimeField(default=timezone.now)
    is_published = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-published_at", "-created_at")
        verbose_name = "Новость"
        verbose_name_plural = "Новости"

    def __str__(self):
        return self.title


class FAQEntry(models.Model):
    question = models.CharField(max_length=255)
    answer = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("question",)
        verbose_name = "Термин/вопрос"
        verbose_name_plural = "Словарь терминов и вопросов"

    def __str__(self):
        return self.question


class PropertyType(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ("name",)
        verbose_name = "Вид недвижимости"
        verbose_name_plural = "Виды недвижимости"

    def __str__(self):
        return self.name


class Amenity(models.Model):
    name = models.CharField(max_length=100, unique=True)

    class Meta:
        ordering = ("name",)
        verbose_name = "Удобство"
        verbose_name_plural = "Удобства"

    def __str__(self):
        return self.name


class Owner(models.Model):
    full_name = models.CharField(max_length=255)
    phone = models.CharField(max_length=19, validators=[phone_validator])
    email = models.EmailField()
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("full_name",)
        verbose_name = "Владелец"
        verbose_name_plural = "Владельцы"

    def __str__(self):
        return self.full_name


class Property(models.Model):
    DEAL_SALE = "sale"
    DEAL_RENT = "rent"
    DEAL_KIND_CHOICES = (
        (DEAL_SALE, "Продажа"),
        (DEAL_RENT, "Аренда"),
    )

    STATUS_AVAILABLE = "available"
    STATUS_RESERVED = "reserved"
    STATUS_SOLD = "sold"
    STATUS_RENTED = "rented"
    STATUS_CHOICES = (
        (STATUS_AVAILABLE, "Доступен"),
        (STATUS_RESERVED, "Забронирован"),
        (STATUS_SOLD, "Продан"),
        (STATUS_RENTED, "Сдан"),
    )

    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    property_type = models.ForeignKey(
        PropertyType,
        on_delete=models.PROTECT,
        related_name="properties",
    )
    owner = models.ForeignKey(Owner, on_delete=models.PROTECT, related_name="properties")
    agents = models.ManyToManyField(UserProfile, related_name="properties", blank=True)
    amenities = models.ManyToManyField(Amenity, related_name="properties", blank=True)
    deal_kind = models.CharField(max_length=10, choices=DEAL_KIND_CHOICES)
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default=STATUS_AVAILABLE,
    )
    city = models.CharField(max_length=100)
    address = models.CharField(max_length=255)
    description = models.TextField()
    rooms = models.PositiveSmallIntegerField(validators=[MinValueValidator(1)])
    area_sqm = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("10.00"))],
    )
    price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("1.00"))],
    )
    published_at = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-published_at", "title")
        verbose_name = "Объект недвижимости"
        verbose_name_plural = "Объекты недвижимости"

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("realty:property-detail", kwargs={"slug": self.slug})

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = transliterated_slug(f"{self.title}-{self.city}")[:200] or "property"
            slug = base_slug
            index = 1
            while Property.objects.exclude(pk=self.pk).filter(slug=slug).exists():
                index += 1
                slug = f"{base_slug[:190]}-{index}"
            self.slug = slug
        super().save(*args, **kwargs)


class PromoCode(models.Model):
    code = models.CharField(max_length=30, unique=True)
    description = models.CharField(max_length=255)
    discount_percent = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(100)]
    )
    starts_at = models.DateField()
    ends_at = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-ends_at", "code")
        verbose_name = "Промокод"
        verbose_name_plural = "Промокоды"

    def __str__(self):
        return self.code

    @property
    def is_current(self):
        today = timezone.localdate()
        return self.starts_at <= today <= self.ends_at


class Deal(models.Model):
    STATUS_NEW = "new"
    STATUS_IN_PROGRESS = "in_progress"
    STATUS_CLOSED = "closed"
    STATUS_CANCELLED = "cancelled"
    STATUS_CHOICES = (
        (STATUS_NEW, "Новая"),
        (STATUS_IN_PROGRESS, "В работе"),
        (STATUS_CLOSED, "Закрыта"),
        (STATUS_CANCELLED, "Отменена"),
    )

    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name="deals")
    client = models.ForeignKey(
        UserProfile,
        on_delete=models.PROTECT,
        related_name="client_deals",
    )
    manager = models.ForeignKey(
        UserProfile,
        on_delete=models.PROTECT,
        related_name="managed_deals",
    )
    promo_code = models.ForeignKey(
        PromoCode,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="deals",
    )
    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default=STATUS_NEW)
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("1.00"))],
    )
    commission_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal("3.00"),
        validators=[MinValueValidator(Decimal("0.00")), MaxValueValidator(Decimal("100.00"))],
    )
    agreement_date = models.DateField(default=timezone.localdate)
    closing_date = models.DateField(blank=True, null=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-agreement_date", "-created_at")
        verbose_name = "Сделка"
        verbose_name_plural = "Сделки"

    def __str__(self):
        return f"{self.property.title} - {self.client.full_name}"

    def clean(self):
        errors = {}
        if self.client_id and not self.client.is_client:
            errors["client"] = "Клиентом сделки может быть только пользователь с ролью клиента."
        if self.manager_id and not self.manager.is_employee:
            errors["manager"] = "Менеджером сделки может быть сотрудник или superuser."
        if self.closing_date and self.closing_date < self.agreement_date:
            errors["closing_date"] = "Дата закрытия не может быть раньше даты договора."
        if self.property_id and self.status in {self.STATUS_NEW, self.STATUS_IN_PROGRESS}:
            if self.property.status in {Property.STATUS_SOLD, Property.STATUS_RENTED}:
                errors["property"] = "Нельзя открыть сделку по уже закрытому объекту."
        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        if not self.amount:
            self.amount = self.property.price
        super().save(*args, **kwargs)
        if self.status == self.STATUS_CLOSED:
            next_status = (
                Property.STATUS_SOLD
                if self.property.deal_kind == Property.DEAL_SALE
                else Property.STATUS_RENTED
            )
            if self.property.status != next_status:
                self.property.status = next_status
                self.property.save(update_fields=["status"])

    def get_absolute_url(self):
        return reverse("realty:deal-detail", kwargs={"pk": self.pk})

    @builtin_property
    def total_with_commission(self):
        commission = self.amount * self.commission_percent / Decimal("100")
        return self.amount + commission

    @builtin_property
    def discount_amount(self):
        if not self.promo_code:
            return Decimal("0.00")
        return self.amount * Decimal(self.promo_code.discount_percent) / Decimal("100")


class Vacancy(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    salary_from = models.PositiveIntegerField(blank=True, null=True)
    salary_to = models.PositiveIntegerField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    published_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ("-published_at", "title")
        verbose_name = "Вакансия"
        verbose_name_plural = "Вакансии"

    def __str__(self):
        return self.title


class Review(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name="reviews")
    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    text = models.TextField()
    approved = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-created_at",)
        verbose_name = "Отзыв"
        verbose_name_plural = "Отзывы"

    def __str__(self):
        return f"{self.author.username}: {self.rating}"


def employee_profiles_queryset():
    return UserProfile.objects.filter(
        Q(role=UserProfile.ROLE_EMPLOYEE) | Q(role=UserProfile.ROLE_SUPERUSER)
    ).select_related("user")


def client_profiles_queryset():
    return UserProfile.objects.filter(role=UserProfile.ROLE_CLIENT).select_related("user")
