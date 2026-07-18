from django.conf import settings
from django.db import models
from django.utils.text import slugify


class Content(models.Model):
    """Central table for all writings-type content (Fiction, Philosophy, Mythology, God Valley).

    God Valley lives here for now; scope calls for splitting it into its own
    dedicated table later once the site grows.
    """

    class Category(models.TextChoices):
        FICTION = 'fiction', 'Fiction'
        PHILOSOPHY = 'philosophy', 'Philosophy'
        MYTHOLOGY = 'mythology', 'Mythology'
        GODVALLEY = 'godvalley', 'The God Valley'

    category = models.CharField(max_length=20, choices=Category.choices)
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220)
    excerpt = models.CharField(max_length=300, blank=True)
    body = models.TextField()
    chapter_number = models.PositiveIntegerField(
        null=True, blank=True,
        help_text="God Valley chapter order. Leave blank for non-chapter content.",
    )
    subcategory = models.ForeignKey(
        'Subcategory', on_delete=models.PROTECT, null=True, blank=True, related_name='contents',
        help_text="Which Fiction story / Philosophy topic / Mythology tradition. Not used for God Valley.",
    )
    cover_image = models.ImageField(upload_to='covers/content/%Y/%m/', blank=True, null=True)
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='contents',
    )
    is_published = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['category', 'is_published', '-created_at'], name='content_cat_pub_created_idx'),
        ]
        constraints = [
            models.UniqueConstraint(fields=['category', 'slug'], name='unique_slug_per_category'),
        ]

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.title)[:200] or self.category
            slug = base
            suffix = 1
            while Content.objects.filter(category=self.category, slug=slug).exists():
                suffix += 1
                slug = f'{base}-{suffix}'[:220]
            self.slug = slug
        super().save(*args, **kwargs)

    def __str__(self):
        if self.category == self.Category.GODVALLEY and self.chapter_number:
            return f"Ch. {self.chapter_number} — {self.title}"
        return self.title

    @property
    def cover_url(self):
        return self.cover_image.url if self.cover_image else ''

    def get_absolute_url(self):
        from django.urls import reverse
        if self.category == self.Category.GODVALLEY:
            return reverse('godvalley_detail', args=[self.slug])
        return reverse('writings_detail', args=[self.category, self.slug])


class Subcategory(models.Model):
    """Admin-created sub-classification: which Fiction story, Philosophy topic, or Mythology
    tradition a Content row belongs to. Created inline from the Upload forms (or Django admin) —
    never hardcoded, so a new story/topic/tradition never needs a code change or migration. Not
    used for God Valley, which has exactly one implicit story.
    """
    parent_category = models.CharField(max_length=20, choices=Content.Category.choices)
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100)

    class Meta:
        ordering = ['name']
        constraints = [
            models.UniqueConstraint(fields=['parent_category', 'slug'], name='unique_subcategory_slug_per_parent'),
        ]

    def __str__(self):
        return f'{self.get_parent_category_display()} / {self.name}'


class Collection(models.Model):
    """Author-curated anthology: a named, ordered grouping of any mix of Content rows across
    categories (e.g. "Best of Philosophy", "God Valley: Arc One"). Created via the Collections
    card on the Upload hub (or Django admin) — visitors browse them publicly at /collections/.
    Slug is globally unique (no category axis) and generated server-side in save(), same as News.
    """
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    description = models.CharField(max_length=300, blank=True)
    cover_image = models.ImageField(upload_to='covers/collections/%Y/%m/', blank=True, null=True)
    is_published = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    contents = models.ManyToManyField(Content, through='CollectionItem', related_name='collections')

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.title)[:200] or 'collection'
            slug = base
            suffix = 1
            while Collection.objects.filter(slug=slug).exists():
                suffix += 1
                slug = f'{base}-{suffix}'[:220]
            self.slug = slug
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

    @property
    def cover_url(self):
        return self.cover_image.url if self.cover_image else ''

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('collection_detail', args=[self.slug])


class CollectionItem(models.Model):
    """One Content row's membership in a Collection, at an author-chosen position. Positions are
    only ever compared relatively (never renumbered after removals — the visitor page numbers rows
    via forloop.counter, so gaps are invisible). CASCADE from Content matches
    Favourite/ReadingListItem: deleting content silently drops its memberships, so the existing
    delete_content flow keeps working.
    """
    collection = models.ForeignKey(Collection, on_delete=models.CASCADE, related_name='items')
    content = models.ForeignKey(Content, on_delete=models.CASCADE, related_name='+')
    position = models.PositiveIntegerField()

    class Meta:
        ordering = ['position']
        constraints = [
            models.UniqueConstraint(fields=['collection', 'content'], name='unique_content_per_collection'),
        ]

    def __str__(self):
        return f'{self.collection} #{self.position}: {self.content}'


class ReadingHistory(models.Model):
    """One row per (user, content) a visitor has opened — deduped so re-reading something just
    bumps `viewed_at` (auto_now, not auto_now_add) rather than piling up duplicate rows. Recorded
    from core.views.writings_detail / godvalley_detail for authenticated users only, and surfaced
    as the "Reading History" panel on /profile/.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reading_history',
    )
    content = models.ForeignKey(Content, on_delete=models.CASCADE, related_name='+')
    viewed_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-viewed_at']
        verbose_name_plural = 'reading history'
        constraints = [
            models.UniqueConstraint(fields=['user', 'content'], name='unique_user_content_view'),
        ]

    def __str__(self):
        return f"{self.user} read {self.content}"


class Favourite(models.Model):
    """One row per (user, content) a visitor has hearted on a detail page — toggled from
    core.views.toggle_favourite, deduped the same way ReadingHistory is (a real unique
    constraint), and surfaced as the "Favourites" page linked from the side drawer.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='favourites',
    )
    content = models.ForeignKey(Content, on_delete=models.CASCADE, related_name='+')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(fields=['user', 'content'], name='unique_user_content_favourite'),
        ]

    def __str__(self):
        return f"{self.user} favourited {self.content}"


class ReadingListItem(models.Model):
    """One row per (user, content) a visitor has explicitly saved via the bookmark button on a
    detail page — toggled from core.views.toggle_reading_list_item, deduped the same way
    Favourite is (a real unique constraint), and surfaced as the "Reading List" page linked from
    the side drawer. Deliberately distinct from ReadingHistory: that one is an automatic view log,
    this one is a user-curated "save for later" list.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reading_list_items',
    )
    content = models.ForeignKey(Content, on_delete=models.CASCADE, related_name='+')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(fields=['user', 'content'], name='unique_user_content_reading_list'),
        ]

    def __str__(self):
        return f"{self.user} saved {self.content} to reading list"


class DownloadHistory(models.Model):
    """One row per (user, content) a visitor has downloaded as a PDF via the download button on a
    detail page — recorded from core.views.download_content, deduped the same way ReadingHistory
    is: `downloaded_at` is `auto_now` (not `auto_now_add`), so re-downloading something bumps it
    back to the top of the "Downloads" page instead of piling up duplicate rows. The PDF itself is
    generated on demand (via reportlab) and never stored — this table is just the history/log of
    what was downloaded and when, not a file store.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='download_history',
    )
    content = models.ForeignKey(Content, on_delete=models.CASCADE, related_name='+')
    downloaded_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-downloaded_at']
        verbose_name_plural = 'download history'
        constraints = [
            models.UniqueConstraint(fields=['user', 'content'], name='unique_user_content_download'),
        ]

    def __str__(self):
        return f"{self.user} downloaded {self.content}"


class News(models.Model):
    """Short dispatches/announcements — deliberately separate from Content, not another
    category on it: no chapters, no long-form body, just title/tag/body created via the
    admin-only 'New' modal on the News page (core.views.create_news). That form isn't Django
    admin, so unlike Content (which relies on admin's prepopulated_fields JS for slugs), the
    slug here is generated server-side in save().
    """

    class Tag(models.TextChoices):
        ANNOUNCEMENT = 'announcement', 'Announcement'
        NEWS = 'news', 'News'
        UPDATE = 'update', 'Update'

    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    tag = models.CharField(max_length=20, choices=Tag.choices, default=Tag.NEWS)
    body = models.TextField()
    cover_image = models.ImageField(upload_to='covers/news/%Y/%m/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'news'

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.title)[:200] or 'news'
            slug = base
            suffix = 1
            while News.objects.filter(slug=slug).exists():
                suffix += 1
                slug = f'{base}-{suffix}'[:220]
            self.slug = slug
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

    @property
    def cover_url(self):
        return self.cover_image.url if self.cover_image else ''
