"""
Authentication decorators for role-based access control.
"""

from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from functools import wraps
from schooldriver_modern.roles import get_user_role
import logging

logger = logging.getLogger(__name__)


def role_required(allowed_roles, login_url=None, redirect_field_name=REDIRECT_FIELD_NAME, raise_exception=False):
    """
    Decorator for views that checks whether a user has a particular role enabled.
    
    Args:
        allowed_roles: List of roles that are allowed to access the view
        login_url: URL to redirect to if user is not logged in
        redirect_field_name: Name of GET parameter for the login redirect
        raise_exception: If True, raise PermissionDenied instead of redirecting
    
    Usage:
        @role_required(['student'])
        @role_required(['admin', 'staff'])
        @role_required(['parent'], raise_exception=True)
    """
    def check_role(user):
        if not user.is_authenticated:
            return False
        
        user_role = get_user_role(user)
        if user_role in allowed_roles:
            logger.debug(f"User {user.username} has required role: {user_role}")
            return True
        
        logger.warning(f"User {user.username} with role {user_role} denied access to view requiring: {allowed_roles}")
        return False
    
    actual_decorator = user_passes_test(
        check_role,
        login_url=login_url,
        redirect_field_name=redirect_field_name
    )
    
    if raise_exception:
        def decorator(view_func):
            @wraps(view_func)
            def _wrapped_view(request, *args, **kwargs):
                if not check_role(request.user):
                    raise PermissionDenied("You don't have permission to access this page.")
                return view_func(request, *args, **kwargs)
            return _wrapped_view
        return decorator
    
    return actual_decorator


def student_required(function=None, redirect_field_name=REDIRECT_FIELD_NAME, login_url=None):
    """
    Decorator that requires user to be a student.
    """
    actual_decorator = role_required(['Student'], login_url=login_url, redirect_field_name=redirect_field_name)
    if function:
        return actual_decorator(function)
    return actual_decorator


def parent_required(function=None, redirect_field_name=REDIRECT_FIELD_NAME, login_url=None):
    """
    Decorator that requires user to be a parent.
    """
    actual_decorator = role_required(['Parent'], login_url=login_url, redirect_field_name=redirect_field_name)
    if function:
        return actual_decorator(function)
    return actual_decorator


def staff_required(function=None, redirect_field_name=REDIRECT_FIELD_NAME, login_url=None):
    """
    Decorator that requires user to be staff or admin.
    """
    actual_decorator = role_required(['Staff', 'Admin'], login_url=login_url, redirect_field_name=redirect_field_name)
    if function:
        return actual_decorator(function)
    return actual_decorator


def admin_required(function=None, redirect_field_name=REDIRECT_FIELD_NAME, login_url=None):
    """
    Decorator that requires user to be an admin.
    """
    actual_decorator = role_required(['Admin'], login_url=login_url, redirect_field_name=redirect_field_name)
    if function:
        return actual_decorator(function)
    return actual_decorator
