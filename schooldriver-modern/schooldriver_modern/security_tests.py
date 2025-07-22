from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.core.cache import cache
from django.contrib.messages import get_messages

from .models import SecurityEvent
from .middleware import get_login_limiter


class SecurityTests(TestCase):
    """Tests for security enhancements"""

    def setUp(self):
        """Set up test data"""
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser", password="testpass123", email="test@example.com"
        )
        # Clear cache before each test
        cache.clear()

    def tearDown(self):
        """Clean up after tests"""
        cache.clear()

    def test_lockout_after_failures(self):
        """Test that 5 bad logins triggers lockout"""
        login_url = reverse("login")

        # Make 4 failed login attempts
        for i in range(4):
            response = self.client.post(
                login_url, {"username": "testuser", "password": "wrongpassword"}
            )
            self.assertEqual(response.status_code, 200)

        # Verify we can still attempt login (not locked yet)
        response = self.client.post(
            login_url, {"username": "testuser", "password": "wrongpassword"}
        )
        self.assertEqual(response.status_code, 200)

        # The 5th failed attempt should trigger lockout
        response = self.client.post(
            login_url, {"username": "testuser", "password": "wrongpassword"}
        )
        self.assertEqual(response.status_code, 200)

        # Now any login attempt should be blocked
        response = self.client.post(
            login_url,
            {
                "username": "testuser",
                "password": "testpass123",  # Correct password but account locked
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "temporarily locked")

        # Check that security events were logged (at least 5 failed attempts)
        failed_events = SecurityEvent.objects.filter(
            username="testuser", event_type="LOGIN_FAILED"
        )
        self.assertGreaterEqual(failed_events.count(), 5)

        locked_events = SecurityEvent.objects.filter(
            username="testuser", event_type="ACCOUNT_LOCKED"
        )
        self.assertGreaterEqual(locked_events.count(), 1)

    def test_successful_login_clears_attempts(self):
        """Test that successful login clears failed attempts"""
        login_url = reverse("login")

        # Make 3 failed login attempts
        for i in range(3):
            self.client.post(
                login_url, {"username": "testuser", "password": "wrongpassword"}
            )

        # Successful login should clear attempts
        response = self.client.post(
            login_url, {"username": "testuser", "password": "testpass123"}
        )
        self.assertEqual(response.status_code, 302)  # Redirect after successful login

        # Check that login success was logged
        success_events = SecurityEvent.objects.filter(
            user=self.user, event_type="LOGIN_SUCCESS"
        )
        self.assertEqual(success_events.count(), 1)

        # Logout and try again - should not be locked
        self.client.logout()
        response = self.client.post(
            login_url, {"username": "testuser", "password": "testpass123"}
        )
        self.assertEqual(response.status_code, 302)  # Should work fine

    def test_csrf_protected(self):
        """Test that POST endpoints require CSRF tokens"""
        # Login first
        self.client.login(username="testuser", password="testpass123")

        # Disable CSRF for this test by using enforce_csrf_checks
        self.client.logout()

        # Create a client with CSRF enforcement
        from django.test import Client

        csrf_client = Client(enforce_csrf_checks=True)
        csrf_client.login(username="testuser", password="testpass123")

        # Try to access profile edit without CSRF token
        response = csrf_client.post(
            reverse("edit_profile"),
            {"first_name": "Updated", "last_name": "Name"},
            follow=False,
        )

        # Should get 403 Forbidden due to missing CSRF token
        self.assertEqual(response.status_code, 403)

    def test_csrf_protected_with_token(self):
        """Test that POST endpoints work with CSRF tokens"""
        # Login first
        self.client.login(username="testuser", password="testpass123")

        # Get the edit profile page to get CSRF token
        response = self.client.get(reverse("edit_profile"))
        self.assertEqual(response.status_code, 200)

        # Extract CSRF token from the form
        csrf_token = response.context["csrf_token"]

        # Try to update profile with CSRF token
        response = self.client.post(
            reverse("edit_profile"),
            {
                "first_name": "Updated",
                "last_name": "Name",
                "csrfmiddlewaretoken": csrf_token,
            },
        )

        # Should redirect to profile page on success
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("profile"))

    def test_event_logged_password_change(self):
        """Test that password change creates a SecurityEvent"""
        # Login first
        self.client.login(username="testuser", password="testpass123")

        # Get the password change page
        response = self.client.get(reverse("password_change"))
        csrf_token = response.context["csrf_token"]

        # Change password
        response = self.client.post(
            reverse("password_change"),
            {
                "old_password": "testpass123",
                "new_password1": "newpassword456",
                "new_password2": "newpassword456",
                "csrfmiddlewaretoken": csrf_token,
            },
        )

        self.assertEqual(response.status_code, 302)

        # Check that password change was logged
        password_events = SecurityEvent.objects.filter(
            user=self.user, event_type="PASSWORD_CHANGE"
        )
        self.assertEqual(password_events.count(), 1)

        # Verify event details
        event = password_events.first()
        self.assertEqual(event.user, self.user)
        self.assertEqual(event.username, "testuser")
        self.assertIsNotNone(event.ip_address)

    def test_login_attempt_limiter_methods(self):
        """Test the login attempt limiter helper methods"""
        limiter = get_login_limiter()
        username = "testuser"

        # Initially should have 0 attempts
        self.assertEqual(limiter.get_failed_attempts(username), 0)
        self.assertFalse(limiter.is_locked_out(username))

        # Record some failed attempts
        for i in range(3):
            count = limiter.record_failed_attempt(username)
            self.assertEqual(count, i + 1)

        # Should have 3 attempts but not locked yet
        self.assertEqual(limiter.get_failed_attempts(username), 3)
        self.assertFalse(limiter.is_locked_out(username))

        # Record 2 more attempts to trigger lockout
        limiter.record_failed_attempt(username)
        count = limiter.record_failed_attempt(username)
        self.assertEqual(count, 5)

        # Should now be locked out
        self.assertTrue(limiter.is_locked_out(username))

        # Clear attempts
        limiter.clear_failed_attempts(username)
        self.assertEqual(limiter.get_failed_attempts(username), 0)

    def test_security_event_log_helper(self):
        """Test the SecurityEvent.log_event helper method"""
        # Create a fake request object
        request = type(
            "MockRequest",
            (),
            {
                "META": {
                    "REMOTE_ADDR": "127.0.0.1",
                    "HTTP_USER_AGENT": "Test Browser",
                    "HTTP_X_FORWARDED_FOR": "192.168.1.1, 127.0.0.1",
                }
            },
        )()

        # Log an event
        event = SecurityEvent.log_event(
            "LOGIN_SUCCESS", user=self.user, request=request, extra_field="test_value"
        )

        # Verify event was created correctly
        self.assertEqual(event.event_type, "LOGIN_SUCCESS")
        self.assertEqual(event.user, self.user)
        self.assertEqual(event.username, "testuser")
        self.assertEqual(event.ip_address, "192.168.1.1")  # Should use X-Forwarded-For
        self.assertEqual(event.user_agent, "Test Browser")
        self.assertEqual(event.details["extra_field"], "test_value")

    def test_session_security_settings(self):
        """Test that session security settings are properly configured"""
        from django.conf import settings

        # Check session security settings
        self.assertEqual(settings.SESSION_COOKIE_AGE, 1800)  # 30 minutes
        self.assertTrue(settings.SESSION_EXPIRE_AT_BROWSER_CLOSE)
        self.assertTrue(settings.SESSION_COOKIE_HTTPONLY)
        self.assertEqual(settings.SESSION_COOKIE_SAMESITE, "Lax")
        self.assertTrue(settings.SESSION_SAVE_EVERY_REQUEST)

    def test_warning_message_for_failed_attempts(self):
        """Test that users see warning after failed attempts"""
        login_url = reverse("login")

        # Make 2 failed attempts
        for i in range(2):
            self.client.post(
                login_url, {"username": "testuser", "password": "wrongpassword"}
            )

        # Successful login should show warning
        response = self.client.post(
            login_url, {"username": "testuser", "password": "testpass123"}, follow=True
        )

        # Check for warning message
        messages = list(get_messages(response.wsgi_request))
        warning_found = any("Warning" in str(message) for message in messages)
        self.assertTrue(warning_found)

    def test_security_event_admin_permissions(self):
        """Test that SecurityEvent admin has proper restrictions"""
        from .admin import SecurityEventAdmin
        from django.contrib.admin.sites import site

        admin_instance = SecurityEventAdmin(SecurityEvent, site)
        request = type("MockRequest", (), {})()

        # Should not allow add, change, or delete
        self.assertFalse(admin_instance.has_add_permission(request))
        self.assertFalse(admin_instance.has_change_permission(request))
        self.assertFalse(admin_instance.has_delete_permission(request))

    def test_middleware_in_settings(self):
        """Test that security middleware is properly configured"""
        from django.conf import settings

        self.assertIn(
            "schooldriver_modern.middleware.LoginAttemptLimitingMiddleware",
            settings.MIDDLEWARE,
        )
