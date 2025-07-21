from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import PasswordChangeView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.views.generic import UpdateView
from django.contrib import messages
from django.contrib.auth.models import User
from django import forms
from .models import UserProfile


class UserProfileForm(forms.ModelForm):
    """Form for editing user profile information"""
    first_name = forms.CharField(max_length=30, required=False)
    last_name = forms.CharField(max_length=30, required=False)
    email = forms.EmailField(required=False)

    class Meta:
        model = UserProfile
        fields = ['avatar']
        widgets = {
            'avatar': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'})
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.user:
            self.fields['first_name'].initial = self.instance.user.first_name
            self.fields['last_name'].initial = self.instance.user.last_name
            self.fields['email'].initial = self.instance.user.email
        
        # Add CSS classes
        for field in self.fields:
            if field != 'avatar':
                self.fields[field].widget.attrs.update({'class': 'form-control'})

    def save(self, commit=True):
        profile = super().save(commit=False)
        if commit:
            # Save User fields
            user = profile.user
            user.first_name = self.cleaned_data['first_name']
            user.last_name = self.cleaned_data['last_name']
            user.email = self.cleaned_data['email']
            user.save()
            profile.save()
        return profile


@login_required
def profile_view(request):
    """Display user profile page"""
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    # Get user role from groups
    user_role = "User"
    if request.user.groups.exists():
        user_role = request.user.groups.first().name
    
    context = {
        'profile': profile,
        'user_role': user_role,
    }
    return render(request, 'profile/profile.html', context)


class ProfileEditView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    """Edit user profile view"""
    model = UserProfile
    form_class = UserProfileForm
    template_name = 'profile/edit_profile.html'
    success_url = reverse_lazy('profile')
    success_message = "Profile updated successfully!"

    def get_object(self):
        profile, created = UserProfile.objects.get_or_create(user=self.request.user)
        return profile


class CustomPasswordChangeView(LoginRequiredMixin, SuccessMessageMixin, PasswordChangeView):
    """Custom password change view"""
    template_name = 'profile/password_change.html'
    success_url = reverse_lazy('profile')
    success_message = "Password changed successfully!"
    
    def form_valid(self, form):
        """Override to ensure proper redirect"""
        response = super().form_valid(form)
        return response

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        # Add CSS classes to form fields
        for field in form.fields:
            form.fields[field].widget.attrs.update({'class': 'form-control'})
        return form
