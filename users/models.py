from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    email_verification_code = models.CharField(max_length=6, blank=True, null=True)
    phone_verification_code = models.CharField(max_length=6, blank=True, null=True)
    is_email_verified = models.BooleanField(default=False)
    is_phone_verified = models.BooleanField(default=False)

    def __str__(self):
        return self.username

class VerificationSettings(models.Model):
    email_verification_enabled = models.BooleanField(default=True)
    phone_verification_enabled = models.BooleanField(default=False)
    
    class Meta:
        verbose_name = "Verification Settings"
        verbose_name_plural = "Verification Settings"
    
    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)
    
    @classmethod
    def get_settings(cls):
        obj, created = cls.objects.get_or_create(pk=1)
        return obj