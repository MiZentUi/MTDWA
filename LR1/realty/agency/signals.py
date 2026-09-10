from datetime import date

from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import UserProfile


@receiver(post_save, sender=User)
def create_or_update_profile(sender, instance, created, **kwargs):
    default_role = (
        UserProfile.ROLE_SUPERUSER if instance.is_superuser else UserProfile.ROLE_CLIENT
    )
    if created:
        UserProfile.objects.create(
            user=instance,
            role=default_role,
            phone="+375 (29) 000-00-00",
            birth_date=date(1990, 1, 1),
        )
        return

    profile = getattr(instance, "profile", None)
    if profile and instance.is_superuser and profile.role != UserProfile.ROLE_SUPERUSER:
        profile.role = UserProfile.ROLE_SUPERUSER
        profile.save(update_fields=["role", "updated_at"])
