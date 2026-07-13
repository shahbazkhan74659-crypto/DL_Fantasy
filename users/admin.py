from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import DeletedUser, LoginHistory, User, VisitSession

admin.site.register(User, UserAdmin)


@admin.register(DeletedUser)
class DeletedUserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'was_staff', 'was_superuser', 'deleted_at', 'deleted_by')
    list_filter = ('was_staff', 'was_superuser')
    ordering = ('-deleted_at',)
    readonly_fields = (
        'username', 'email', 'date_joined', 'was_staff', 'was_superuser', 'deleted_at', 'deleted_by',
    )

    def has_add_permission(self, request):
        return False


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
