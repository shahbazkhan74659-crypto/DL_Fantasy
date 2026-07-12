from datetime import timedelta

from django.contrib import messages
from django.contrib.auth import login as auth_login
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme

from upload.models import Content
from users.models import DailyVisit

from .forms import SignupForm, StyledAuthenticationForm

WRITINGS_CATEGORIES = (
    Content.Category.FICTION,
    Content.Category.PHILOSOPHY,
    Content.Category.MYTHOLOGY,
)

PAGE_SIZE = 12


def _paginate(request, queryset):
    return Paginator(queryset, PAGE_SIZE).get_page(request.GET.get('page'))


def home(request):
    recent = Content.objects.filter(is_published=True).order_by('-created_at')[:6]
    return render(request, 'home.html', {'recent': recent})


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
    return render(request, 'writings_list.html', {
        'category': category,
        'category_label': Content.Category(category).label,
        'entries': _paginate(request, entries),
    })


def writings_detail(request, category, slug):
    if category not in WRITINGS_CATEGORIES:
        raise Http404("Unknown writings category")
    entry = get_object_or_404(Content, category=category, slug=slug, is_published=True)
    return render(request, 'writings_detail.html', {'entry': entry})


def godvalley_list(request):
    return render(request, 'godvalley_list.html')


def godvalley_chapters(request):
    chapters = Content.objects.filter(
        category=Content.Category.GODVALLEY, is_published=True,
    ).order_by('chapter_number')

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

    return render(request, 'godvalley_detail.html', {
        'chapter': chapter,
        'prev_chapter': prev_chapter,
        'next_chapter': next_chapter,
    })


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


def concepts(request):
    return render(request, 'concepts.html')


def collections(request):
    return render(request, 'collections.html')


def about(request):
    return render(request, 'about.html')


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
            auth_login(request, user)
            messages.success(request, 'Welcome to DL Fantasy — your account is ready.')
            return redirect('home')
    else:
        form = SignupForm()
    return render(request, 'signup.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('account')
    next_url = request.POST.get('next') or request.GET.get('next', '')
    if request.method == 'POST':
        form = StyledAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            auth_login(request, form.get_user())
            messages.success(request, f"Welcome back, {form.get_user().username}.")
            return redirect(_safe_next(request, next_url))
    else:
        form = StyledAuthenticationForm(request)
    return render(request, 'login.html', {'form': form, 'next': next_url})


@login_required
def account(request):
    today = timezone.localdate()
    start_date = today - timedelta(days=29)
    visited_dates = set(
        DailyVisit.objects.filter(user=request.user, date__gte=start_date).values_list('date', flat=True)
    )
    visit_days = [
        {'date': start_date + timedelta(days=i), 'count': int((start_date + timedelta(days=i)) in visited_dates)}
        for i in range(30)
    ]
    visit_count_30d = sum(day['count'] for day in visit_days)
    return render(request, 'account.html', {
        'visit_days': visit_days,
        'visit_count_30d': visit_count_30d,
        'max_count': 1,
    })
