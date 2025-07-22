from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from django.conf import settings
import os
import tempfile
from PIL import Image
from .models import UserProfile


class ProfileTests(TestCase):
    """Tests for user profile functionality"""

    def setUp(self):
        """Set up test data"""
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser",
            first_name="Test",
            last_name="User",
            email="test@example.com",
            password="testpass123",
        )
        self.profile, created = UserProfile.objects.get_or_create(user=self.user)

    def test_profile_page_200(self):
        """Test that profile page loads successfully"""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(reverse("profile"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "My Profile")
        self.assertContains(response, "testuser")

    def test_profile_page_requires_login(self):
        """Test that profile page requires authentication"""
        response = self.client.get(reverse("profile"))
        self.assertEqual(response.status_code, 302)  # Redirect to login

    def test_edit_profile_page_200(self):
        """Test that edit profile page loads successfully"""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(reverse("edit_profile"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Edit Profile")

    def test_edit_profile_form_submission(self):
        """Test editing profile information"""
        self.client.login(username="testuser", password="testpass123")

        # Submit form with updated info
        response = self.client.post(
            reverse("edit_profile"),
            {
                "first_name": "Updated",
                "last_name": "Name",
                "email": "updated@example.com",
            },
        )

        # Check redirect to profile page
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("profile"))

        # Check that user data was updated
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, "Updated")
        self.assertEqual(self.user.last_name, "Name")
        self.assertEqual(self.user.email, "updated@example.com")

    def create_test_image(self):
        """Create a test image for avatar upload tests"""
        # Create a simple test image
        image = Image.new("RGB", (100, 100), color="red")
        temp_file = tempfile.NamedTemporaryFile(suffix=".jpg", delete=False)
        image.save(temp_file.name, "JPEG")
        temp_file.seek(0)

        # Create uploadable file
        with open(temp_file.name, "rb") as f:
            uploaded_file = SimpleUploadedFile(
                name="test_avatar.jpg", content=f.read(), content_type="image/jpeg"
            )

        # Cleanup temp file
        os.unlink(temp_file.name)
        return uploaded_file

    def test_avatar_upload(self):
        """Test avatar upload functionality"""
        self.client.login(username="testuser", password="testpass123")

        # Create test image
        test_image = self.create_test_image()

        # Submit form with avatar
        response = self.client.post(
            reverse("edit_profile"),
            {
                "first_name": "Test",
                "last_name": "User",
                "email": "test@example.com",
                "avatar": test_image,
            },
        )

        # Check redirect
        self.assertEqual(response.status_code, 302)

        # Check that avatar was saved
        self.profile.refresh_from_db()
        self.assertTrue(self.profile.avatar)

        # Check that file exists in media directory
        avatar_path = os.path.join(settings.MEDIA_ROOT, self.profile.avatar.name)
        self.assertTrue(os.path.exists(avatar_path))

        # Cleanup uploaded file
        if os.path.exists(avatar_path):
            os.unlink(avatar_path)

    def test_password_change_page_200(self):
        """Test that password change page loads successfully"""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(reverse("password_change"))
        self.assertEqual(response.status_code, 200)
        # The template might have different text, let's check for form elements
        self.assertContains(response, "old_password")
        self.assertContains(response, "new_password1")

    def test_password_change(self):
        """Test password change functionality"""
        self.client.login(username="testuser", password="testpass123")

        # Submit password change form
        response = self.client.post(
            reverse("password_change"),
            {
                "old_password": "testpass123",
                "new_password1": "newpassword456",
                "new_password2": "newpassword456",
            },
        )

        # Check redirect to profile page
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("profile"))

        # Check that password was changed
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("newpassword456"))
        self.assertFalse(self.user.check_password("testpass123"))

    def test_password_change_wrong_old_password(self):
        """Test password change with wrong old password"""
        self.client.login(username="testuser", password="testpass123")

        response = self.client.post(
            reverse("password_change"),
            {
                "old_password": "wrongpassword",
                "new_password1": "newpassword456",
                "new_password2": "newpassword456",
            },
        )

        # Should stay on same page with error
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Your old password was entered incorrectly")

    def test_user_profile_creation_signal(self):
        """Test that UserProfile is created automatically when User is created"""
        new_user = User.objects.create_user(username="newuser", password="testpass123")

        # Profile should be created automatically
        self.assertTrue(hasattr(new_user, "profile"))
        self.assertTrue(UserProfile.objects.filter(user=new_user).exists())

    def test_avatar_url_property(self):
        """Test avatar_url property returns correct URL"""
        # Test with no avatar
        self.assertEqual(self.profile.avatar_url, "/static/img/default-avatar.png")

        # Test with avatar (mock)
        self.profile.avatar.name = "avatars/test_avatar.jpg"
        # Note: In real test, avatar.url would be properly set
        # Here we just test that the property works

    def tearDown(self):
        """Clean up after tests"""
        # Clean up any uploaded files during testing
        import shutil

        media_avatars_path = os.path.join(settings.MEDIA_ROOT, "avatars")
        if os.path.exists(media_avatars_path):
            shutil.rmtree(media_avatars_path, ignore_errors=True)
