from django import forms
from django.contrib.auth.password_validation import validate_password
from .models import CustomUser, VerificationSettings

class CustomUserCreationForm(forms.ModelForm):
    username = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username'}))
    first_name = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First Name'}))
    last_name = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last Name'}))
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email'}))
    phone_number = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Phone Number'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'}), validators=[validate_password])
    confirm_password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm Password'}))

    class Meta:
        model = CustomUser
        fields = ('username', 'first_name', 'last_name', 'email', 'phone_number')

    def clean_confirm_password(self):
        password = self.cleaned_data.get('password')
        confirm_password = self.cleaned_data.get('confirm_password')
        if password and confirm_password and password != confirm_password:
            raise forms.ValidationError("Passwords don't match")
        return confirm_password

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
        return user

class EmailVerificationForm(forms.Form):
    code = forms.CharField(max_length=6, required=True, label='Verification Code', widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter code'}))

class PhoneVerificationForm(forms.Form):
    code = forms.CharField(max_length=6, required=True, label='Phone Verification Code', widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter SMS code'}))

class VerificationSettingsForm(forms.ModelForm):
    class Meta:
        model = VerificationSettings
        fields = ['email_verification_enabled', 'phone_verification_enabled']
        widgets = {
            'email_verification_enabled': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'phone_verification_enabled': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
