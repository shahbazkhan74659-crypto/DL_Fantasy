from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend

UserModel = get_user_model()


class EmailBackend(ModelBackend):
    """Authenticates by email instead of username, for the visitor-facing login form
    (core.forms.StyledAuthenticationForm), which asks for email rather than username.

    Kept alongside ModelBackend (see AUTHENTICATION_BACKENDS) rather than replacing it, since
    Django admin's own login form still authenticates by username.
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None or password is None:
            return None
        try:
            user = UserModel._default_manager.get(email__iexact=username)
        except (UserModel.DoesNotExist, UserModel.MultipleObjectsReturned):
            UserModel().set_password(password)  # mirrors ModelBackend: constant-time no-op
            return None
        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None
