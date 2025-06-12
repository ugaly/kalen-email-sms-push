from django.contrib import admin
from .models import SystemConfiguration, APILog

@admin.register(SystemConfiguration)
class SystemConfigurationAdmin(admin.ModelAdmin):
    list_display = ('key', 'value_preview', 'is_active', 'updated_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('key', 'description')
    ordering = ('key',)
    
    def value_preview(self, obj):
        return obj.value[:50] + '...' if len(obj.value) > 50 else obj.value
    value_preview.short_description = 'Value'

@admin.register(APILog)
class APILogAdmin(admin.ModelAdmin):
    list_display = (
        'endpoint', 'method', 'user', 'response_status', 
        'response_time', 'timestamp'
    )
    list_filter = (
        'method', 'response_status', 'timestamp'
    )
    search_fields = ('endpoint', 'user__email', 'ip_address')
    readonly_fields = ('timestamp',)
    ordering = ('-timestamp',)
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')
