from django.shortcuts import render, redirect
from django.core.mail import send_mail
from django.conf import settings
from .forms import CustomUserCreationForm, EmailVerificationForm
from .models import CustomUser
import random

def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False
            code = str(random.randint(100000, 999999))
            user.email_verification_code = code
            user.save()
            send_mail(
                'Your verification code',
                f'Your verification code is: {code}',
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=False,
            )
            # Store user's pk in session to retrieve after verification
            request.session['user_pk_for_verification'] = user.pk
            return redirect('verify_email')
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
                user.is_active = True
                user.is_email_verified = True
                user.email_verification_code = ''
                user.save()
                del request.session['user_pk_for_verification']
                return redirect('login')
            except CustomUser.DoesNotExist:
                form.add_error('code', 'Invalid verification code')
    else:
        form = EmailVerificationForm()
    return render(request, 'registration/verify_email.html', {'form': form})

def root_redirect_view(request):
    return redirect('login')
