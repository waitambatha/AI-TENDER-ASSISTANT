from django.urls import path
from .views import register, verify_email

urlpatterns = [
    path('register/', register, name='register'),
    path('verify_email/', verify_email, name='verify_email'),
]
