from django.utils import timezone

from .models import DailyVisit

VISIT_SESSION_KEY = 'visit_recorded_for_date'


class TrackDailyVisitMiddleware:
    """Records at most one DailyVisit row per authenticated user per calendar day."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = getattr(request, 'user', None)
        if user is not None and user.is_authenticated:
            today = timezone.localdate()
            if request.session.get(VISIT_SESSION_KEY) != today.isoformat():
                DailyVisit.objects.get_or_create(user=user, date=today)
                request.session[VISIT_SESSION_KEY] = today.isoformat()
        return self.get_response(request)
