from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from .models import (
    Notification, NotificationTemplate, NotificationCategory,
    NotificationBatch, NotificationPreference
)
from .serializers import (
    NotificationSerializer, CreateNotificationSerializer,
    NotificationTemplateSerializer, NotificationCategorySerializer,
    NotificationBatchSerializer, NotificationPreferenceSerializer,
    BulkNotificationSerializer
)
from .tasks import create_bulk_notifications, process_notification_batch
from .services import NotificationService

User = get_user_model()

class NotificationListCreateView(generics.ListCreateAPIView):
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['status', 'notification_type', 'category']
    search_fields = ['subject', 'message']
    ordering_fields = ['created_at', 'scheduled_at', 'sent_at']
    ordering = ['-created_at']
    
    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user).select_related(
            'category', 'template'
        )
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return CreateNotificationSerializer
        return NotificationSerializer
    
    def perform_create(self, serializer):
        print("Performing create notification")
        users = serializer.validated_data.pop('users', [self.request.user.id])
        notification_data = serializer.validated_data
        
        service = NotificationService()
        notifications = []
        
        for user_id in users:
            try:
                user = User.objects.get(id=user_id)
                notification = service.create_and_send_notification(
                    user=user,
                    **notification_data
                )
                notifications.append(notification)
            except User.DoesNotExist:
                continue
        
        return notifications

class NotificationDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)

class NotificationTemplateListCreateView(generics.ListCreateAPIView):
    queryset = NotificationTemplate.objects.filter(is_active=True)
    serializer_class = NotificationTemplateSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['template_type']

class NotificationCategoryListView(generics.ListAPIView):
    queryset = NotificationCategory.objects.all()
    serializer_class = NotificationCategorySerializer
    permission_classes = [permissions.IsAuthenticated]

class NotificationBatchListCreateView(generics.ListCreateAPIView):
    queryset = NotificationBatch.objects.all()
    serializer_class = NotificationBatchSerializer
    permission_classes = [permissions.IsAuthenticated]
    ordering = ['-created_at']

class NotificationPreferenceListView(generics.ListCreateAPIView):
    serializer_class = NotificationPreferenceSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return NotificationPreference.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def send_bulk_notifications(request):
    """Send bulk notifications to multiple users"""
    serializer = BulkNotificationSerializer(data=request.data)
    if serializer.is_valid():
        # Queue the bulk notification task
        task = create_bulk_notifications.delay(serializer.validated_data)
        
        return Response({
            'message': 'Bulk notifications queued successfully',
            'task_id': task.id
        }, status=status.HTTP_202_ACCEPTED)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def create_notification_batch(request):
    """Create and process a notification batch"""
    serializer = NotificationBatchSerializer(data=request.data)
    if serializer.is_valid():
        batch = serializer.save()
        
        # Queue the batch processing task
        task = process_notification_batch.delay(str(batch.id))
        
        return Response({
            'batch': NotificationBatchSerializer(batch).data,
            'task_id': task.id
        }, status=status.HTTP_201_CREATED)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def notification_stats(request):
    """Get notification statistics for the current user"""
    user = request.user
    
    stats = {
        'total_notifications': Notification.objects.filter(user=user).count(),
        'sent_notifications': Notification.objects.filter(user=user, status='sent').count(),
        'pending_notifications': Notification.objects.filter(user=user, status='pending').count(),
        'failed_notifications': Notification.objects.filter(user=user, status='failed').count(),
        'email_notifications': Notification.objects.filter(
            user=user, notification_type='email'
        ).count(),
        'sms_notifications': Notification.objects.filter(
            user=user, notification_type='sms'
        ).count(),
        'push_notifications': Notification.objects.filter(
            user=user, notification_type='push'
        ).count(),
    }
    
    return Response(stats)

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def test_notification(request):
    """Send a test notification"""
    notification_type = request.data.get('type', 'email')
    message = request.data.get('message', 'This is a test notification')
    subject = request.data.get('subject', 'Test Notification')
    
    # Get or create a test category
    from .models import NotificationCategory
    category, _ = NotificationCategory.objects.get_or_create(
        name='test',
        defaults={'description': 'Test notifications', 'priority': 1}
    )
    
    service = NotificationService()
    notification = service.create_and_send_notification(
        user=request.user,
        category=category,
        notification_type=notification_type,
        subject=subject,
        message=message,
        metadata={'test': True}
    )
    
    return Response({
        'message': 'Test notification sent',
        'notification_id': str(notification.id)
    }, status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def cancel_notification(request, notification_id):
    """Cancel a pending notification"""
    try:
        notification = Notification.objects.get(
            id=notification_id,
            user=request.user,
            status='pending'
        )
        
        notification.status = 'cancelled'
        notification.save()
        
        return Response({
            'message': 'Notification cancelled successfully'
        }, status=status.HTTP_200_OK)
        
    except Notification.DoesNotExist:
        return Response({
            'error': 'Notification not found or cannot be cancelled'
        }, status=status.HTTP_404_NOT_FOUND)

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def retry_failed_notification(request, notification_id):
    """Retry a failed notification"""
    try:
        notification = Notification.objects.get(
            id=notification_id,
            user=request.user,
            status='failed'
        )
        
        # Reset notification for retry
        notification.status = 'pending'
        notification.retry_count = 0
        notification.error_message = ''
        notification.scheduled_at = timezone.now()
        notification.save()
        
        # Queue the notification again
        from .tasks import send_email_notification, send_sms_notification, send_push_notification
        
        if notification.notification_type == 'email':
            send_email_notification.delay(str(notification.id))
        elif notification.notification_type == 'sms':
            send_sms_notification.delay(str(notification.id))
        elif notification.notification_type == 'push':
            send_push_notification.delay(str(notification.id))
        
        return Response({
            'message': 'Notification queued for retry'
        }, status=status.HTTP_200_OK)
        
    except Notification.DoesNotExist:
        return Response({
            'error': 'Failed notification not found'
        }, status=status.HTTP_404_NOT_FOUND)
