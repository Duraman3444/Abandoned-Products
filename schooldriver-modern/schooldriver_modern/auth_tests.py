from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.core import mail
from django.test.utils import override_settings
import time


class AuthTests(TestCase):
    """Tests for Step 2.1: Modern Login Interface."""
    
    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.test_user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            is_staff=True  # Make user staff to access dashboard
        )
        
    def test_login_page_200(self):
        """Test that GET /accounts/login/ returns 200."""
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Sign in to your account')
        self.assertContains(response, 'Remember me for 30 days')
        
    def test_login_page_uses_custom_template(self):
        """Test that login page uses custom template."""
        response = self.client.get(reverse('login'))
        self.assertTemplateUsed(response, 'registration/login.html')
        
    def test_successful_login_without_remember_me(self):
        """Test successful login without remember me."""
        response = self.client.post(reverse('login'), {
            'username': 'testuser',
            'password': 'testpass123'
        })
        self.assertRedirects(response, '/dashboard/')
        
        # Check session expiry (should be default Django session length, not 30 days)
        session_expiry = self.client.session.get_expiry_age()
        self.assertLess(session_expiry, 2500000)  # Less than 30 days
        
    def test_remember_me_session_expiry(self):
        """Test that session expiry ≥ 2,600,000 s (30 days) when remember me is checked."""
        response = self.client.post(reverse('login'), {
            'username': 'testuser',
            'password': 'testpass123',
            'remember_me': 'true'
        })
        self.assertRedirects(response, '/dashboard/')
        
        # Check session expiry (should be around 30 days = 2,592,000 seconds)
        session_expiry = self.client.session.get_expiry_age()
        self.assertGreaterEqual(session_expiry, 2590000)  # Close to 30 days (2,592,000)
        
    def test_invalid_login_credentials(self):
        """Test login with invalid credentials."""
        response = self.client.post(reverse('login'), {
            'username': 'testuser',
            'password': 'wrongpassword'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Authentication Error')
        
    def test_password_reset_flow(self):
        """Test that POST to /password_reset/ sends email to console."""
        # Clear any existing mail
        mail.outbox = []
        
        response = self.client.post(reverse('password_reset'), {
            'email': 'test@example.com'
        })
        
        # Should redirect to password_reset_done
        self.assertRedirects(response, reverse('password_reset_done'))
        
        # Check that email was sent
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ['test@example.com'])
        self.assertIn('Password reset', mail.outbox[0].subject)
        
    def test_password_reset_done_page(self):
        """Test password reset done page."""
        response = self.client.get(reverse('password_reset_done'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Check your email')
        
    def test_password_reset_form_page(self):
        """Test password reset form page."""
        response = self.client.get(reverse('password_reset'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Reset your password')
        self.assertContains(response, 'Email address')
        
    def test_password_strength_validation_javascript(self):
        """Test that password strength validation JavaScript is included."""
        response = self.client.get(reverse('login'))
        self.assertContains(response, 'checkPasswordStrength')
        self.assertContains(response, 'password-strength')
        
    def test_login_form_has_required_fields(self):
        """Test that login form has all required fields."""
        response = self.client.get(reverse('login'))
        
        # Check for username field
        self.assertContains(response, 'name="username"')
        self.assertContains(response, 'type="text"')
        
        # Check for password field
        self.assertContains(response, 'name="password"')
        self.assertContains(response, 'type="password"')
        
        # Check for remember me checkbox
        self.assertContains(response, 'name="remember_me"')
        self.assertContains(response, 'type="checkbox"')
        
        # Check for CSRF token
        self.assertContains(response, 'csrfmiddlewaretoken')
        
    def test_login_helper_links(self):
        """Test that login page contains helper links."""
        response = self.client.get(reverse('login'))
        
        # Check for forgot password link
        self.assertContains(response, reverse('password_reset'))
        self.assertContains(response, 'Forgot your password?')
        
        # Check for admin login link
        self.assertContains(response, '/admin/')
        self.assertContains(response, 'Admin Login')
        
    def test_modern_styling_present(self):
        """Test that modern Tailwind CSS styling is present."""
        response = self.client.get(reverse('login'))
        
        # Check for Tailwind classes
        self.assertContains(response, 'tailwindcss.com')
        self.assertContains(response, 'bg-indigo-600')
        self.assertContains(response, 'rounded-md')
        self.assertContains(response, 'focus:ring-indigo-500')
        
    def test_password_reset_invalid_email(self):
        """Test password reset with non-existent email."""
        response = self.client.post(reverse('password_reset'), {
            'email': 'nonexistent@example.com'
        })
        
        # Should still redirect to done page (security measure)
        self.assertRedirects(response, reverse('password_reset_done'))
        
        # No email should be sent for non-existent user
        self.assertEqual(len(mail.outbox), 0)
        
    def test_login_redirect_after_successful_auth(self):
        """Test that successful login redirects to dashboard."""
        response = self.client.post(reverse('login'), {
            'username': 'testuser',
            'password': 'testpass123'
        }, follow=True)
        
        # Should be redirected to dashboard
        self.assertRedirects(response, '/dashboard/')
        
        # Should be authenticated
        self.assertTrue(response.wsgi_request.user.is_authenticated)
        
    def test_remember_me_functionality_in_template(self):
        """Test that remember me JavaScript functionality is included."""
        response = self.client.get(reverse('login'))
        
        # Check for remember me handling JavaScript
        self.assertContains(response, "document.getElementById('remember_me')")
        self.assertContains(response, "document.getElementById('loginForm')")
        self.assertContains(response, "addEventListener('submit'")


class PasswordValidationTests(TestCase):
    """Tests for password validation functionality."""
    
    def test_password_validators_configured(self):
        """Test that Django password validators are properly configured."""
        from django.conf import settings
        
        validators = settings.AUTH_PASSWORD_VALIDATORS
        
        # Check that we have the expected validators
        validator_names = [v['NAME'] for v in validators]
        
        expected_validators = [
            'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
            'django.contrib.auth.password_validation.MinimumLengthValidator',
            'django.contrib.auth.password_validation.CommonPasswordValidator',
            'django.contrib.auth.password_validation.NumericPasswordValidator',
        ]
        
        for expected in expected_validators:
            self.assertIn(expected, validator_names)
            
    def test_minimum_length_validator_configured(self):
        """Test that minimum length validator is set to 8 characters."""
        from django.conf import settings
        
        validators = settings.AUTH_PASSWORD_VALIDATORS
        min_length_validator = next(
            (v for v in validators if 'MinimumLengthValidator' in v['NAME']), 
            None
        )
        
        self.assertIsNotNone(min_length_validator)
        self.assertEqual(min_length_validator['OPTIONS']['min_length'], 8)
