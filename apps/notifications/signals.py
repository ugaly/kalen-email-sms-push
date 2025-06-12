from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .models import NotificationCategory, NotificationPreference

User = get_user_model()

@receiver(post_save, sender=User)
def create_default_notification_preferences(sender, instance, created, **kwargs):
    """Create default notification preferences for new users"""
    if created:
        # Get all categories and create preferences
        categories = NotificationCategory.objects.all()
        for category in categories:
            NotificationPreference.objects.get_or_create(
                user=instance,
                category=category,
                defaults={
                    'email_enabled': True,
                    'sms_enabled': True,
                    'push_enabled': True,
                    'frequency': 'immediate'
                }
            )
