from rest_framework import serializers
from .models import (
    Notification, NotificationTemplate, NotificationCategory,
    NotificationBatch, NotificationPreference, NotificationLog
)

class NotificationCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationCategory
        fields = '__all__'

class NotificationTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationTemplate
        fields = '__all__'

class NotificationLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationLog
        fields = '__all__'

class NotificationSerializer(serializers.ModelSerializer):
    logs = NotificationLogSerializer(many=True, read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    
    class Meta:
        model = Notification
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at', 'sent_at', 'retry_count')

class CreateNotificationSerializer(serializers.ModelSerializer):
    users = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False,
        help_text="List of user IDs to send notification to"
    )
    
    class Meta:
        model = Notification
        fields = [
            'category', 'template', 'notification_type', 'subject', 
            'message', 'html_content', 'metadata', 'scheduled_at', 'users'
        ]
    
    def validate(self, attrs):
        notification_type = attrs.get('notification_type')
        
        if notification_type == 'email' and not attrs.get('subject'):
            raise serializers.ValidationError("Subject is required for email notifications")
        
        return attrs

class NotificationBatchSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationBatch
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'started_at', 'completed_at')

class NotificationPreferenceSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    
    class Meta:
        model = NotificationPreference
        fields = '__all__'
        read_only_fields = ('user', 'created_at', 'updated_at')

class BulkNotificationSerializer(serializers.Serializer):
    category = serializers.PrimaryKeyRelatedField(queryset=NotificationCategory.objects.all())
    template = serializers.PrimaryKeyRelatedField(
        queryset=NotificationTemplate.objects.all(), 
        required=False
    )
    notification_type = serializers.ChoiceField(choices=Notification.NOTIFICATION_TYPES)
    subject = serializers.CharField(max_length=200, required=False)
    message = serializers.CharField()
    metadata = serializers.JSONField(default=dict)
    scheduled_at = serializers.DateTimeField(required=False)
    
    # Targeting options
    user_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        help_text="Specific user IDs"
    )
    user_filters = serializers.JSONField(
        default=dict,
        help_text="Django ORM filters for users"
    )
    
    def validate(self, attrs):
        if not attrs.get('user_ids') and not attrs.get('user_filters'):
            raise serializers.ValidationError(
                "Either user_ids or user_filters must be provided"
            )
        return attrs
