"""
Custom Security Middleware for additional security headers and protection
"""

import logging
from django.conf import settings
from django.http import HttpResponseForbidden
from django.utils.deprecation import MiddlewareMixin
from django.core.cache import cache

logger = logging.getLogger(__name__)


class SecurityHeadersMiddleware(MiddlewareMixin):
    """
    Adds additional security headers to all responses
    """

    def process_response(self, request, response):
        """Add security headers to response"""

        # Content Security Policy (CSP)
        if not settings.DEBUG:
            csp_policy = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval' cdn.jsdelivr.net cdnjs.cloudflare.com; "
                "style-src 'self' 'unsafe-inline' cdn.jsdelivr.net; "
                "img-src 'self' data: https:; "
                "font-src 'self' cdn.jsdelivr.net; "
                "connect-src 'self'; "
                "frame-ancestors 'none';"
            )
            response["Content-Security-Policy"] = csp_policy

        # Additional security headers
        response["X-Content-Type-Options"] = "nosniff"
        response["X-Frame-Options"] = "DENY"
        response["X-XSS-Protection"] = "1; mode=block"
        response["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"

        # Remove server information
        if "Server" in response:
            del response["Server"]

        return response


class RateLimitingMiddleware(MiddlewareMixin):
    """
    Basic rate limiting middleware to prevent abuse
    """

    def __init__(self, get_response):
        self.get_response = get_response
        super().__init__(get_response)

    def process_request(self, request):
        """Check rate limits for requests"""

        # Skip rate limiting in debug mode
        if settings.DEBUG:
            return None

        # Get client IP
        client_ip = self.get_client_ip(request)

        # Different limits for different endpoints
        if request.path.startswith("/accounts/login/"):
            # Stricter limits for login attempts
            if self.is_rate_limited(
                client_ip, "login", limit=5, window=300
            ):  # 5 attempts per 5 minutes
                logger.warning(
                    f"Rate limit exceeded for login attempts from {client_ip}"
                )
                return HttpResponseForbidden(
                    "Too many login attempts. Please try again later."
                )

        elif request.path.startswith("/api/"):
            # API rate limiting
            if self.is_rate_limited(
                client_ip, "api", limit=100, window=60
            ):  # 100 requests per minute
                logger.warning(f"API rate limit exceeded from {client_ip}")
                return HttpResponseForbidden(
                    "API rate limit exceeded. Please slow down."
                )

        else:
            # General rate limiting
            if self.is_rate_limited(
                client_ip, "general", limit=300, window=60
            ):  # 300 requests per minute
                logger.warning(f"General rate limit exceeded from {client_ip}")
                return HttpResponseForbidden("Rate limit exceeded. Please slow down.")

        return None

    def get_client_ip(self, request):
        """Get the real client IP address"""
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            ip = x_forwarded_for.split(",")[0].strip()
        else:
            ip = request.META.get("REMOTE_ADDR", "0.0.0.0")
        return ip

    def is_rate_limited(self, identifier, category, limit, window):
        """Check if request should be rate limited"""
        cache_key = f"rate_limit:{category}:{identifier}"

        try:
            # Get current count from cache
            current_count = cache.get(cache_key, 0)

            if current_count >= limit:
                return True

            # Increment counter
            cache.set(cache_key, current_count + 1, window)
            return False

        except Exception as e:
            # If cache fails, allow request but log error
            logger.error(f"Rate limiting cache error: {e}")
            return False


class SecurityAuditMiddleware(MiddlewareMixin):
    """
    Logs security-relevant events for auditing
    """

    def process_request(self, request):
        """Log security-relevant requests"""

        # Log admin access attempts
        if request.path.startswith("/admin/"):
            logger.info(
                f"Admin access attempt from {request.META.get('REMOTE_ADDR')} to {request.path}"
            )

        # Log authentication attempts
        if request.path.startswith("/accounts/login/") and request.method == "POST":
            username = request.POST.get("username", "unknown")
            logger.info(
                f"Login attempt for username '{username}' from {request.META.get('REMOTE_ADDR')}"
            )

        # Log suspicious requests
        user_agent = request.META.get("HTTP_USER_AGENT", "").lower()
        suspicious_patterns = ["sqlmap", "nikto", "nmap", "dirb", "burp", "owasp"]

        if any(pattern in user_agent for pattern in suspicious_patterns):
            logger.warning(
                f"Suspicious user agent detected: {user_agent} from {request.META.get('REMOTE_ADDR')}"
            )

        # Log requests with suspicious parameters
        suspicious_params = ["../", "<script", "union select", "drop table", "exec("]
        query_string = request.META.get("QUERY_STRING", "").lower()

        if any(param in query_string for param in suspicious_params):
            logger.warning(
                f"Suspicious query parameters: {query_string} from {request.META.get('REMOTE_ADDR')}"
            )

        return None

    def process_response(self, request, response):
        """Log security-relevant responses"""

        # Log failed authentication attempts
        if (
            request.path.startswith("/accounts/login/")
            and request.method == "POST"
            and response.status_code in [400, 401, 403]
        ):
            username = request.POST.get("username", "unknown")
            logger.warning(
                f"Failed login attempt for username '{username}' from {request.META.get('REMOTE_ADDR')}"
            )

        return response
