from django.db import models
from users.models import CustomUser
from cryptography.fernet import Fernet
from django.conf import settings

class QueryCache(models.Model):
    question = models.TextField()
    response = models.TextField()
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']

class Document(models.Model):
    STATUS_CHOICES = (
        ('uploaded', 'Uploaded'),
        ('processing', 'Processing'),
        ('processed', 'Processed'),
        ('failed', 'Failed'),
    )

    uploaded_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    file = models.FileField(upload_to='documents/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='uploaded')
    summarized_file = models.FileField(upload_to='summaries/', blank=True, null=True)

    def __str__(self):
        return self.file.name

class SearchLog(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    query = models.TextField()
    results = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']

class UserAPIKey(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    encrypted_key = models.TextField()
    is_active = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def set_api_key(self, api_key):
        key = getattr(settings, 'ENCRYPTION_KEY', Fernet.generate_key()).encode()
        f = Fernet(key)
        self.encrypted_key = f.encrypt(api_key.encode()).decode()
    
    def get_api_key(self):
        key = getattr(settings, 'ENCRYPTION_KEY', None)
        if key:
            f = Fernet(key.encode())
            return f.decrypt(self.encrypted_key.encode()).decode()
        return None
    
    class Meta:
        unique_together = ['user', 'name']