from django.contrib.auth.views import LoginView
from django.contrib.auth import login, authenticate
from django.http import HttpResponseRedirect
from django.contrib import messages
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
