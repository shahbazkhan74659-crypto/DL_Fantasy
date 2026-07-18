from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Count, Max
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from .forms import (
    CollectionForm, FictionUploadForm, GodValleyUploadForm, MythologyUploadForm,
    PhilosophyUploadForm,
)
from .models import Collection, CollectionItem, Content

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

COLLECTIONS_CARD = {
    'label': 'Collections', 'url_name': 'upload_collections',
    'icon': 'collections', 'eyebrow': 'Curation',
    'description': 'Curate anthologies from anything already published.',
    'noun_singular': 'collection', 'noun_plural': 'collections',
}

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
    collection_count = Collection.objects.count()
    cards.append({
        **COLLECTIONS_CARD,
        'url': reverse(COLLECTIONS_CARD['url_name']),
        'count': collection_count,
        'noun': COLLECTIONS_CARD['noun_singular'] if collection_count == 1 else COLLECTIONS_CARD['noun_plural'],
    })
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


def _grouped_published_content():
    """Published content grouped by category in CARDS order, for the collection item picker."""
    grouped = {card['category']: [] for card in CARDS}
    for content in Content.objects.filter(is_published=True).order_by('chapter_number', '-created_at'):
        grouped[content.category].append(content)
    return [
        (card['label'], grouped[card['category']])
        for card in CARDS if grouped[card['category']]
    ]


def _selected_ids(form):
    """Content ids the picker should render checked: POSTed values on a bound (failed) submit,
    the instance's current items when editing, empty on a fresh form."""
    if form.is_bound:
        return {int(v) for v in form.data.getlist('items') if v.isdigit()}
    initial = form.fields['items'].initial
    return {content.pk for content in initial} if initial else set()


def _sync_collection_items(collection, selected_contents):
    """Make the collection's items match the picker: drop unchecked, append newly checked at the
    end (in picker display order). Kept items keep their positions — never renumbered."""
    selected_ids = {content.pk for content in selected_contents}
    collection.items.exclude(content_id__in=selected_ids).delete()
    existing_ids = set(collection.items.values_list('content_id', flat=True))
    next_position = (collection.items.aggregate(m=Max('position'))['m'] or 0) + 1
    for _, contents in _grouped_published_content():
        for content in contents:
            if content.pk in selected_ids and content.pk not in existing_ids:
                CollectionItem.objects.create(collection=collection, content=content, position=next_position)
                next_position += 1


@login_required
def upload_collections(request):
    _staff_only(request)
    if request.method == 'POST':
        form = CollectionForm(request.POST, request.FILES)
        if form.is_valid():
            collection = form.save()
            _sync_collection_items(collection, form.cleaned_data['items'])
            messages.success(request, f'"{collection.title}" was created.')
            return redirect('upload_collections')
    else:
        form = CollectionForm()
    existing_collections = Collection.objects.annotate(n_items=Count('items'))
    return render(request, 'upload_collection_form.html', {
        'form': form,
        'heading': 'Upload — Collections',
        'grouped_content': _grouped_published_content(),
        'selected_ids': _selected_ids(form),
        'existing_collections': existing_collections,
    })


@login_required
def edit_collection(request, pk):
    _staff_only(request)
    collection = get_object_or_404(Collection, pk=pk)
    if request.method == 'POST':
        form = CollectionForm(request.POST, request.FILES, instance=collection)
        if form.is_valid():
            form.save()
            _sync_collection_items(collection, form.cleaned_data['items'])
            messages.success(request, f'"{collection.title}" was updated.')
            return redirect('upload_collections')
    else:
        form = CollectionForm(instance=collection)
    return render(request, 'upload_collection_edit.html', {
        'form': form,
        'heading': 'Edit — Collection',
        'collection': collection,
        'grouped_content': _grouped_published_content(),
        'selected_ids': _selected_ids(form),
        'ordered_items': collection.items.select_related('content'),
    })


@login_required
def move_collection_item(request, pk):
    if not request.user.is_staff or request.method != 'POST':
        raise Http404
    item = get_object_or_404(CollectionItem, pk=pk)
    direction = request.POST.get('direction')
    if direction == 'up':
        neighbour = item.collection.items.filter(position__lt=item.position).order_by('-position').first()
    elif direction == 'down':
        neighbour = item.collection.items.filter(position__gt=item.position).order_by('position').first()
    else:
        neighbour = None
    if neighbour:
        with transaction.atomic():
            item.position, neighbour.position = neighbour.position, item.position
            item.save(update_fields=['position'])
            neighbour.save(update_fields=['position'])
    return redirect('edit_collection', pk=item.collection_id)


@login_required
def delete_collection(request, pk):
    if not request.user.is_staff or request.method != 'POST':
        raise Http404
    collection = get_object_or_404(Collection, pk=pk)
    title = collection.title
    collection.delete()
    messages.success(request, f'"{title}" was deleted.')
    return redirect('upload_collections')


@login_required
def delete_collection_cover(request, pk):
    if not request.user.is_staff or request.method != 'POST':
        raise Http404
    collection = get_object_or_404(Collection, pk=pk)
    if collection.cover_image:
        collection.cover_image.delete(save=True)
        messages.success(request, 'Cover image was deleted.')
    return redirect('edit_collection', pk=pk)
