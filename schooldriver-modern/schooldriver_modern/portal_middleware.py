"""
Portal Access Control Middleware

Ensures users can only access portals they're authorized for.
"""

from django.http import HttpResponseRedirect
from django.urls import reverse
from django.contrib import messages
from django.shortcuts import redirect
from .roles import get_user_role, UserRoles
import logging

logger = logging.getLogger(__name__)


class PortalAccessMiddleware:
    """Middleware to control access to different portals based on user roles."""
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Process the request before the view
        response = self.process_request(request)
        if response:
            return response
        
        # Get the response from the view
        response = self.get_response(request)
        return response

    def process_request(self, request):
        """Process the request to check portal access permissions."""
        
        # Skip middleware for certain paths
        skip_paths = [
            '/accounts/login/',
            '/accounts/logout/',
            '/accounts/signup/',
            '/admin/login/',
            '/static/',
            '/media/',
            '/health/',
            '/',  # Public home page
            '/about/',
            '/programs/',
            '/admissions/',
            '/contact/',
        ]
        
        # Skip if path should be ignored
        if any(request.path.startswith(path) for path in skip_paths):
            return None
        
        # Skip for unauthenticated users (let login_required handle it)
        if not request.user.is_authenticated:
            return None
        
        # Get user role
        user_role = get_user_role(request.user)
        
        # Check student portal access
        if request.path.startswith('/student/'):
            if user_role != UserRoles.STUDENT:
                messages.error(
                    request, 
                    'You do not have permission to access the student portal. '
                    'Please contact an administrator if this is incorrect.'
                )
                return redirect('/')
        
        # Check parent portal access
        elif request.path.startswith('/parent/'):
            if user_role != UserRoles.PARENT:
                messages.error(
                    request, 
                    'You do not have permission to access the parent portal. '
                    'Please contact an administrator if this is incorrect.'
                )
                return redirect('/')
        
        # Check admin access
        elif request.path.startswith('/admin/'):
            if user_role not in [UserRoles.ADMIN, UserRoles.STAFF]:
                messages.error(
                    request, 
                    'You do not have permission to access the admin interface. '
                    'Please log in with an administrator account.'
                )
                return redirect('/')
        
        # Check dashboard access (legacy)
        elif request.path.startswith('/dashboard/'):
            if user_role not in [UserRoles.ADMIN, UserRoles.STAFF]:
                # Redirect non-admin users to their appropriate portal
                if user_role == UserRoles.STUDENT:
                    return redirect('/student/')
                elif user_role == UserRoles.PARENT:
                    return redirect('/parent/')
                else:
                    return redirect('/')
        
        return None
