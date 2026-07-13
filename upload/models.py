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

    def __str__(self):
        if self.category == self.Category.GODVALLEY and self.chapter_number:
            return f"Ch. {self.chapter_number} — {self.title}"
        return self.title


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
