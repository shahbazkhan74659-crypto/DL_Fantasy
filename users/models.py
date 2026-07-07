from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    """Custom user model so future non-admin accounts don't require a data migration."""
    pass
