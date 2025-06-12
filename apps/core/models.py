from django.db import models

class SystemConfiguration(models.Model):
    key = models.CharField(max_length=100, unique=True)
    value = models.TextField()
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'system_configurations'
    
    def __str__(self):
        return f"{self.key}: {self.value[:50]}"

class APILog(models.Model):
    endpoint = models.CharField(max_length=200)
    method = models.CharField(max_length=10)
    user = models.ForeignKey(
        'accounts.User', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True
    )
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True)
    request_data = models.JSONField(default=dict)
    response_status = models.IntegerField()
    response_time = models.FloatField()  # in milliseconds
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'api_logs'
        indexes = [
            models.Index(fields=['endpoint', 'timestamp']),
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['response_status', 'timestamp']),
        ]
    
    def __str__(self):
        return f"{self.method} {self.endpoint} - {self.response_status}"
