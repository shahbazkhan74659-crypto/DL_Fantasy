"""One-time-password email verification for signup, sent via Gmail SMTP — optional and
self-hiding, same pattern as core/google_oauth.py: if EMAIL_HOST_USER/EMAIL_HOST_PASSWORD aren't
set in .env, is_configured() returns False and signup activates accounts immediately, exactly as
it did before this feature existed.

Codes are stored in the cache (not a DB model) keyed by user id, the same lightweight approach
core.views' login-throttle counters already use — no migration needed, and a 10-minute TTL is a
natural fit for cache expiry.
"""
import secrets
from smtplib import SMTPException

from django.conf import settings
from django.core.cache import cache
from django.core.mail import send_mail

OTP_LENGTH = 6
OTP_TTL = 10 * 60  # seconds a generated code stays valid
RESEND_COOLDOWN = 60  # seconds between resend requests, to stop a resend-spam loop
MAX_VERIFY_ATTEMPTS = 5  # caps brute-forcing a 6-digit code before a fresh one is required


class OTPSendError(Exception):
    """Raised when the verification email itself fails to send — callers show a generic error."""


def is_configured():
    return bool(settings.EMAIL_HOST_USER and settings.EMAIL_HOST_PASSWORD)


def _code_key(user_id):
    return f'otp:code:{user_id}'


def _attempts_key(user_id):
    return f'otp:attempts:{user_id}'


def _cooldown_key(user_id):
    return f'otp:cooldown:{user_id}'


def generate_and_send(user):
    """Generates a fresh code (invalidating any previous one), resets the attempt counter, and
    emails it. Returns False without sending anything if still within the resend cooldown.
    """
    if cache.get(_cooldown_key(user.pk)):
        return False

    code = ''.join(secrets.choice('0123456789') for _ in range(OTP_LENGTH))
    cache.set(_code_key(user.pk), code, OTP_TTL)
    cache.set(_attempts_key(user.pk), 0, OTP_TTL)
    cache.set(_cooldown_key(user.pk), True, RESEND_COOLDOWN)

    try:
        send_mail(
            subject='Your DL Fantasy verification code',
            message=f'Your verification code is {code}. It expires in 10 minutes.',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )
    except SMTPException as exc:
        raise OTPSendError('Could not send the verification email.') from exc
    return True


def verify(user, submitted_code):
    """Checks a submitted code against the stored one. Attempt-limited so a 6-digit space (1 in a
    million) can't just be brute-forced against the cache. Clears state on success.
    """
    attempts_key = _attempts_key(user.pk)
    if cache.get(attempts_key, 0) >= MAX_VERIFY_ATTEMPTS:
        return False

    expected = cache.get(_code_key(user.pk))
    if expected is None or not secrets.compare_digest(expected, submitted_code or ''):
        cache.set(attempts_key, cache.get(attempts_key, 0) + 1, OTP_TTL)
        return False

    cache.delete(_code_key(user.pk))
    cache.delete(attempts_key)
    return True
