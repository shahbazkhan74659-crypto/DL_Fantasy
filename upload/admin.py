from django.contrib import admin

from .models import Content


@admin.register(Content)
class ContentAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'chapter_number', 'is_published', 'created_at')
    list_filter = ('category', 'is_published')
    search_fields = ('title', 'excerpt', 'body')
    prepopulated_fields = {'slug': ('title',)}
    ordering = ('category', 'chapter_number', '-created_at')
