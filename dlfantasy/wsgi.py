"""
WSGI config for dlfantasy project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dlfantasy.settings')

application = get_wsgi_application()

# dlfantasy/urls.py only serves MEDIA_URL through Django's own static() helper when DEBUG=True
# (Django's documented dev-only shortcut) — gunicorn in production runs with DEBUG=False, so
# without this, every uploaded cover image (Content.cover_image / News.cover_image) 404s on a
# real deploy despite working fine locally. Wrapping the WSGI app in WhiteNoise here (in addition
# to WhiteNoiseMiddleware in settings.py, which only handles STATIC_ROOT) serves MEDIA_ROOT
# directly at the /media/ prefix in every environment gunicorn runs in, with zero extra
# infrastructure (no S3/nginx) — consistent with this project's existing preference for
# zero-infrastructure options (see CLAUDE.md's Downloads/otp sections).
from django.conf import settings
from whitenoise import WhiteNoise

application = WhiteNoise(application, root=str(settings.MEDIA_ROOT), prefix=settings.MEDIA_URL)
