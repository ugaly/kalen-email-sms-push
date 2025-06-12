from rest_framework import generics, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.db.models import Count, Avg, Q
from django.utils import timezone
from datetime import timedelta
from .models import SystemConfiguration, APILog
from .serializers import SystemConfigurationSerializer, APILogSerializer

class SystemConfigurationListView(generics.ListAPIView):
    queryset = SystemConfiguration.objects.filter(is_active=True)
    serializer_class = SystemConfigurationSerializer
    permission_classes = [permissions.IsAuthenticated]

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def system_health(request):
    """Get system health status"""
    from apps.notifications.models import Notification
    
    now = timezone.now()
    last_hour = now - timedelta(hours=1)
    last_day = now - timedelta(days=1)
    
    health_data = {
        'status': 'healthy',
        'timestamp': now,
        'notifications': {
            'last_hour': {
                'total': Notification.objects.filter(created_at__gte=last_hour).count(),
                'sent': Notification.objects.filter(
                    sent_at__gte=last_hour, status='sent'
                ).count(),
                'failed': Notification.objects.filter(
                    updated_at__gte=last_hour, status='failed'
                ).count(),
            },
            'last_day': {
                'total': Notification.objects.filter(created_at__gte=last_day).count(),
                'sent': Notification.objects.filter(
                    sent_at__gte=last_day, status='sent'
                ).count(),
                'failed': Notification.objects.filter(
                    updated_at__gte=last_day, status='failed'
                ).count(),
            }
        },
        'api': {
            'last_hour': {
                'requests': APILog.objects.filter(timestamp__gte=last_hour).count(),
                'avg_response_time': APILog.objects.filter(
                    timestamp__gte=last_hour
                ).aggregate(avg_time=Avg('response_time'))['avg_time'] or 0,
                'error_rate': APILog.objects.filter(
                    timestamp__gte=last_hour,
                    response_status__gte=400
                ).count()
            }
        }
    }
    
    # Determine overall health status
    error_rate = health_data['api']['last_hour']['error_rate']
    total_requests = health_data['api']['last_hour']['requests']
    
    if total_requests > 0:
        error_percentage = (error_rate / total_requests) * 100
        if error_percentage > 10:
            health_data['status'] = 'degraded'
        elif error_percentage > 25:
            health_data['status'] = 'unhealthy'
    
    return Response(health_data)

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def api_analytics(request):
    """Get API usage analytics"""
    days = int(request.GET.get('days', 7))
    start_date = timezone.now() - timedelta(days=days)
    
    analytics = APILog.objects.filter(timestamp__gte=start_date).aggregate(
        total_requests=Count('id'),
        avg_response_time=Avg('response_time'),
        error_count=Count('id', filter=Q(response_status__gte=400))
    )
    
    top_endpoints = APILog.objects.filter(
        timestamp__gte=start_date
    ).values('endpoint').annotate(
        count=Count('id'),
        avg_time=Avg('response_time')
    ).order_by('-count')[:10]
    
    return Response({
        'period_days': days,
        'summary': analytics,
        'top_endpoints': list(top_endpoints)
    })
