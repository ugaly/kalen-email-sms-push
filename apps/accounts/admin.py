from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, UserProfile

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('email', 'username', 'is_active', 'is_staff', 'created_at')
    list_filter = ('is_active', 'is_staff', 'is_superuser', 'created_at')
    search_fields = ('email', 'username', 'phone_number')
    ordering = ('-created_at',)
    
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Additional Info', {
            'fields': ('phone_number', 'is_email_verified', 'is_phone_verified')
        }),
        ('Notification Preferences', {
            'fields': ('email_notifications_enabled', 'sms_notifications_enabled', 'push_notifications_enabled')
        }),
    )

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'location', 'timezone', 'created_at')
    search_fields = ('user__email', 'location')
    list_filter = ('timezone', 'created_at')
