from datetime import date

from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator


PHONE_PATTERN = r"^\+375 \(29\) \d{3}-\d{2}-\d{2}$"

phone_validator = RegexValidator(
    regex=PHONE_PATTERN,
    message="Номер телефона должен быть в формате +375 (29) XXX-XX-XX.",
)


def validate_adult(value: date):
    today = date.today()
    age = today.year - value.year - ((today.month, today.day) < (value.month, value.day))
    if age < 18:
        raise ValidationError("Возраст должен быть не менее 18 лет.")
