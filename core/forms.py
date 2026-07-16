from django import forms
from django.contrib.auth.forms import AuthenticationForm, SetPasswordForm, UserCreationForm

from upload.models import News
from users.models import User

FIELD_ATTRS = {'class': 'auth-field', 'autocomplete': 'off'}


class SignupForm(UserCreationForm):
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs=FIELD_ATTRS))

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name in ('username', 'password1', 'password2'):
            self.fields[name].widget.attrs.update(FIELD_ATTRS)

    def clean_email(self):
        email = self.cleaned_data['email']
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('An account with this email already exists.')
        return email


class StyledAuthenticationForm(AuthenticationForm):
    """Asks for email rather than username — the 'username' field name is kept internally
    (only its label/widget change) since AuthenticationForm.clean() always calls
    authenticate(username=<value>, ...), which users.backends.EmailBackend then resolves by email.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].label = 'Email'
        self.fields['username'].widget = forms.EmailInput(attrs=FIELD_ATTRS)
        for field in self.fields.values():
            field.widget.attrs.update(FIELD_ATTRS)

    def get_invalid_login_error(self):
        return forms.ValidationError(
            'Please enter a correct email and password. Note that both fields may be case-sensitive.',
            code='invalid_login',
        )


class StyledPasswordChangeForm(SetPasswordForm):
    """No old-password check for now — revisit once real account security is in scope."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update(FIELD_ATTRS)


class UserEditForm(forms.ModelForm):
    """Backs the edit-user modal on the admin-only /users/ page. Deliberately scoped to identity
    fields only (username/email/active) — staff/superuser status isn't editable here, so this
    form can't be used to self-escalate or de-escalate admin privileges by accident.
    """
    class Meta:
        model = User
        fields = ('username', 'email', 'is_active')

    def clean_email(self):
        email = self.cleaned_data['email']
        if User.objects.filter(email__iexact=email).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError('Another account already uses this email.')
        return email


class NewsForm(forms.ModelForm):
    """Backs the 'New' modal on the admin-only News page. Only title/tag/body/cover_image are
    user-supplied — the slug is generated in News.save() and created_at is auto_now_add, so
    there's no date input."""
    class Meta:
        model = News
        fields = ('title', 'tag', 'body', 'cover_image')


class ProfileForm(forms.ModelForm):
    """Self-service version of UserEditForm on the /profile/ page — a visitor editing their own
    username/email. No is_active field here (unlike UserEditForm): that's an admin-only lever,
    not something an account should be able to flip on itself.
    """
    class Meta:
        model = User
        fields = ('username', 'email')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update(FIELD_ATTRS)

    def clean_email(self):
        email = self.cleaned_data['email']
        if User.objects.filter(email__iexact=email).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError('Another account already uses this email.')
        return email
