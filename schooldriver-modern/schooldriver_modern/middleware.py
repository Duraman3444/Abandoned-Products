from django.http import HttpResponseForbidden
from django.contrib.auth import authenticate
from django.core.cache import cache
from django.contrib.auth.signals import user_login_failed, user_logged_in
from django.dispatch import receiver
from django.utils import timezone
from datetime import timedelta
import json

from .models import SecurityEvent


class LoginAttemptLimitingMiddleware:
    """Middleware to limit login attempts and lock accounts after too many failures"""
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.max_attempts = 5
        self.lockout_duration = timedelta(minutes=30)
    
    def __call__(self, request):
        response = self.get_response(request)
        return response
    
    def get_cache_key(self, identifier):
        """Generate cache key for tracking failed attempts"""
        return f"login_attempts:{identifier}"
    
    def get_lockout_key(self, identifier):
        """Generate cache key for lockout status"""
        return f"account_locked:{identifier}"
    
    def is_locked_out(self, identifier):
        """Check if account/IP is currently locked out"""
        lockout_key = self.get_lockout_key(identifier)
        return cache.get(lockout_key, False)
    
    def get_failed_attempts(self, identifier):
        """Get number of failed attempts for identifier"""
        cache_key = self.get_cache_key(identifier)
        attempts_data = cache.get(cache_key, {'count': 0, 'attempts': []})
        
        # Clean old attempts (older than lockout duration)
        cutoff_time = timezone.now() - self.lockout_duration
        attempts_data['attempts'] = [
            attempt for attempt in attempts_data['attempts']
            if attempt > cutoff_time.timestamp()
        ]
        attempts_data['count'] = len(attempts_data['attempts'])
        
        cache.set(cache_key, attempts_data, timeout=int(self.lockout_duration.total_seconds()))
        return attempts_data['count']
    
    def record_failed_attempt(self, identifier):
        """Record a failed login attempt"""
        cache_key = self.get_cache_key(identifier)
        attempts_data = cache.get(cache_key, {'count': 0, 'attempts': []})
        
        # Add current attempt
        now = timezone.now().timestamp()
        attempts_data['attempts'].append(now)
        
        # Clean old attempts
        cutoff_time = timezone.now() - self.lockout_duration
        attempts_data['attempts'] = [
            attempt for attempt in attempts_data['attempts']
            if attempt > cutoff_time.timestamp()
        ]
        attempts_data['count'] = len(attempts_data['attempts'])
        
        # Check if we should lock the account
        if attempts_data['count'] >= self.max_attempts:
            self.lock_account(identifier)
        
        cache.set(cache_key, attempts_data, timeout=int(self.lockout_duration.total_seconds()))
        return attempts_data['count']
    
    def lock_account(self, identifier):
        """Lock an account/IP"""
        lockout_key = self.get_lockout_key(identifier)
        cache.set(lockout_key, True, timeout=int(self.lockout_duration.total_seconds()))
    
    def clear_failed_attempts(self, identifier):
        """Clear failed attempts after successful login"""
        cache_key = self.get_cache_key(identifier)
        cache.delete(cache_key)


# Global instance for use in signal handlers
_login_limiter = None

def get_login_limiter():
    """Get the global login limiter instance"""
    global _login_limiter
    if _login_limiter is None:
        _login_limiter = LoginAttemptLimitingMiddleware(lambda x: x)
    return _login_limiter


@receiver(user_login_failed)
def handle_failed_login(sender, credentials, request, **kwargs):
    """Handle failed login attempts"""
    username = credentials.get('username', '')
    if not username:
        return
    
    limiter = get_login_limiter()
    failed_count = limiter.record_failed_attempt(username)
    
    # Log the failed attempt
    SecurityEvent.log_event(
        'LOGIN_FAILED',
        username=username,
        request=request,
        failed_attempts=failed_count
    )
    
    # If account is now locked, log that too
    if failed_count >= limiter.max_attempts:
        SecurityEvent.log_event(
            'ACCOUNT_LOCKED',
            username=username,
            request=request,
            reason='Too many failed login attempts'
        )


@receiver(user_logged_in)
def handle_successful_login(sender, user, request, **kwargs):
    """Handle successful login"""
    limiter = get_login_limiter()
    limiter.clear_failed_attempts(user.username)
    
    # Log successful login
    SecurityEvent.log_event(
        'LOGIN_SUCCESS',
        user=user,
        request=request
    )


def check_login_allowed(username):
    """Check if login is allowed for username"""
    limiter = get_login_limiter()
    
    # Check if account is locked
    if limiter.is_locked_out(username):
        return False, f"Account temporarily locked due to too many failed login attempts. Try again later."
    
    # Check failed attempts
    failed_count = limiter.get_failed_attempts(username)
    remaining = limiter.max_attempts - failed_count
    
    if remaining <= 0:
        return False, f"Account temporarily locked due to too many failed login attempts. Try again later."
    
    if failed_count > 0:
        return True, f"Warning: {failed_count} failed login attempts. {remaining} attempts remaining."
    
    return True, None
