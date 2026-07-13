from datetime import timedelta

from django.utils import timezone
from django.utils.dateparse import parse_datetime

from .models import VisitSession

SESSION_ID_KEY = 'active_visit_session_id'
SESSION_DATE_KEY = 'active_visit_date'
LAST_SEEN_KEY = 'active_visit_last_seen'


class TrackVisitSessionsMiddleware:
    """Splits an authenticated user's activity into distinct visits per day.

    A new VisitSession row starts when the user has been inactive for more than SESSION_GAP, or
    when the calendar day has rolled over since their last request; otherwise the existing row's
    last_seen_at is just bumped. This lets the account page report both how many separate times a
    user visited on a given day and how long they spent on each visit, instead of the old
    one-row-per-day dedup that could only say yes/no.
    """
    SESSION_GAP = timedelta(minutes=30)

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = getattr(request, 'user', None)
        if user is not None and user.is_authenticated:
            now = timezone.now()
            today = timezone.localdate()
            session_id = request.session.get(SESSION_ID_KEY)
            visit_date = request.session.get(SESSION_DATE_KEY)
            last_seen = parse_datetime(request.session.get(LAST_SEEN_KEY) or '')

            starts_new_visit = (
                session_id is None
                or last_seen is None
                or now - last_seen > self.SESSION_GAP
                or visit_date != today.isoformat()
            )

            if starts_new_visit:
                visit = VisitSession.objects.create(user=user, date=today, started_at=now, last_seen_at=now)
                request.session[SESSION_ID_KEY] = visit.pk
                request.session[SESSION_DATE_KEY] = today.isoformat()
            else:
                VisitSession.objects.filter(pk=session_id).update(last_seen_at=now)

            request.session[LAST_SEEN_KEY] = now.isoformat()
        return self.get_response(request)
