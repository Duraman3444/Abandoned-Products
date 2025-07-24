from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import translation
from schooldriver_modern.models import UserProfile
from students.models import Student, GradeLevel
from datetime import date


class FullLanguageImplementationTest(TestCase):
    """Test the complete multi-language implementation end-to-end"""
    
    def setUp(self):
        self.client = Client()
        
        # Create a parent user
        self.user = User.objects.create_user(
            username='testparent',
            email='parent@test.com',
            password='testpass123',
            first_name='Test',
            last_name='Parent'
        )
        
        # Assign Parent role
        from schooldriver_modern.roles import assign_role_to_user
        assign_role_to_user(self.user, 'Parent')
        
        # Get the profile created by the signal
        self.profile = UserProfile.objects.get(user=self.user)
        
        # Create a student linked to this parent
        grade = GradeLevel.objects.create(name='10th', order=10)
        self.student = Student.objects.create(
            first_name='Test',
            last_name='Student', 
            date_of_birth=date(2008, 5, 15),
            enrollment_date=date(2023, 8, 15),
            grade_level=grade
        )
        
        # Link parent to student
        self.student.family_access_users.add(self.user)
        
    def test_profile_form_language_functionality(self):
        """Test that the profile form properly handles language changes"""
        from parent_portal.profile_forms import ParentProfileForm
        
        # Test form initialization with current language
        form = ParentProfileForm(instance=self.profile, user=self.user)
        self.assertIn('preferred_language', form.fields)
        self.assertEqual(form.initial['preferred_language'], 'en')
        
        # Test form with language change
        form_data = {
            'first_name': 'Test',
            'last_name': 'Parent',
            'email': 'parent@test.com',
            'phone_number': '555-123-4567',
            'address': '123 Test Street',
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
        
        # Verify language was saved
        self.assertEqual(saved_profile.preferred_language, 'es')
        
        # Verify user fields were updated
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, 'Test')
        self.assertEqual(self.user.email, 'parent@test.com')
    
    def test_language_middleware_functionality(self):
        """Test that the middleware properly sets user language"""
        from schooldriver_modern.language_middleware import UserLanguageMiddleware
        from django.test import RequestFactory
        
        # Create a mock request
        factory = RequestFactory()
        request = factory.get('/')
        request.user = self.user
        request.session = {}
        
        # Set user's preferred language to Spanish
        self.profile.preferred_language = 'es'
        self.profile.save()
        
        # Create middleware instance
        def dummy_response(request):
            return "dummy response"
        
        middleware = UserLanguageMiddleware(dummy_response)
        
        # Call middleware
        response = middleware(request)
        
        # Check that session was updated
        self.assertEqual(request.session.get('django_language'), 'es')
    
    def test_language_switching_view(self):
        """Test the language switching view functionality"""
        # Login the user first
        self.client.login(username='testparent', password='testpass123')
        
        # Test language switching
        response = self.client.post(
            reverse('parent_portal:set_language'),
            {'language': 'fr'},
            HTTP_REFERER='/parent/profile/'
        )
        
        # Should redirect back
        self.assertEqual(response.status_code, 302)
        
        # Check that profile was updated
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.preferred_language, 'fr')
        
        # Test invalid language
        response = self.client.post(
            reverse('parent_portal:set_language'),
            {'language': 'invalid'},
            HTTP_REFERER='/parent/profile/'
        )
        
        # Should still redirect but not change language
        self.assertEqual(response.status_code, 302)
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.preferred_language, 'fr')  # Should remain unchanged
    
    def test_profile_view_integration(self):
        """Test that the profile view properly integrates with the form"""
        # Login the user
        self.client.login(username='testparent', password='testpass123')
        
        # GET request should show form
        response = self.client.get(reverse('parent_portal:profile'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('form', response.context)
        
        # POST request should update profile
        response = self.client.post(reverse('parent_portal:profile'), {
            'first_name': 'Updated',
            'last_name': 'Parent',
            'email': 'updated@test.com',
            'phone_number': '555-987-6543',
            'address': '456 Updated Street',
            'preferred_language': 'es',
            'email_notifications': True,
            'sms_notifications': True
        })
        
        # Should redirect after successful update
        self.assertEqual(response.status_code, 302)
        
        # Check that data was saved
        self.user.refresh_from_db()
        self.profile.refresh_from_db()
        
        self.assertEqual(self.user.first_name, 'Updated')
        self.assertEqual(self.user.email, 'updated@test.com')
        self.assertEqual(self.profile.preferred_language, 'es')
        self.assertEqual(self.profile.phone_number, '555-987-6543')
        self.assertTrue(self.profile.sms_notifications)
    
    def test_language_choices_match_settings(self):
        """Test that language choices in form match Django settings"""
        from django.conf import settings
        from parent_portal.profile_forms import ParentProfileForm
        
        form = ParentProfileForm(instance=self.profile, user=self.user)
        form_choices = form.fields['preferred_language'].choices
        settings_languages = settings.LANGUAGES
        
        self.assertEqual(len(form_choices), len(settings_languages))
        
        for form_choice, settings_lang in zip(form_choices, settings_languages):
            self.assertEqual(form_choice[0], settings_lang[0])
            self.assertEqual(form_choice[1], settings_lang[1])
    
    def test_default_language_behavior(self):
        """Test behavior when user has default language"""
        # User should start with English (default)
        self.assertEqual(self.profile.preferred_language, 'en')
        
        # Middleware should not crash on default language
        from schooldriver_modern.language_middleware import UserLanguageMiddleware  
        from django.test import RequestFactory
        
        factory = RequestFactory()
        request = factory.get('/')
        request.user = self.user
        request.session = {}
        
        def dummy_response(request):
            return "dummy"
        
        middleware = UserLanguageMiddleware(dummy_response)
        response = middleware(request)
        
        # Should work without error
        self.assertEqual(response, "dummy")
        self.assertEqual(request.session.get('django_language'), 'en')
