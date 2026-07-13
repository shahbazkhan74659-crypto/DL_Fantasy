from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import LoginHistory, User, VisitSession

admin.site.register(User, UserAdmin)


@admin.register(LoginHistory)
class LoginHistoryAdmin(admin.ModelAdmin):
    list_display = ('user', 'timestamp', 'ip_address')
    list_filter = ('user',)
    ordering = ('-timestamp',)
    readonly_fields = ('user', 'timestamp', 'ip_address')


@admin.register(VisitSession)
class VisitSessionAdmin(admin.ModelAdmin):
    list_display = ('user', 'date', 'started_at', 'last_seen_at', 'duration')
    list_filter = ('user', 'date')
    ordering = ('-started_at',)
    readonly_fields = ('user', 'date', 'started_at', 'last_seen_at')

    @admin.display(description='Duration')
    def duration(self, obj):
        minutes = int((obj.last_seen_at - obj.started_at).total_seconds() // 60)
        return f"{minutes // 60}h {minutes % 60}m" if minutes >= 60 else f"{minutes}m"
