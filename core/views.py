import re
from datetime import timedelta

from django.contrib import messages
from django.contrib.auth import login as auth_login
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Count, DurationField, ExpressionWrapper, F, Sum
from django.http import Http404, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme

from upload.models import Content, DownloadHistory, Favourite, News, ReadingHistory, ReadingListItem, Subcategory
from users.models import DeletedUser, User, VisitSession

from . import google_oauth
from .forms import NewsForm, ProfileForm, SignupForm, StyledAuthenticationForm, UserEditForm
from .pdf import build_content_pdf

WRITINGS_CATEGORIES = (
    Content.Category.FICTION,
    Content.Category.PHILOSOPHY,
    Content.Category.MYTHOLOGY,
)

PAGE_SIZE = 12


def _paginate(request, queryset):
    return Paginator(queryset, PAGE_SIZE).get_page(request.GET.get('page'))


SPOTLIGHT_SIZE = 6


def home(request):
    entries = Content.objects.filter(is_published=True).order_by('-created_at')
    spotlight = Content.objects.filter(is_published=True).order_by('?')[:SPOTLIGHT_SIZE]
    return render(request, 'home.html', {'entries': _paginate(request, entries), 'spotlight': spotlight})


def shuffle_spotlight(request):
    entries = Content.objects.filter(is_published=True).order_by('?')[:SPOTLIGHT_SIZE]
    return JsonResponse({
        'items': [
            {'url': entry.get_absolute_url(), 'title': entry.title, 'cover_url': entry.cover_url}
            for entry in entries
        ],
    })


def writings(request):
    highlights = {category: None for category in WRITINGS_CATEGORIES}
    entries = Content.objects.filter(
        category__in=WRITINGS_CATEGORIES, is_published=True,
    ).order_by('category', '-created_at')
    for entry in entries:
        if highlights[entry.category] is None:
            highlights[entry.category] = entry
    return render(request, 'writings.html', {'highlights': highlights})


def writings_category_list(request, category):
    if category not in WRITINGS_CATEGORIES:
        raise Http404("Unknown writings category")
    entries = Content.objects.filter(category=category, is_published=True).order_by('-created_at')

    subcategories = Subcategory.objects.filter(parent_category=category)
    active_subcategory = None
    requested = request.GET.get('topic', '')
    if requested:
        active_subcategory = subcategories.filter(slug=requested).first()
        if active_subcategory:
            entries = entries.filter(subcategory=active_subcategory)

    return render(request, 'writings_list.html', {
        'category': category,
        'category_label': Content.Category(category).label,
        'entries': _paginate(request, entries),
        'subcategories': subcategories,
        'active_topic': active_subcategory.slug if active_subcategory else '',
    })


def _record_reading_history(request, content):
    if not request.user.is_authenticated:
        return
    history, created = ReadingHistory.objects.get_or_create(user=request.user, content=content)
    if not created:
        history.save()  # bumps auto_now viewed_at so re-reads float back to the top


def _is_favourited(request, content):
    if not request.user.is_authenticated:
        return False
    return Favourite.objects.filter(user=request.user, content=content).exists()


def _is_in_reading_list(request, content):
    if not request.user.is_authenticated:
        return False
    return ReadingListItem.objects.filter(user=request.user, content=content).exists()


def writings_detail(request, category, slug):
    if category not in WRITINGS_CATEGORIES:
        raise Http404("Unknown writings category")
    entry = get_object_or_404(Content, category=category, slug=slug, is_published=True)
    _record_reading_history(request, entry)
    return render(request, 'writings_detail.html', {
        'entry': entry,
        'is_favourited': _is_favourited(request, entry),
        'is_in_reading_list': _is_in_reading_list(request, entry),
        'page_cover_url': entry.cover_url,
    })


def godvalley_list(request):
    return render(request, 'godvalley_list.html')


def godvalley_chapters(request):
    chapters = Content.objects.filter(
        category=Content.Category.GODVALLEY, is_published=True,
    ).order_by('-chapter_number')

    query = request.GET.get('q', '').strip()
    if query:
        chapters = chapters.filter(title__icontains=query)

    return render(request, 'godvalley_chapters.html', {'chapters': _paginate(request, chapters), 'query': query})


def godvalley_detail(request, slug):
    chapter = get_object_or_404(
        Content, category=Content.Category.GODVALLEY, slug=slug, is_published=True,
    )
    base_qs = Content.objects.filter(category=Content.Category.GODVALLEY, is_published=True)
    prev_chapter = (
        base_qs.filter(chapter_number__lt=chapter.chapter_number)
        .order_by('-chapter_number').only('slug', 'chapter_number', 'title').first()
    )
    next_chapter = (
        base_qs.filter(chapter_number__gt=chapter.chapter_number)
        .order_by('chapter_number').only('slug', 'chapter_number', 'title').first()
    )

    _record_reading_history(request, chapter)

    return render(request, 'godvalley_detail.html', {
        'chapter': chapter,
        'prev_chapter': prev_chapter,
        'next_chapter': next_chapter,
        'is_favourited': _is_favourited(request, chapter),
        'is_in_reading_list': _is_in_reading_list(request, chapter),
        'page_cover_url': chapter.cover_url,
    })


@login_required
def toggle_favourite(request, content_id):
    if request.method != 'POST':
        raise Http404
    content = get_object_or_404(Content, pk=content_id, is_published=True)
    favourite, created = Favourite.objects.get_or_create(user=request.user, content=content)
    if not created:
        favourite.delete()
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'is_favourited': created})
    next_url = request.POST.get('next')
    return redirect(_safe_next(request, next_url))


@login_required
def favourites(request):
    items = Favourite.objects.filter(user=request.user).select_related('content')
    return render(request, 'favourites.html', {'favourites': _paginate(request, items)})


@login_required
def toggle_reading_list_item(request, content_id):
    if request.method != 'POST':
        raise Http404
    content = get_object_or_404(Content, pk=content_id, is_published=True)
    item, created = ReadingListItem.objects.get_or_create(user=request.user, content=content)
    if not created:
        item.delete()
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'is_in_reading_list': created})
    next_url = request.POST.get('next')
    return redirect(_safe_next(request, next_url))


@login_required
def reading_list(request):
    items = ReadingListItem.objects.filter(user=request.user).select_related('content')
    return render(request, 'reading_list.html', {'reading_list_items': _paginate(request, items)})


@login_required
def download_content(request, content_id):
    if request.method != 'POST':
        raise Http404
    content = get_object_or_404(Content, pk=content_id, is_published=True)

    record, created = DownloadHistory.objects.get_or_create(user=request.user, content=content)
    if not created:
        record.save()  # bumps auto_now downloaded_at so re-downloads float back to the top

    pdf_bytes = build_content_pdf(content)
    response = HttpResponse(pdf_bytes, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{content.slug}.pdf"'
    return response


@login_required
def downloads(request):
    items = DownloadHistory.objects.filter(user=request.user).select_related('content')
    return render(request, 'downloads.html', {'download_history': _paginate(request, items)})


def search(request):
    query = request.GET.get('q', '').strip()
    results = Content.objects.none()
    if query:
        results = Content.objects.filter(
            is_published=True, title__icontains=query,
        ).order_by('-created_at')
    return render(request, 'search.html', {
        'query': query,
        'results': _paginate(request, results),
    })


def archive(request):
    return render(request, 'archive.html')


@login_required
def concepts(request):
    if not request.user.is_staff:
        raise Http404
    return render(request, 'concepts.html')


def collections(request):
    return render(request, 'collections.html')


def about(request):
    return render(request, 'about.html')


def news(request):
    items = News.objects.all()
    if request.user.is_staff:
        for item in items:
            item.menu_actions = [
                {
                    'type': 'edit-modal',
                    'label': 'Edit',
                    'url': reverse('edit_news', args=[item.slug]),
                    'trigger_class': 'news-edit-btn',
                    'data': {'title': item.title, 'tag': item.tag, 'body': item.body},
                },
                {
                    'type': 'delete',
                    'label': 'Delete',
                    'url': reverse('delete_news', args=[item.slug]),
                    'confirm': f'Delete "{item.title}"? This can\'t be undone.',
                },
            ]
    return render(request, 'news.html', {'items': items})


def news_detail(request, slug):
    item = get_object_or_404(News, slug=slug)
    return render(request, 'news_detail.html', {'item': item})


@login_required
def create_news(request):
    if not request.user.is_staff:
        raise Http404
    if request.method == 'POST':
        form = NewsForm(request.POST, request.FILES)
        if form.is_valid():
            item = form.save()
            messages.success(request, f'"{item.title}" was published.')
            return redirect('news')
        errors = '; '.join(f"{field}: {', '.join(errs)}" for field, errs in form.errors.items())
        messages.error(request, f"Could not publish — {errors}")
    return redirect('news')


@login_required
def edit_news(request, slug):
    if not request.user.is_staff:
        raise Http404
    item = get_object_or_404(News, slug=slug)
    if request.method == 'POST':
        form = NewsForm(request.POST, request.FILES, instance=item)
        if form.is_valid():
            form.save()
            messages.success(request, f'"{item.title}" was updated.')
        else:
            errors = '; '.join(f"{field}: {', '.join(errs)}" for field, errs in form.errors.items())
            messages.error(request, f"Could not update {item.title} — {errors}")
    return redirect('news')


@login_required
def delete_news(request, slug):
    if not request.user.is_staff or request.method != 'POST':
        raise Http404
    item = get_object_or_404(News, slug=slug)
    title = item.title
    item.delete()
    messages.success(request, f'"{title}" was deleted.')
    return redirect('news')


def _safe_next(request, next_url):
    if next_url and url_has_allowed_host_and_scheme(
        next_url, allowed_hosts={request.get_host()}, require_https=request.is_secure(),
    ):
        return next_url
    return 'home'


def signup(request):
    if request.user.is_authenticated:
        return redirect('account')
    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            user = form.save()
            auth_login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            messages.success(request, 'Welcome to DL Fantasy — your account is ready.')
            return redirect('home')
    else:
        form = SignupForm()
    return render(request, 'signup.html', {'form': form, 'google_oauth_enabled': google_oauth.is_configured()})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('account')
    next_url = request.POST.get('next') or request.GET.get('next', '')
    if request.method == 'POST':
        form = StyledAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            auth_login(request, form.get_user())
            return redirect(_safe_next(request, next_url))
    else:
        form = StyledAuthenticationForm(request)
    return render(request, 'login.html', {
        'form': form,
        'next': next_url,
        'google_oauth_enabled': google_oauth.is_configured(),
    })


def _generate_username_from_email(email):
    base = re.sub(r'[^\w.@+-]', '', email.split('@')[0])[:140] or 'user'
    username = base
    suffix = 1
    while User.objects.filter(username=username).exists():
        suffix += 1
        username = f'{base}{suffix}'[:150]
    return username


def google_login(request):
    if not google_oauth.is_configured():
        raise Http404
    redirect_uri = request.build_absolute_uri(reverse('google_callback'))
    return redirect(google_oauth.build_authorization_url(request, redirect_uri))


def google_callback(request):
    if not google_oauth.is_configured():
        raise Http404

    if request.GET.get('error') or not google_oauth.verify_callback_state(request):
        messages.error(request, 'Google sign-in was cancelled or could not be verified.')
        return redirect('login')

    code = request.GET.get('code')
    if not code:
        messages.error(request, 'Google sign-in failed — please try again.')
        return redirect('login')

    redirect_uri = request.build_absolute_uri(reverse('google_callback'))
    try:
        identity = google_oauth.fetch_identity(code, redirect_uri)
    except google_oauth.GoogleOAuthError:
        messages.error(request, 'Google sign-in failed — please try again.')
        return redirect('login')

    user = (
        User.objects.filter(google_sub=identity['sub']).first()
        or User.objects.filter(email__iexact=identity['email']).first()
    )
    if user is None:
        user = User(username=_generate_username_from_email(identity['email']), email=identity['email'])
        user.set_unusable_password()

    user.google_sub = identity['sub']
    user.google_picture_url = identity['picture']
    user.save()

    auth_login(request, user, backend='django.contrib.auth.backends.ModelBackend')
    messages.success(request, f"Welcome, {user.username}.")
    return redirect('account')


@login_required
def account(request):
    today = timezone.localdate()
    start_date = today - timedelta(days=29)

    duration = ExpressionWrapper(F('last_seen_at') - F('started_at'), output_field=DurationField())
    stats_by_date = {
        row['date']: row
        for row in (
            VisitSession.objects.filter(user=request.user, date__gte=start_date)
            .annotate(duration=duration)
            .values('date')
            .annotate(count=Count('id'), total_duration=Sum('duration'))
        )
    }

    visit_days = []
    for i in range(30):
        d = start_date + timedelta(days=i)
        stat = stats_by_date.get(d)
        count = stat['count'] if stat else 0
        total_duration = stat['total_duration'] if stat and stat['total_duration'] else timedelta()
        visit_days.append({
            'date': d,
            'count': count,
            'minutes': int(total_duration.total_seconds() // 60),
        })

    visit_count_30d = sum(day['count'] for day in visit_days)
    total_minutes_30d = sum(day['minutes'] for day in visit_days)
    max_count = max((day['count'] for day in visit_days), default=0) or 1

    return render(request, 'account.html', {
        'visit_days': visit_days,
        'visit_count_30d': visit_count_30d,
        'total_hours_30d': total_minutes_30d // 60,
        'total_minutes_30d': total_minutes_30d % 60,
        'max_count': max_count,
    })


@login_required
def profile(request):
    if request.method == 'POST':
        form = ProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your profile was updated.')
            return redirect('profile')
    else:
        form = ProfileForm(instance=request.user)

    reading_history = (
        ReadingHistory.objects.filter(user=request.user).select_related('content')[:10]
    )

    return render(request, 'profile.html', {'form': form, 'reading_history': reading_history})


@login_required
def users_list(request):
    if not request.user.is_staff:
        raise Http404
    users = User.objects.all().order_by('-is_superuser', '-is_staff', '-date_joined')
    return render(request, 'users_list.html', {'users': users})


@login_required
def edit_user(request, user_id):
    if not request.user.is_staff:
        raise Http404
    target = get_object_or_404(User, pk=user_id)
    if request.method == 'POST':
        form = UserEditForm(request.POST, instance=target)
        if form.is_valid():
            form.save()
            messages.success(request, f"{target.username} was updated.")
        else:
            errors = '; '.join(f"{field}: {', '.join(errs)}" for field, errs in form.errors.items())
            messages.error(request, f"Could not update {target.username} — {errors}")
    return redirect('users_list')


@login_required
def delete_user(request, user_id):
    if not request.user.is_staff or request.method != 'POST':
        raise Http404
    target = get_object_or_404(User, pk=user_id)
    if target.is_staff or target.is_superuser:
        messages.error(request, "Admin accounts can't be deleted.")
        return redirect('users_list')

    DeletedUser.objects.create(
        username=target.username,
        email=target.email,
        date_joined=target.date_joined,
        was_staff=target.is_staff,
        was_superuser=target.is_superuser,
        deleted_by=request.user,
    )
    username = target.username
    target.delete()
    messages.success(request, f"{username} was deleted.")
    return redirect('users_list')
