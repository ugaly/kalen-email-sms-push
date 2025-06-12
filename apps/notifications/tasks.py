import logging
from celery import shared_task
from django.core.mail import send_mail, EmailMultiAlternatives
from django.conf import settings
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.db import transaction
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from .models import Notification, NotificationBatch, NotificationLog
from .services import EmailService, SMSService, PushNotificationService
from datetime import timedelta

User = get_user_model()
logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_email_notification(self, notification_id):
    """Send email notification with retry mechanism"""
    try:
        notification = Notification.objects.get(id=notification_id)
        
        if notification.status != 'pending':
            logger.info(f"Notification {notification_id} already processed")
            return
        
        notification.status = 'processing'
        notification.save()
        
        NotificationLog.objects.create(
            notification=notification,
            status='processing',
            message='Starting email send process'
        )
        
        email_service = EmailService()
        success = email_service.send_email(
            to_email=notification.recipient_email or notification.user.email,
            subject=notification.subject,
            message=notification.message,
            use_html=notification.template.name,
            first_name=notification.user.first_name if notification.user else None,
            last_name=notification.user.last_name if notification.user else None,
            templete_content=notification.template.content if notification.template else None,
            primary_color=notification.template.primary_color if notification.template else None,
            metadata=notification.metadata,
            
        )
        
        if success:
            notification.status = 'sent'
            notification.sent_at = timezone.now()
            notification.save()
            
            NotificationLog.objects.create(
                notification=notification,
                status='sent',
                message='Email sent successfully'
            )
            
            logger.info(f"Email notification {notification_id} sent successfully")
        else:
            raise Exception("Email service returned failure")
            
    except Notification.DoesNotExist:
        logger.error(f"Notification {notification_id} not found")
        return
    
    except Exception as exc:
        notification.retry_count += 1
        notification.error_message = str(exc)
        
        if notification.retry_count >= notification.max_retries:
            notification.status = 'failed'
            NotificationLog.objects.create(
                notification=notification,
                status='failed',
                message=f'Max retries exceeded: {str(exc)}'
            )
            logger.error(f"Email notification {notification_id} failed permanently: {exc}")
        else:
            notification.status = 'pending'
            NotificationLog.objects.create(
                notification=notification,
                status='retry',
                message=f'Retry {notification.retry_count}: {str(exc)}'
            )
            logger.warning(f"Email notification {notification_id} failed, retrying: {exc}")
            
            countdown = 60 * (2 ** notification.retry_count)
            raise self.retry(exc=exc, countdown=countdown)
        
        notification.save()

@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_sms_notification(self, notification_id):
    """Send SMS notification with retry mechanism"""
    try:
        notification = Notification.objects.get(id=notification_id)
        
        if notification.status != 'pending':
            return
        
        notification.status = 'processing'
        notification.save()
        
        NotificationLog.objects.create(
            notification=notification,
            status='processing',
            message='Starting SMS send process'
        )
        
        sms_service = SMSService()
        success = sms_service.send_sms(
            to_phone=notification.recipient_phone or notification.user.phone_number,
            message=notification.message,
            metadata=notification.metadata
        )
        
        if success:
            notification.status = 'sent'
            notification.sent_at = timezone.now()
            notification.save()
            
            NotificationLog.objects.create(
                notification=notification,
                status='sent',
                message='SMS sent successfully'
            )
            
            logger.info(f"SMS notification {notification_id} sent successfully")
        else:
            raise Exception("SMS service returned failure")
            
    except Notification.DoesNotExist:
        logger.error(f"Notification {notification_id} not found")
        return
    
    except Exception as exc:
        notification.retry_count += 1
        notification.error_message = str(exc)
        
        if notification.retry_count >= notification.max_retries:
            notification.status = 'failed'
            NotificationLog.objects.create(
                notification=notification,
                status='failed',
                message=f'Max retries exceeded: {str(exc)}'
            )
        else:
            notification.status = 'pending'
            NotificationLog.objects.create(
                notification=notification,
                status='retry',
                message=f'Retry {notification.retry_count}: {str(exc)}'
            )
            countdown = 60 * (2 ** notification.retry_count)
            raise self.retry(exc=exc, countdown=countdown)
        
        notification.save()

@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_push_notification(self, notification_id):
    """Send push notification with retry mechanism"""
    try:
        notification = Notification.objects.get(id=notification_id)
        
        if notification.status != 'pending':
            return
        
        notification.status = 'processing'
        notification.save()
        
        push_service = PushNotificationService()
        success = push_service.send_push(
            user=notification.user,
            title=notification.subject,
            message=notification.message,
            metadata=notification.metadata
        )
        
        if success:
            notification.status = 'sent'
            notification.sent_at = timezone.now()
            notification.save()
            
            NotificationLog.objects.create(
                notification=notification,
                status='sent',
                message='Push notification sent successfully'
            )
        else:
            raise Exception("Push notification service returned failure")
            
    except Exception as exc:
        notification.retry_count += 1
        notification.error_message = str(exc)
        
        if notification.retry_count >= notification.max_retries:
            notification.status = 'failed'
        else:
            notification.status = 'pending'
            countdown = 60 * (2 ** notification.retry_count)
            raise self.retry(exc=exc, countdown=countdown)
        
        notification.save()

@shared_task
def process_pending_notifications():
    """Process pending notifications that are ready to be sent"""
    now = timezone.now()
    
    pending_notifications = Notification.objects.filter(
        status='pending',
        scheduled_at__lte=now
    ).select_related('user', 'category')[:100]  # Process in batches
    
    for notification in pending_notifications:
        if not _should_send_notification(notification):
            notification.status = 'cancelled'
            notification.save()
            continue
        
        if notification.notification_type == 'email':
            send_email_notification.delay(str(notification.id))
        elif notification.notification_type == 'sms':
            send_sms_notification.delay(str(notification.id))
        elif notification.notification_type == 'push':
            send_push_notification.delay(str(notification.id))

def _should_send_notification(notification):
    """Check if notification should be sent based on user preferences"""
    user = notification.user
    
    if notification.notification_type == 'email' and not user.email_notifications_enabled:
        return False
    if notification.notification_type == 'sms' and not user.sms_notifications_enabled:
        return False
    if notification.notification_type == 'push' and not user.push_notifications_enabled:
        return False
    
    if hasattr(user, 'profile') and user.profile.quiet_hours_start and user.profile.quiet_hours_end:
        current_time = timezone.now().time()
        if user.profile.quiet_hours_start <= current_time <= user.profile.quiet_hours_end:
            return False
    
    return True

@shared_task
def process_notification_batch(batch_id):
    """Process a batch of notifications"""
    try:
        batch = NotificationBatch.objects.get(id=batch_id)
        batch.status = 'processing'
        batch.started_at = timezone.now()
        batch.save()
        
        notifications = Notification.objects.filter(
            metadata__batch_id=str(batch_id),
            status='pending'
        )
        
        batch.total_notifications = notifications.count()
        batch.save()
        
        for notification in notifications:
            if notification.notification_type == 'email':
                send_email_notification.delay(str(notification.id))
            elif notification.notification_type == 'sms':
                send_sms_notification.delay(str(notification.id))
            elif notification.notification_type == 'push':
                send_push_notification.delay(str(notification.id))
        
        batch.status = 'completed'
        batch.completed_at = timezone.now()
        batch.save()
        
    except NotificationBatch.DoesNotExist:
        logger.error(f"Notification batch {batch_id} not found")

@shared_task
def cleanup_old_notifications():
    """Clean up old notifications and logs"""
    cutoff_date = timezone.now() - timedelta(days=30)
    
    deleted_logs = NotificationLog.objects.filter(
        timestamp__lt=cutoff_date
    ).delete()
    
    deleted_notifications = Notification.objects.filter(
        status='sent',
        sent_at__lt=cutoff_date
    ).delete()
    
    logger.info(f"Cleaned up {deleted_logs[0]} logs and {deleted_notifications[0]} notifications")

@shared_task
def generate_notification_reports():
    """Generate daily notification reports"""
    yesterday = timezone.now().date() - timedelta(days=1)
    
    stats = {
        'total_sent': Notification.objects.filter(
            sent_at__date=yesterday,
            status='sent'
        ).count(),
        'total_failed': Notification.objects.filter(
            updated_at__date=yesterday,
            status='failed'
        ).count(),
        'email_sent': Notification.objects.filter(
            sent_at__date=yesterday,
            status='sent',
            notification_type='email'
        ).count(),
        'sms_sent': Notification.objects.filter(
            sent_at__date=yesterday,
            status='sent',
            notification_type='sms'
        ).count(),
        'push_sent': Notification.objects.filter(
            sent_at__date=yesterday,
            status='sent',
            notification_type='push'
        ).count(),
    }
    
    logger.info(f"Daily notification report for {yesterday}: {stats}")
    
    return stats

@shared_task
def create_bulk_notifications(data):
    """Create bulk notifications from serialized data"""
    from .serializers import BulkNotificationSerializer
    
    serializer = BulkNotificationSerializer(data=data)
    if not serializer.is_valid():
        logger.error(f"Invalid bulk notification data: {serializer.errors}")
        return
    
    validated_data = serializer.validated_data
    
    if validated_data.get('user_ids'):
        users = User.objects.filter(id__in=validated_data['user_ids'])
    else:
        users = User.objects.filter(**validated_data.get('user_filters', {}))
    
    notifications = []
    for user in users:
        notification = Notification(
            user=user,
            category=validated_data['category'],
            template=validated_data.get('template'),
            notification_type=validated_data['notification_type'],
            subject=validated_data.get('subject', ''),
            message=validated_data['message'],
            metadata=validated_data.get('metadata', {}),
            scheduled_at=validated_data.get('scheduled_at', timezone.now()),
        )
        
        if notification.notification_type == 'email':
            notification.recipient_email = user.email
        elif notification.notification_type == 'sms':
            notification.recipient_phone = user.phone_number
        
        notifications.append(notification)
    
    created_notifications = Notification.objects.bulk_create(notifications, batch_size=1000)
    
    logger.info(f"Created {len(created_notifications)} bulk notifications")
    return len(created_notifications)
