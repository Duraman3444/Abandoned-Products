from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.conf import settings
from schooldriver_modern.models import UserProfile


class LanguageSupportTestCase(TestCase):
    """Test multi-language support in parent portal"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testparent',
            email='parent@test.com',
            password='testpass123'
        )
        # Get the profile created by the signal
        self.profile = UserProfile.objects.get(user=self.user)
        self.profile.preferred_language = 'en'
        self.profile.save()
    
    def test_user_profile_language_field(self):
        """Test that UserProfile has preferred_language field"""
        self.assertEqual(self.profile.preferred_language, 'en')
        
        # Test updating language
        self.profile.preferred_language = 'es'
        self.profile.save()
        
        # Reload from database
        updated_profile = UserProfile.objects.get(user=self.user)
        self.assertEqual(updated_profile.preferred_language, 'es')
    
    def test_language_choices_in_settings(self):
        """Test that LANGUAGES setting is configured"""
        self.assertIn('LANGUAGES', dir(settings))
        languages = settings.LANGUAGES
        
        # Check that we have the expected languages
        language_codes = [lang[0] for lang in languages]
        self.assertIn('en', language_codes)
        self.assertIn('es', language_codes)
        self.assertIn('fr', language_codes)
    
    def test_profile_form_includes_language_field(self):
        """Test that the profile form includes language preference"""
        from parent_portal.profile_forms import ParentProfileForm
        
        form = ParentProfileForm(user=self.user, instance=self.profile)
        self.assertIn('preferred_language', form.fields)
        
        # Test form choices match settings
        form_choices = [choice[0] for choice in form.fields['preferred_language'].choices]
        settings_choices = [lang[0] for lang in settings.LANGUAGES]
        self.assertEqual(form_choices, settings_choices)
    
    def test_profile_form_save_updates_language(self):
        """Test that saving the profile form updates the language preference"""
        from parent_portal.profile_forms import ParentProfileForm
        
        form_data = {
            'first_name': 'Test',
            'last_name': 'Parent',
            'email': 'parent@test.com',
            'phone_number': '555-123-4567',
            'address': '123 Test St',
            'preferred_language': 'es',
            'email_notifications': True,
            'sms_notifications': False
        }
        
        form = ParentProfileForm(
            data=form_data,
            instance=self.profile,
            user=self.user
        )
        
        self.assertTrue(form.is_valid(), f"Form errors: {form.errors}")
        saved_profile = form.save()
        
        self.assertEqual(saved_profile.preferred_language, 'es')
        # Also check that user fields were updated
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, 'Test')
        self.assertEqual(self.user.last_name, 'Parent')
    
    def test_user_language_middleware_exists(self):
        """Test that the language middleware is properly configured"""
        from schooldriver_modern.language_middleware import UserLanguageMiddleware
        
        # Should be able to import without error
        middleware = UserLanguageMiddleware(lambda x: x)
        self.assertIsNotNone(middleware)
    
    def test_language_switching_view_exists(self):
        """Test that language switching view exists"""
        from parent_portal.language_views import set_language_view
        
        # Should be able to import without error
        self.assertIsNotNone(set_language_view)
