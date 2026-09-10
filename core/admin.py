from django.contrib import admin
from .models import AuditLog
# Register your models here.
@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'user', 'action', 'model_name', 'object_repr', 'ip_address')
    list_filter = ('action', 'model_name', 'timestamp')
    search_fields = ('user__email', 'user__first_name', 'user__last_name', 'object_repr', 'details', 'ip_address')
    readonly_fields = ('user', 'action', 'model_name', 'object_id', 'object_repr', 'ip_address', 'user_agent', 'details', 'timestamp')
    ordering = ('-timestamp',)

    def has_add_permission(self, request):
        return False  # Nobody can manually add audit logs

    def has_delete_permission(self, request, obj=None):
        return False  # Nobody can delete audit logs

    def has_change_permission(self, request, obj=None):
        return False  # Nobody can edit audit logs