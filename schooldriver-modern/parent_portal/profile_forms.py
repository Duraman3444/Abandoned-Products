from django import forms
from django.contrib.auth.models import User
from django.conf import settings
from schooldriver_modern.models import UserProfile


class ParentProfileForm(forms.ModelForm):
    """Form for updating parent profile information including language preference"""
    
    # User fields
    first_name = forms.CharField(
        max_length=30,
        widget=forms.TextInput(attrs={
            'class': 'form-control bg-dark border-secondary text-light',
            'placeholder': 'First Name'
        })
    )
    last_name = forms.CharField(
        max_length=30,
        widget=forms.TextInput(attrs={
            'class': 'form-control bg-dark border-secondary text-light',
            'placeholder': 'Last Name'
        })
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control bg-dark border-secondary text-light',
            'placeholder': 'Email Address'
        })
    )
    
    class Meta:
        model = UserProfile
        fields = [
            'phone_number', 'address', 'preferred_language',
            'email_notifications', 'sms_notifications'
        ]
        widgets = {
            'phone_number': forms.TextInput(attrs={
                'class': 'form-control bg-dark border-secondary text-light',
                'placeholder': '(555) 123-4567'
            }),
            'address': forms.Textarea(attrs={
                'class': 'form-control bg-dark border-secondary text-light',
                'rows': 3,
                'placeholder': 'Home Address'
            }),
            'preferred_language': forms.Select(attrs={
                'class': 'form-select bg-dark border-secondary text-light'
            }),
            'email_notifications': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'sms_notifications': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Set language choices from settings
        self.fields['preferred_language'].choices = settings.LANGUAGES
        
        # Populate user fields if user exists
        if self.user:
            self.fields['first_name'].initial = self.user.first_name
            self.fields['last_name'].initial = self.user.last_name
            self.fields['email'].initial = self.user.email
    
    def save(self, commit=True):
        # Save profile
        profile = super().save(commit=False)
        
        # Update user fields
        if self.user:
            self.user.first_name = self.cleaned_data['first_name']
            self.user.last_name = self.cleaned_data['last_name']
            self.user.email = self.cleaned_data['email']
            
            if commit:
                self.user.save()
                profile.save()
        
        return profile
