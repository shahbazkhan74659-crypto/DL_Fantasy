from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import DailyVisit, LoginHistory, User

admin.site.register(User, UserAdmin)


@admin.register(LoginHistory)
class LoginHistoryAdmin(admin.ModelAdmin):
    list_display = ('user', 'timestamp', 'ip_address')
    list_filter = ('user',)
    ordering = ('-timestamp',)
    readonly_fields = ('user', 'timestamp', 'ip_address')


@admin.register(DailyVisit)
class DailyVisitAdmin(admin.ModelAdmin):
    list_display = ('user', 'date')
    list_filter = ('user',)
    ordering = ('-date',)
    readonly_fields = ('user', 'date')
