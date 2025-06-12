from django.urls import path
from . import views

urlpatterns = [
    # Notifications
    path('', views.NotificationListCreateView.as_view(), name='notification-list-create'),
    path('<uuid:pk>/', views.NotificationDetailView.as_view(), name='notification-detail'),
    path('<uuid:notification_id>/cancel/', views.cancel_notification, name='cancel-notification'),
    path('<uuid:notification_id>/retry/', views.retry_failed_notification, name='retry-notification'),
    
    # Templates
    path('templates/', views.NotificationTemplateListCreateView.as_view(), name='template-list-create'),
    
    # Categories
    path('categories/', views.NotificationCategoryListView.as_view(), name='category-list'),
    
    # Batches
    path('batches/', views.NotificationBatchListCreateView.as_view(), name='batch-list-create'),
    path('batches/create/', views.create_notification_batch, name='create-batch'),
    
    # Preferences
    path('preferences/', views.NotificationPreferenceListView.as_view(), name='preference-list'),
    
    # Bulk operations
    path('bulk/send/', views.send_bulk_notifications, name='bulk-send'),
    
    # Utilities
    path('stats/', views.notification_stats, name='notification-stats'),
    path('test/', views.test_notification, name='test-notification'),
]
