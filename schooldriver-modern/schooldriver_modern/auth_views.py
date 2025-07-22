from django.contrib.auth.views import LoginView
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.http import HttpResponseRedirect
from django.contrib import messages
from django.shortcuts import render, redirect
from django.views.generic import CreateView
from django import forms
from .roles import get_redirect_url_for_user
from .middleware import check_login_allowed
from .models import SecurityEvent


class CustomLoginView(LoginView):
    """Custom login view with Remember Me functionality and role-based redirects."""
    
    template_name = 'registration/login.html'
    
    def form_valid(self, form):
        """Handle successful login with remember me functionality and role-based redirects."""
        username = form.cleaned_data.get('username')
        
        # Check if login is allowed (not locked out)
        allowed, message = check_login_allowed(username)
        if not allowed:
            form.add_error(None, message)
            return self.form_invalid(form)
        
        # Show warning if there have been failed attempts
        if message and "Warning" in message:
            messages.warning(self.request, message)
        
        # Check if remember me is checked
        remember_me = self.request.POST.get('remember_me')
        
        # Authenticate and login the user
        login(self.request, form.get_user())
        
        # Set session expiry based on remember me
        if remember_me:
            # Set session to expire in 30 days (30 * 24 * 60 * 60 = 2,592,000 seconds)
            self.request.session.set_expiry(2592000)
        else:
            # Use default session expiry (browser session)
            self.request.session.set_expiry(0)
        
        # Get role-based redirect URL
        redirect_url = get_redirect_url_for_user(form.get_user())
        
        return HttpResponseRedirect(redirect_url)


class CustomUserCreationForm(UserCreationForm):
    """Custom user creation form with additional fields."""
    
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    role = forms.ChoiceField(
        choices=[
            ('', 'Select your role'),
            ('parent', 'Parent'),
            ('student', 'Student'),
        ],
        required=True
    )
    
    class Meta:
        model = User
        fields = ("username", "email", "first_name", "last_name", "password1", "password2", "role")
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        user.first_name = self.cleaned_data["first_name"]
        user.last_name = self.cleaned_data["last_name"]
        
        if commit:
            user.save()
            # You can add role assignment logic here if needed
            # For now, we'll just save the user
        
        return user


class SignUpView(CreateView):
    """Custom signup view with role-based redirects."""
    
    form_class = CustomUserCreationForm
    template_name = 'registration/signup.html'
    
    def form_valid(self, form):
        """Handle successful signup."""
        user = form.save()
        
        # Log the user in automatically after signup
        login(self.request, user)
        
        # Add success message
        messages.success(self.request, f'Welcome to SchoolDriver Modern, {user.first_name}!')
        
        # Get role-based redirect URL
        redirect_url = get_redirect_url_for_user(user)
        
        return HttpResponseRedirect(redirect_url)
    
    def form_invalid(self, form):
        """Handle invalid form submission."""
        messages.error(self.request, 'Please correct the errors below.')
        return super().form_invalid(form)
