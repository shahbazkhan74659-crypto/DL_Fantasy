from django.contrib import admin

from .models import Content, DownloadHistory, Favourite, News, ReadingHistory, ReadingListItem, Subcategory


@admin.register(Content)
class ContentAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'chapter_number', 'subcategory', 'is_published', 'created_at')
    list_filter = ('category', 'subcategory', 'is_published')
    search_fields = ('title', 'excerpt', 'body')
    prepopulated_fields = {'slug': ('title',)}
    ordering = ('category', 'chapter_number', '-created_at')


@admin.register(Subcategory)
class SubcategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'parent_category', 'slug')
    list_filter = ('parent_category',)
    prepopulated_fields = {'slug': ('name',)}
    ordering = ('parent_category', 'name')


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


@admin.register(ReadingListItem)
class ReadingListItemAdmin(admin.ModelAdmin):
    list_display = ('user', 'content', 'created_at')
    list_filter = ('user',)
    ordering = ('-created_at',)
    readonly_fields = ('user', 'content', 'created_at')


@admin.register(DownloadHistory)
class DownloadHistoryAdmin(admin.ModelAdmin):
    list_display = ('user', 'content', 'downloaded_at')
    list_filter = ('user',)
    ordering = ('-downloaded_at',)
    readonly_fields = ('user', 'content', 'downloaded_at')
