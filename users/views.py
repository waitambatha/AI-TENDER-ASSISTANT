from django.shortcuts import render, redirect
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import CustomUserCreationForm, EmailVerificationForm, PhoneVerificationForm, VerificationSettingsForm, VerificationMethodForm
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
            user.save()
            request.session['user_pk_for_verification'] = user.pk
            
            # Check verification options and redirect accordingly
            both_enabled = settings_obj.email_verification_enabled and settings_obj.phone_verification_enabled
            
            if both_enabled:
                return redirect('choose_verification_method')
            elif settings_obj.email_verification_enabled:
                return redirect('send_email_verification')
            elif settings_obj.phone_verification_enabled:
                return redirect('send_phone_verification')
    else:
        form = CustomUserCreationForm()
    return render(request, 'registration/register.html', {'form': form})

def choose_verification_method(request):
    user_pk = request.session.get('user_pk_for_verification')
    if not user_pk:
        return redirect('register')
    
    if request.method == 'POST':
        form = VerificationMethodForm(request.POST)
        if form.is_valid():
            method = form.cleaned_data['verification_method']
            if method == 'email':
                return redirect('send_email_verification')
            elif method == 'phone':
                return redirect('send_phone_verification')
    else:
        form = VerificationMethodForm()
    
    return render(request, 'registration/choose_verification.html', {'form': form})

def send_email_verification(request):
    user_pk = request.session.get('user_pk_for_verification')
    if not user_pk:
        return redirect('register')
    
    try:
        user = CustomUser.objects.get(pk=user_pk)
        email_code = str(random.randint(100000, 999999))
        user.email_verification_code = email_code
        user.save()
        
        send_mail(
            'Your verification code',
            f'Your verification code is: {email_code}',
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False,
        )
        messages.success(request, 'Verification code sent to your email.')
        return redirect('verify_email')
    except Exception as e:
        messages.error(request, 'Failed to send email verification code.')
        return redirect('choose_verification_method')

def send_phone_verification(request):
    user_pk = request.session.get('user_pk_for_verification')
    if not user_pk:
        return redirect('register')
    
    try:
        user = CustomUser.objects.get(pk=user_pk)
        phone_code = str(random.randint(100000, 999999))
        user.phone_verification_code = phone_code
        user.save()
        
        if send_sms(user.phone_number, f'Your verification code is: {phone_code}'):
            messages.success(request, 'Verification code sent to your phone.')
            return redirect('verify_phone')
        else:
            messages.error(request, 'Failed to send SMS verification code.')
            return redirect('choose_verification_method')
    except Exception as e:
        messages.error(request, 'Failed to send SMS verification code.')
        return redirect('choose_verification_method')

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
