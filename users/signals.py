from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver

from .models import LoginHistory


@receiver(user_logged_in)
def record_login(sender, request, user, **kwargs):
    LoginHistory.objects.create(
        user=user,
        ip_address=request.META.get('REMOTE_ADDR') if request else None,
    )
