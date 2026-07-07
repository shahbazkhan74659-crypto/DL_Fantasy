from django.core.paginator import Paginator
from django.http import Http404
from django.shortcuts import get_object_or_404, render

from upload.models import Content

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
