from django.shortcuts import render, redirect
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import CustomUserCreationForm, EmailVerificationForm, PhoneVerificationForm, VerificationSettingsForm
from .models import CustomUser, VerificationSettings
from .sms_service import send_sms
import random

def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            settings_obj = VerificationSettings.get_settings()
            user = form.save(commit=False)
            
            # Check if any verification is needed
            if not settings_obj.email_verification_enabled and not settings_obj.phone_verification_enabled:
                user.is_active = True
                user.is_email_verified = True
                user.is_phone_verified = True
                user.save()
                messages.success(request, 'Account created successfully! You can now login.')
                return redirect('login')
            
            user.is_active = False
            
            # Generate codes if verification is enabled
            if settings_obj.email_verification_enabled:
                email_code = str(random.randint(100000, 999999))
                user.email_verification_code = email_code
                try:
                    send_mail(
                        'Your verification code',
                        f'Your verification code is: {email_code}',
                        settings.DEFAULT_FROM_EMAIL,
                        [user.email],
                        fail_silently=False,
                    )
                except Exception as e:
                    messages.error(request, 'Failed to send email verification code.')
                    return render(request, 'registration/register.html', {'form': form})
            
            if settings_obj.phone_verification_enabled:
                phone_code = str(random.randint(100000, 999999))
                user.phone_verification_code = phone_code
                if not send_sms(user.phone_number, f'Your verification code is: {phone_code}'):
                    messages.error(request, 'Failed to send SMS verification code.')
                    return render(request, 'registration/register.html', {'form': form})
            
            user.save()
            request.session['user_pk_for_verification'] = user.pk
            
            # Redirect based on what verification is enabled
            if settings_obj.email_verification_enabled:
                return redirect('verify_email')
            elif settings_obj.phone_verification_enabled:
                return redirect('verify_phone')
    else:
        form = CustomUserCreationForm()
    return render(request, 'registration/register.html', {'form': form})

def verify_email(request):
    if request.method == 'POST':
        form = EmailVerificationForm(request.POST)
        user_pk = request.session.get('user_pk_for_verification')
        if form.is_valid() and user_pk:
            code = form.cleaned_data['code']
            try:
                user = CustomUser.objects.get(pk=user_pk, email_verification_code=code)
                user.is_email_verified = True
                user.email_verification_code = ''
                
                settings_obj = VerificationSettings.get_settings()
                
                # Check if phone verification is also needed
                if settings_obj.phone_verification_enabled and not user.is_phone_verified:
                    user.save()
                    messages.success(request, 'Email verified! Now verify your phone number.')
                    return redirect('verify_phone')
                else:
                    user.is_active = True
                    user.save()
                    del request.session['user_pk_for_verification']
                    messages.success(request, 'Account verified successfully! You can now login.')
                    return redirect('login')
            except CustomUser.DoesNotExist:
                form.add_error('code', 'Invalid verification code')
    else:
        form = EmailVerificationForm()
    return render(request, 'registration/verify_email.html', {'form': form})

def verify_phone(request):
    if request.method == 'POST':
        form = PhoneVerificationForm(request.POST)
        user_pk = request.session.get('user_pk_for_verification')
        if form.is_valid() and user_pk:
            code = form.cleaned_data['code']
            try:
                user = CustomUser.objects.get(pk=user_pk, phone_verification_code=code)
                user.is_phone_verified = True
                user.phone_verification_code = ''
                
                settings_obj = VerificationSettings.get_settings()
                
                # Check if email verification is also needed
                if settings_obj.email_verification_enabled and not user.is_email_verified:
                    user.save()
                    messages.success(request, 'Phone verified! Now verify your email address.')
                    return redirect('verify_email')
                else:
                    user.is_active = True
                    user.save()
                    del request.session['user_pk_for_verification']
                    messages.success(request, 'Account verified successfully! You can now login.')
                    return redirect('login')
            except CustomUser.DoesNotExist:
                form.add_error('code', 'Invalid verification code')
    else:
        form = PhoneVerificationForm()
    return render(request, 'registration/verify_phone.html', {'form': form})

@login_required
def verification_settings(request):
    if not request.user.is_staff:
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
    
    settings_obj = VerificationSettings.get_settings()
    
    if request.method == 'POST':
        form = VerificationSettingsForm(request.POST, instance=settings_obj)
        if form.is_valid():
            form.save()
            messages.success(request, 'Verification settings updated successfully.')
            return redirect('verification_settings')
    else:
        form = VerificationSettingsForm(instance=settings_obj)
    
    return render(request, 'users/verification_settings.html', {'form': form, 'settings': settings_obj})

def root_redirect_view(request):
    return redirect('login')
