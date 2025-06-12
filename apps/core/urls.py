from django.urls import path
from . import views

urlpatterns = [
    path('config/', views.SystemConfigurationListView.as_view(), name='system-config'),
    path('health/', views.system_health, name='system-health'),
    path('analytics/', views.api_analytics, name='api-analytics'),
]
