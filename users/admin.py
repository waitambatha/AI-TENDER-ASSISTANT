from django.contrib import admin
from .models import CustomUser, VerificationSettings

admin.site.register(CustomUser)
admin.site.register(VerificationSettings)
