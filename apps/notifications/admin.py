from django.contrib import admin
from django.utils.html import format_html
from .models import (
    Notification, NotificationTemplate, NotificationCategory,
    NotificationBatch, NotificationPreference, NotificationLog
)

@admin.register(NotificationCategory)
class NotificationCategoryAdmin(admin.ModelAdmin):
    list_display = ( 'name', 'priority', 'max_per_hour', 'max_per_day', 'created_at')
    list_filter = ('priority', 'created_at')
    search_fields = ('name', 'description')
    ordering = ('priority', 'name')

@admin.register(NotificationTemplate)
class NotificationTemplateAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'template_type', 'html_template', 'is_active', 'created_at')
    list_filter = ('template_type', 'is_active', 'html_template', 'created_at')
    search_fields = ('name', 'subject', 'content')
    ordering = ('template_type', 'name')
    
    fieldsets = (
        (None, {
            'fields': ('name', 'template_type', 'is_active', 'subject', 'content')
        }),
        ('HTML Email Settings', {
            'fields': ('use_html_template', 'html_template', 'primary_color', 'logo_url', 'company_name')
        }),
        ('Template Variables', {
            'fields': ('variables',)
        }),
    )

class NotificationLogInline(admin.TabularInline):
    model = NotificationLog
    extra = 0
    readonly_fields = ('status', 'message', 'timestamp')

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'user_email', 'notification_type', 'status', 
        'category', 'created_at', 'sent_at'
    )
    list_filter = (
        'notification_type', 'status', 'category', 
        'created_at', 'sent_at'
    )
    search_fields = ('user__email', 'subject', 'message')
    readonly_fields = ('id', 'created_at', 'updated_at', 'sent_at')
    ordering = ('-created_at',)
    inlines = [NotificationLogInline]
    
    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'User Email'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'category', 'template')

@admin.register(NotificationBatch)
class NotificationBatchAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'status', 'total_notifications', 
        'sent_notifications', 'failed_notifications', 'created_at'
    )
    list_filter = ('status', 'created_at')
    search_fields = ('name', 'description')
    readonly_fields = (
        'id', 'created_at', 'started_at', 'completed_at',
        'total_notifications', 'sent_notifications', 'failed_notifications'
    )
    ordering = ('-created_at',)

@admin.register(NotificationPreference)
class NotificationPreferenceAdmin(admin.ModelAdmin):
    list_display = (
        'user', 'category', 'email_enabled', 
        'sms_enabled', 'push_enabled', 'frequency'
    )
    list_filter = ('category', 'frequency', 'email_enabled', 'sms_enabled', 'push_enabled')
    search_fields = ('user__email', 'category__name')
    ordering = ('user__email', 'category__name')
