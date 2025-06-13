from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
import uuid

User = get_user_model()

class NotificationTemplate(models.Model):
    TEMPLATE_TYPES = [
        ('email', 'Email'),
        ('sms', 'SMS'),
        ('push', 'Push Notification'),
    ]
    
    EMAIL_TEMPLATE_CHOICES = [
        ('order_placed_email.html', 'Order Placed'),
        ('order_shipped_email.html', 'Order Shipped'),
        ('order_delivered_email.html', 'Order Delivered'),
        ('security_alert_email.html', 'Security Alert'),
        ('marketing_email.html', 'Marketing'),
        ('base_email_template.html', 'Generic Email'),
    ]
    
    name = models.CharField(max_length=100)
    template_type = models.CharField(max_length=10, choices=TEMPLATE_TYPES)
    subject = models.CharField(max_length=200, blank=True)  # just kwaajili ya email tu
    content = models.TextField()
    html_template = models.CharField(
        max_length=100, 
        choices=EMAIL_TEMPLATE_CHOICES, 
        blank=True,
        help_text="HTML template file to use for email"
    )
    use_html_template = models.BooleanField(default=True)
    variables = models.JSONField(default=dict, help_text="Template variables as JSON")
    is_active = models.BooleanField(default=True)
    
    # Styling options for emails
    primary_color = models.CharField(max_length=20, default='#4CAF50', blank=True)
    logo_url = models.URLField(blank=True)
    company_name = models.CharField(max_length=100, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'notification_templates'
        unique_together = ['name', 'template_type']
        indexes = [
            models.Index(fields=['template_type', 'is_active']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.template_type})"

class NotificationCategory(models.Model):
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    priority = models.IntegerField(default=1, help_text="1=Low, 2=Medium, 3=High, 4=Critical")
    
    primary_color = models.CharField(max_length=20, default='#4CAF50', blank=True)
    default_email_template = models.CharField(
        max_length=100, 
        choices=NotificationTemplate.EMAIL_TEMPLATE_CHOICES,
        default='base_email_template.html',
        blank=True
    )
    
    max_per_hour = models.IntegerField(default=100)
    max_per_day = models.IntegerField(default=1000)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'notification_categories'
        verbose_name_plural = 'Notification Categories'
    
    def __str__(self):
        return self.name

class Notification(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('sent', 'Sent'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    
    NOTIFICATION_TYPES = [
        ('email', 'Email'),
        ('sms', 'SMS'),
        ('push', 'Push Notification'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    category = models.ForeignKey(NotificationCategory, on_delete=models.CASCADE)
    template = models.ForeignKey(NotificationTemplate, on_delete=models.SET_NULL, null=True, blank=True)
    
    notification_type = models.CharField(max_length=10, choices=NOTIFICATION_TYPES)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='pending')
    
    subject = models.CharField(max_length=200, blank=True)
    message = models.TextField()
    html_content = models.TextField(blank=True)
    metadata = models.JSONField(default=dict)
    
    recipient_email = models.EmailField(blank=True, null=True)
    recipient_phone = models.CharField(max_length=20, blank=True, null=True)
    
    scheduled_at = models.DateTimeField(null=True, blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    
    retry_count = models.IntegerField(default=0)
    max_retries = models.IntegerField(default=3)
    
    error_message = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'notifications'
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['notification_type', 'status']),
            models.Index(fields=['scheduled_at']),
            models.Index(fields=['created_at']),
            models.Index(fields=['category', 'status']),
        ]
    
    def __str__(self):
        return f"{self.notification_type} to {self.user.email} - {self.status}"

class NotificationLog(models.Model):
    notification = models.ForeignKey(Notification, on_delete=models.CASCADE, related_name='logs')
    status = models.CharField(max_length=15)
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'notification_logs'
        indexes = [
            models.Index(fields=['notification', 'timestamp']),
        ]

class NotificationBatch(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='pending')
    
    total_notifications = models.IntegerField(default=0)
    sent_notifications = models.IntegerField(default=0)
    failed_notifications = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'notification_batches'
    
    def __str__(self):
        return f"Batch: {self.name} ({self.status})"

class NotificationPreference(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notification_preferences')
    category = models.ForeignKey(NotificationCategory, on_delete=models.CASCADE)
    
    email_enabled = models.BooleanField(default=True)
    sms_enabled = models.BooleanField(default=True)
    push_enabled = models.BooleanField(default=True)
    
    frequency = models.CharField(
        max_length=20,
        choices=[
            ('immediate', 'Immediate'),
            ('hourly', 'Hourly Digest'),
            ('daily', 'Daily Digest'),
            ('weekly', 'Weekly Digest'),
        ],
        default='immediate'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'notification_preferences'
        unique_together = ['user', 'category']




