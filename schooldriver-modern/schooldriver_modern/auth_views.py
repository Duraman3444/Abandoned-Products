from django.contrib.auth.views import LoginView
from django.contrib.auth import login
from django.http import HttpResponseRedirect


class CustomLoginView(LoginView):
    """Custom login view with Remember Me functionality."""
    
    template_name = 'registration/login.html'
    
    def form_valid(self, form):
        """Handle successful login with remember me functionality."""
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
        
        return HttpResponseRedirect(self.get_success_url())
