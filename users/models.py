from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Custom user model so future non-admin accounts don't require a data migration."""
    pass


class LoginHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='login_history')
    timestamp = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        ordering = ['-timestamp']
        indexes = [models.Index(fields=['user', 'timestamp'], name='loginhistory_user_ts_idx')]

    def __str__(self):
        return f"{self.user} @ {self.timestamp:%Y-%m-%d %H:%M}"


class DailyVisit(models.Model):
    """One row per user per calendar day they visited the site, deduped regardless of session length."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='daily_visits')
    date = models.DateField()

    class Meta:
        ordering = ['-date']
        constraints = [models.UniqueConstraint(fields=['user', 'date'], name='unique_user_visit_per_day')]

    def __str__(self):
        return f"{self.user} @ {self.date}"
