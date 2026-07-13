from django.contrib import admin

from .models import Content, Favourite, News, ReadingHistory


@admin.register(Content)
class ContentAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'chapter_number', 'is_published', 'created_at')
    list_filter = ('category', 'is_published')
    search_fields = ('title', 'excerpt', 'body')
    prepopulated_fields = {'slug': ('title',)}
    ordering = ('category', 'chapter_number', '-created_at')


@admin.register(News)
class NewsAdmin(admin.ModelAdmin):
    list_display = ('title', 'tag', 'created_at')
    list_filter = ('tag',)
    search_fields = ('title', 'body')
    prepopulated_fields = {'slug': ('title',)}
    ordering = ('-created_at',)


@admin.register(ReadingHistory)
class ReadingHistoryAdmin(admin.ModelAdmin):
    list_display = ('user', 'content', 'viewed_at')
    list_filter = ('user',)
    ordering = ('-viewed_at',)
    readonly_fields = ('user', 'content', 'viewed_at')


@admin.register(Favourite)
class FavouriteAdmin(admin.ModelAdmin):
    list_display = ('user', 'content', 'created_at')
    list_filter = ('user',)
    ordering = ('-created_at',)
    readonly_fields = ('user', 'content', 'created_at')
