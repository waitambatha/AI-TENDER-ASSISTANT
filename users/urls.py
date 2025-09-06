from django.urls import path
from .views import register, verify_email, verify_phone, verification_settings, choose_verification_method, send_email_verification, send_phone_verification

urlpatterns = [
    path('register/', register, name='register'),
    path('choose_verification/', choose_verification_method, name='choose_verification_method'),
    path('send_email_verification/', send_email_verification, name='send_email_verification'),
    path('send_phone_verification/', send_phone_verification, name='send_phone_verification'),
    path('verify_email/', verify_email, name='verify_email'),
    path('verify_phone/', verify_phone, name='verify_phone'),
    path('verification_settings/', verification_settings, name='verification_settings'),
]
