from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.db import models

username_validator = RegexValidator(
    regex=r'^[\w.@+\- ]+$',
    message='Only letters, digits, spaces, and @/./+/-/_ are allowed.',
)


class User(AbstractUser):
    """Custom user model so future non-admin accounts don't require a data migration.

    Overrides AbstractUser's `username` only to relax its validator to also allow spaces (e.g.
    "Shahbaz Khan") — this project's username doubles as a visible display handle (shown on
    /users/, /profile/, admin) rather than a login identifier (login is by email, see
    users.backends.EmailBackend), so Django's default no-spaces restriction serves no purpose here.
    """
    username = models.CharField(
        'username', max_length=150, unique=True,
        help_text='150 characters or fewer. Letters, digits, spaces, and @/./+/-/_ only.',
        validators=[username_validator],
        error_messages={'unique': 'A user with that username already exists.'},
    )
    google_sub = models.CharField(
        max_length=255, blank=True, null=True, unique=True,
        help_text="Google's stable per-account ID ('sub' claim) — the real link to a Google "
                   "Sign-In identity, since email addresses can change but this doesn't.",
    )
    google_picture_url = models.URLField(
        blank=True, null=True,
        help_text='Refreshed from the Google ID token on every Google Sign-In.',
    )


class DeletedUser(models.Model):
    """Snapshot of an account at the moment it's removed via the admin-only Users page
    (core.views.delete_user) — a soft-delete audit trail, not a restore mechanism: the real `User`
    row (and its CASCADE-linked VisitSession/LoginHistory rows) is actually deleted, this just
    keeps a record of who existed and who removed them.
    """
    username = models.CharField(max_length=150)
    email = models.EmailField(blank=True)
    date_joined = models.DateTimeField()
    was_staff = models.BooleanField(default=False)
    was_superuser = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(auto_now_add=True)
    deleted_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name='deletions_performed',
    )

    class Meta:
        ordering = ['-deleted_at']

    def __str__(self):
        return f"{self.username} (deleted {self.deleted_at:%Y-%m-%d})"


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
