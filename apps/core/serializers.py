from rest_framework import serializers
from .models import SystemConfiguration, APILog

class SystemConfigurationSerializer(serializers.ModelSerializer):
    class Meta:
        model = SystemConfiguration
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at')

class APILogSerializer(serializers.ModelSerializer):
    user_email = serializers.CharField(source='user.email', read_only=True)
    
    class Meta:
        model = APILog
        fields = '__all__'
        read_only_fields = ('timestamp',)
