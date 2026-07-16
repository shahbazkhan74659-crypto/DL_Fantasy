from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from .forms import FictionUploadForm, GodValleyUploadForm, MythologyUploadForm, PhilosophyUploadForm
from .models import Content

CARDS = (
    {
        'category': Content.Category.GODVALLEY, 'label': 'The God Valley', 'url_name': 'upload_godvalley',
        'icon': 'godvalley', 'eyebrow': 'Flagship',
        'description': 'Continue the flagship chronicle, chapter by chapter.',
        'noun_singular': 'chapter', 'noun_plural': 'chapters',
    },
    {
        'category': Content.Category.FICTION, 'label': 'Fiction', 'url_name': 'upload_fiction',
        'icon': 'fiction', 'eyebrow': 'Writings',
        'description': 'Short stories and one-offs outside the Valley.',
        'noun_singular': 'story', 'noun_plural': 'stories',
    },
    {
        'category': Content.Category.PHILOSOPHY, 'label': 'Philosophy', 'url_name': 'upload_philosophy',
        'icon': 'philosophy', 'eyebrow': 'Writings',
        'description': 'Essays, arguments, and worldview pieces.',
        'noun_singular': 'essay', 'noun_plural': 'essays',
    },
    {
        'category': Content.Category.MYTHOLOGY, 'label': 'Mythology', 'url_name': 'upload_mythology',
        'icon': 'mythology', 'eyebrow': 'Writings',
        'description': 'Myths, cosmology, and inherited lore.',
        'noun_singular': 'myth', 'noun_plural': 'myths',
    },
)

FORM_CLASSES = {
    Content.Category.GODVALLEY: GodValleyUploadForm,
    Content.Category.FICTION: FictionUploadForm,
    Content.Category.PHILOSOPHY: PhilosophyUploadForm,
    Content.Category.MYTHOLOGY: MythologyUploadForm,
}

HEADINGS = {
    Content.Category.GODVALLEY: 'The God Valley',
    Content.Category.FICTION: 'Fiction',
    Content.Category.PHILOSOPHY: 'Philosophy',
    Content.Category.MYTHOLOGY: 'Mythology',
}

URL_NAMES = {card['category']: card['url_name'] for card in CARDS}


def _staff_only(request):
    if not request.user.is_staff:
        raise Http404


@login_required
def upload_hub(request):
    _staff_only(request)
    counts = dict(Content.objects.values_list('category').annotate(n=Count('id')).values_list('category', 'n'))
    cards = []
    for card in CARDS:
        count = counts.get(card['category'], 0)
        noun = card['noun_singular'] if count == 1 else card['noun_plural']
        cards.append({**card, 'url': reverse(card['url_name']), 'count': count, 'noun': noun})
    return render(request, 'upload_hub.html', {'cards': cards})


def _handle_upload(request, form_class, category, heading, url_name):
    _staff_only(request)
    if request.method == 'POST':
        form = form_class(request.POST, request.FILES)
        if form.is_valid():
            content = form.save(commit=False)
            content.category = category
            content.author = request.user
            content.save()
            messages.success(request, f'"{content.title}" was uploaded.')
            return redirect(url_name)
    else:
        form = form_class()
    existing_items = Content.objects.filter(category=category).select_related('subcategory').order_by('-created_at')
    return render(request, 'upload_form.html', {'form': form, 'heading': heading, 'existing_items': existing_items})


@login_required
def upload_godvalley(request):
    return _handle_upload(request, GodValleyUploadForm, Content.Category.GODVALLEY, 'Upload — The God Valley', 'upload_godvalley')


@login_required
def upload_fiction(request):
    return _handle_upload(request, FictionUploadForm, Content.Category.FICTION, 'Upload — Fiction', 'upload_fiction')


@login_required
def upload_philosophy(request):
    return _handle_upload(request, PhilosophyUploadForm, Content.Category.PHILOSOPHY, 'Upload — Philosophy', 'upload_philosophy')


@login_required
def upload_mythology(request):
    return _handle_upload(request, MythologyUploadForm, Content.Category.MYTHOLOGY, 'Upload — Mythology', 'upload_mythology')


@login_required
def edit_content(request, pk):
    _staff_only(request)
    content = get_object_or_404(Content, pk=pk)
    form_class = FORM_CLASSES[content.category]
    url_name = URL_NAMES[content.category]
    if request.method == 'POST':
        form = form_class(request.POST, request.FILES, instance=content)
        if form.is_valid():
            form.save()
            messages.success(request, f'"{content.title}" was updated.')
            return redirect(url_name)
    else:
        form = form_class(instance=content)
    heading = f'Edit — {HEADINGS[content.category]}'
    return render(request, 'upload_edit.html', {
        'form': form, 'heading': heading, 'url_name': url_name, 'content': content,
    })


@login_required
def delete_content(request, pk):
    if not request.user.is_staff or request.method != 'POST':
        raise Http404
    content = get_object_or_404(Content, pk=pk)
    url_name = URL_NAMES[content.category]
    title = content.title
    content.delete()
    messages.success(request, f'"{title}" was deleted.')
    return redirect(url_name)


@login_required
def delete_content_cover(request, pk):
    if not request.user.is_staff or request.method != 'POST':
        raise Http404
    content = get_object_or_404(Content, pk=pk)
    if content.cover_image:
        content.cover_image.delete(save=True)
        messages.success(request, 'Cover image was deleted.')
    return redirect('edit_content', pk=pk)
