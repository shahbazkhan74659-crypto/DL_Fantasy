from django.http import Http404
from django.shortcuts import get_object_or_404, render

from upload.models import Content

WRITINGS_CATEGORIES = (
    Content.Category.FICTION,
    Content.Category.PHILOSOPHY,
    Content.Category.MYTHOLOGY,
)


def home(request):
    recent = Content.objects.filter(is_published=True).order_by('-created_at')[:6]
    return render(request, 'home.html', {'recent': recent})


def writings(request):
    highlights = {
        category: Content.objects.filter(category=category, is_published=True).order_by('-created_at').first()
        for category in WRITINGS_CATEGORIES
    }
    return render(request, 'writings.html', {'highlights': highlights})


def writings_category_list(request, category):
    if category not in WRITINGS_CATEGORIES:
        raise Http404("Unknown writings category")
    entries = Content.objects.filter(category=category, is_published=True).order_by('-created_at')
    return render(request, 'writings_list.html', {
        'category': category,
        'category_label': Content.Category(category).label,
        'entries': entries,
    })


def writings_detail(request, category, slug):
    if category not in WRITINGS_CATEGORIES:
        raise Http404("Unknown writings category")
    entry = get_object_or_404(Content, category=category, slug=slug, is_published=True)
    return render(request, 'writings_detail.html', {'entry': entry})


def godvalley_list(request):
    chapters = Content.objects.filter(
        category=Content.Category.GODVALLEY, is_published=True,
    ).order_by('chapter_number')

    query = request.GET.get('q', '').strip()
    if query:
        chapters = chapters.filter(title__icontains=query)

    return render(request, 'godvalley_list.html', {'chapters': chapters, 'query': query})


def godvalley_detail(request, slug):
    chapter = get_object_or_404(
        Content, category=Content.Category.GODVALLEY, slug=slug, is_published=True,
    )
    chapters = list(
        Content.objects.filter(category=Content.Category.GODVALLEY, is_published=True).order_by('chapter_number')
    )
    index = chapters.index(chapter)
    prev_chapter = chapters[index - 1] if index > 0 else None
    next_chapter = chapters[index + 1] if index < len(chapters) - 1 else None

    return render(request, 'godvalley_detail.html', {
        'chapter': chapter,
        'prev_chapter': prev_chapter,
        'next_chapter': next_chapter,
    })


def about(request):
    return render(request, 'about.html')
