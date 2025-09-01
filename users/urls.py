from django.urls import path
from .views import register, verify_email, verify_phone, verification_settings

urlpatterns = [
    path('register/', register, name='register'),
    path('verify_email/', verify_email, name='verify_email'),
    path('verify_phone/', verify_phone, name='verify_phone'),
    path('verification_settings/', verification_settings, name='verification_settings'),
]
