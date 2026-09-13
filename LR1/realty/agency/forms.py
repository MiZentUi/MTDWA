from datetime import date

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import (
    Deal,
    Property,
    Review,
    UserProfile,
    client_profiles_queryset,
    employee_profiles_queryset,
)
from .timezones import get_default_timezone_name, get_timezone_choices
from .validators import PHONE_PATTERN, validate_adult


class DateInput(forms.DateInput):
    input_type = "date"


class SignUpForm(UserCreationForm):
    first_name = forms.CharField(max_length=150, label="Имя")
    last_name = forms.CharField(max_length=150, label="Фамилия")
    email = forms.EmailField(label="Email")
    phone = forms.RegexField(
        regex=PHONE_PATTERN,
        label="Телефон",
        help_text="Формат: +375 (29) XXX-XX-XX",
    )
    birth_date = forms.DateField(label="Дата рождения", widget=DateInput())
    timezone = forms.ChoiceField(
        choices=get_timezone_choices,
        initial=get_default_timezone_name,
        label="Часовой пояс",
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = (
            "username",
            "first_name",
            "last_name",
            "email",
            "phone",
            "birth_date",
            "timezone",
            "password1",
            "password2",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        today = date.today()
        adult_border = date(today.year - 18, today.month, today.day)
        self.fields["birth_date"].widget.attrs["max"] = adult_border.isoformat()

    def clean_birth_date(self):
        birth_date = self.cleaned_data["birth_date"]
        validate_adult(birth_date)
        return birth_date

    def save(self, commit=True):
        user = super().save(commit=False)
        user.first_name = self.cleaned_data["first_name"]
        user.last_name = self.cleaned_data["last_name"]
        user.email = self.cleaned_data["email"]
        if commit:
            user.save()
            profile = user.profile
            profile.phone = self.cleaned_data["phone"]
            profile.birth_date = self.cleaned_data["birth_date"]
            profile.timezone = self.cleaned_data["timezone"]
            profile.role = UserProfile.ROLE_CLIENT
            profile.save()
        return user


class PropertyForm(forms.ModelForm):
    class Meta:
        model = Property
        fields = (
            "title",
            "property_type",
            "owner",
            "agents",
            "amenities",
            "deal_kind",
            "status",
            "city",
            "address",
            "description",
            "rooms",
            "area_sqm",
            "price",
        )
        widgets = {
            "agents": forms.CheckboxSelectMultiple(),
            "amenities": forms.CheckboxSelectMultiple(),
            "description": forms.Textarea(attrs={"rows": 5}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["agents"].queryset = employee_profiles_queryset()
        for name in ("rooms", "area_sqm", "price"):
            self.fields[name].widget.attrs["min"] = "1"


class DealForm(forms.ModelForm):
    class Meta:
        model = Deal
        fields = (
            "property",
            "client",
            "manager",
            "promo_code",
            "status",
            "amount",
            "commission_percent",
            "agreement_date",
            "closing_date",
            "notes",
        )
        widgets = {
            "agreement_date": DateInput(),
            "closing_date": DateInput(),
            "notes": forms.Textarea(attrs={"rows": 4}),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["client"].queryset = client_profiles_queryset()
        self.fields["manager"].queryset = employee_profiles_queryset()
        self.fields["property"].queryset = Property.objects.select_related(
            "property_type",
            "owner",
        ).prefetch_related("agents")
        if user and hasattr(user, "profile") and user.profile.role == UserProfile.ROLE_EMPLOYEE:
            self.fields["manager"].queryset = employee_profiles_queryset().filter(pk=user.profile.pk)
            self.fields["manager"].initial = user.profile


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ("rating", "text")
        widgets = {
            "text": forms.Textarea(attrs={"rows": 5, "maxlength": "1000"}),
        }


class PaymentForm(forms.Form):
    full_name = forms.CharField(max_length=255, label="ФИО плательщика")
    email = forms.EmailField(label="Email")
    phone = forms.RegexField(
        regex=PHONE_PATTERN,
        label="Телефон",
        help_text="Формат: +375 (29) XXX-XX-XX",
    )
    delivery_date = forms.DateField(label="Дата оплаты", widget=DateInput())
    payment_method = forms.ChoiceField(
        label="Способ оплаты",
        choices=(
            ("card", "Банковская карта"),
            ("invoice", "Безналичный расчёт"),
            ("cash", "Наличный расчёт"),
        ),
    )
    promo_code = forms.CharField(max_length=30, label="Промокод", required=False)
    contact_time = forms.TimeField(label="Время для связи", required=False)
    need_call = forms.BooleanField(label="Перезвонить для подтверждения", required=False)
    agree_terms = forms.BooleanField(label="Согласие на обработку данных")
    comment = forms.CharField(
        label="Комментарий к заказу",
        required=False,
        widget=forms.Textarea(attrs={"rows": 4, "maxlength": "500"}),
    )
