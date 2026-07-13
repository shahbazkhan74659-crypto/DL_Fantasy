"""Minimal "Sign in with Google" OAuth2 client — just enough to authenticate a visitor and read
their email/name/photo, without pulling in a full social-auth framework like django-allauth.

Flow: google_login() sends the visitor to Google's consent screen with a random `state`; Google
redirects back to google_callback() with a `code`; that code is exchanged for tokens, and the
returned ID token is verified (signature, issuer, audience, expiry) via google-auth rather than
decoded by hand, since hand-rolled JWT verification is exactly the kind of thing that quietly
becomes a security hole.
"""
import secrets
from urllib.parse import urlencode

import requests
from django.conf import settings
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token as google_id_token

AUTH_ENDPOINT = 'https://accounts.google.com/o/oauth2/v2/auth'
TOKEN_ENDPOINT = 'https://oauth2.googleapis.com/token'
SCOPES = 'openid email profile'
STATE_SESSION_KEY = 'google_oauth_state'


class GoogleOAuthError(Exception):
    """Raised for any failure in the exchange/verify steps — callers show a generic error."""


def is_configured():
    return bool(settings.GOOGLE_OAUTH_CLIENT_ID and settings.GOOGLE_OAUTH_CLIENT_SECRET)


def build_authorization_url(request, redirect_uri):
    state = secrets.token_urlsafe(32)
    request.session[STATE_SESSION_KEY] = state

    params = {
        'client_id': settings.GOOGLE_OAUTH_CLIENT_ID,
        'redirect_uri': redirect_uri,
        'response_type': 'code',
        'scope': SCOPES,
        'state': state,
        'prompt': 'select_account',
    }
    return f'{AUTH_ENDPOINT}?{urlencode(params)}'


def verify_callback_state(request):
    """Pops and checks the one-time state token; True if it matches what google_login() stored."""
    expected = request.session.pop(STATE_SESSION_KEY, None)
    received = request.GET.get('state')
    return expected is not None and secrets.compare_digest(expected, received or '')


def fetch_identity(code, redirect_uri):
    """Exchanges an authorization code for a verified identity: {sub, email, name, picture}."""
    try:
        response = requests.post(
            TOKEN_ENDPOINT,
            data={
                'code': code,
                'client_id': settings.GOOGLE_OAUTH_CLIENT_ID,
                'client_secret': settings.GOOGLE_OAUTH_CLIENT_SECRET,
                'redirect_uri': redirect_uri,
                'grant_type': 'authorization_code',
            },
            timeout=10,
        )
        response.raise_for_status()
        token_response = response.json()
    except (requests.RequestException, ValueError) as exc:
        raise GoogleOAuthError('Could not reach Google to complete sign-in.') from exc

    raw_id_token = token_response.get('id_token')
    if not raw_id_token:
        raise GoogleOAuthError('Google did not return an identity token.')

    try:
        claims = google_id_token.verify_oauth2_token(
            raw_id_token, google_requests.Request(), settings.GOOGLE_OAUTH_CLIENT_ID,
        )
    except ValueError as exc:
        raise GoogleOAuthError('Google identity token failed verification.') from exc

    if not claims.get('email_verified'):
        raise GoogleOAuthError('Google account email is not verified.')

    return {
        'sub': claims['sub'],
        'email': claims['email'],
        'name': claims.get('name', ''),
        'picture': claims.get('picture', ''),
    }
