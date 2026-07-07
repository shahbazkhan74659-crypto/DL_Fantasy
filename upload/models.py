from django.conf import settings
from django.db import models


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
