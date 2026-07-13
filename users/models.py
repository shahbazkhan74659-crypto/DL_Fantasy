from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Custom user model so future non-admin accounts don't require a data migration."""
    google_sub = models.CharField(
        max_length=255, blank=True, null=True, unique=True,
        help_text="Google's stable per-account ID ('sub' claim) — the real link to a Google "
                   "Sign-In identity, since email addresses can change but this doesn't.",
    )
    google_picture_url = models.URLField(
        blank=True, null=True,
        help_text='Refreshed from the Google ID token on every Google Sign-In.',
    )


class LoginHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='login_history')
    timestamp = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        ordering = ['-timestamp']
        indexes = [models.Index(fields=['user', 'timestamp'], name='loginhistory_user_ts_idx')]

    def __str__(self):
        return f"{self.user} @ {self.timestamp:%Y-%m-%d %H:%M}"


class VisitSession(models.Model):
    """One row per distinct visit — a burst of activity by a user, separated from the next one by
    a gap of inactivity (see TrackVisitSessionsMiddleware.SESSION_GAP) or a calendar-day rollover.
    Visit count and time-on-site per day are both derived from these rows at query time (count of
    rows for a date, and sum of last_seen_at - started_at), rather than stored as a running total,
    so there's no risk of a stale aggregate drifting from reality.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='visit_sessions')
    date = models.DateField()
    started_at = models.DateTimeField()
    last_seen_at = models.DateTimeField()

    class Meta:
        ordering = ['-started_at']
        indexes = [models.Index(fields=['user', 'date'], name='visitsession_user_date_idx')]

    def __str__(self):
        return f"{self.user} @ {self.date}"
