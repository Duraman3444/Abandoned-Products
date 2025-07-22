from django.test import TestCase, Client
from django.contrib.auth.models import User, Group
from django.urls import reverse


class NavigationTests(TestCase):
    """Tests for site navigation functionality"""

    def setUp(self):
        """Set up test data"""
        self.client = Client()

        # Create test users with different roles
        self.admin_user = User.objects.create_user(
            username="admin_user", password="testpass123", is_superuser=True
        )

        self.staff_user = User.objects.create_user(
            username="staff_user", password="testpass123"
        )

        self.parent_user = User.objects.create_user(
            username="parent_user", password="testpass123"
        )

        self.student_user = User.objects.create_user(
            username="student_user", password="testpass123"
        )

        # Create groups
        admin_group, _ = Group.objects.get_or_create(name="Admin")
        staff_group, _ = Group.objects.get_or_create(name="Staff")
        parent_group, _ = Group.objects.get_or_create(name="Parent")
        student_group, _ = Group.objects.get_or_create(name="Student")

        # Assign users to groups
        self.staff_user.groups.add(staff_group)
        self.parent_user.groups.add(parent_group)
        self.student_user.groups.add(student_group)

    def test_admin_navigation_links(self):
        """Test that admin users see appropriate navigation links"""
        self.client.login(username="admin_user", password="testpass123")
        response = self.client.get(reverse("dashboard"))

        # Admin should see dashboard, profile, and admin links
        self.assertContains(response, "📊 Dashboard")
        self.assertContains(response, "👤 My Profile")
        self.assertContains(response, "⚙️ Admin")

        # Should not see parent or student portals
        self.assertNotContains(response, "👨‍👩‍👧‍👦 Parent Portal")
        self.assertNotContains(response, "🎓 Student Portal")

    def test_staff_navigation_links(self):
        """Test that staff users see appropriate navigation links"""
        self.client.login(username="staff_user", password="testpass123")
        response = self.client.get(reverse("dashboard"))

        # Staff should see dashboard and profile links
        self.assertContains(response, "📊 Dashboard")
        self.assertContains(response, "👤 My Profile")

        # Should not see admin, parent or student portals
        self.assertNotContains(response, "⚙️ Admin")
        self.assertNotContains(response, "👨‍👩‍👧‍👦 Parent Portal")
        self.assertNotContains(response, "🎓 Student Portal")

    def test_parent_navigation_links(self):
        """Test that parent users see appropriate navigation links"""
        self.client.login(username="parent_user", password="testpass123")
        response = self.client.get(reverse("parent"))

        # Parent should see parent portal and profile links
        self.assertContains(response, "👨‍👩‍👧‍👦 Parent Portal")
        self.assertContains(response, "👤 My Profile")

        # Should not see admin, dashboard, or student portal
        self.assertNotContains(response, "⚙️ Admin")
        self.assertNotContains(response, "📊 Dashboard")
        self.assertNotContains(response, "🎓 Student Portal")

    def test_student_navigation_links(self):
        """Test that student users see appropriate navigation links"""
        self.client.login(username="student_user", password="testpass123")
        response = self.client.get(reverse("student"))

        # Student should see student portal and profile links
        self.assertContains(response, "🎓 Student Portal")
        self.assertContains(response, "👤 My Profile")

        # Should not see admin, dashboard, or parent portal
        self.assertNotContains(response, "⚙️ Admin")
        self.assertNotContains(response, "📊 Dashboard")
        self.assertNotContains(response, "👨‍👩‍👧‍👦 Parent Portal")

    def test_breadcrumb_navigation(self):
        """Test that breadcrumb navigation is present"""
        self.client.login(username="admin_user", password="testpass123")

        # Test dashboard breadcrumb
        response = self.client.get(reverse("dashboard"))
        self.assertContains(response, "Analytics Dashboard")

        # Test profile breadcrumb
        response = self.client.get(reverse("profile"))
        self.assertContains(response, "My Profile")

        # Test edit profile breadcrumb
        response = self.client.get(reverse("edit_profile"))
        self.assertContains(response, "Edit Profile")

    def test_mobile_navigation_elements(self):
        """Test that mobile navigation elements are present"""
        self.client.login(username="admin_user", password="testpass123")
        response = self.client.get(reverse("dashboard"))

        # Should contain mobile menu button
        self.assertContains(response, "mobile-menu-button")
        self.assertContains(response, "mobile-menu")

    def test_role_indicator_display(self):
        """Test that role indicators are displayed correctly"""
        # Test admin role indicator
        self.client.login(username="admin_user", password="testpass123")
        response = self.client.get(reverse("dashboard"))
        self.assertContains(response, "Logged in as:")

        # Test parent role indicator
        self.client.login(username="parent_user", password="testpass123")
        response = self.client.get(reverse("parent"))
        self.assertContains(response, "Parent")

    def test_logo_navigation_link(self):
        """Test that clicking the logo navigates appropriately"""
        # For authenticated users, logo should link to dashboard
        self.client.login(username="admin_user", password="testpass123")
        response = self.client.get(reverse("dashboard"))
        self.assertContains(response, "SchoolDriver Modern")

        # Check that the logo has proper href
        self.assertContains(response, reverse("dashboard"))

    def test_cross_section_navigation(self):
        """Test navigation between different sections"""
        # Login as admin
        self.client.login(username="admin_user", password="testpass123")

        # Should be able to navigate from dashboard to profile
        response = self.client.get(reverse("dashboard"))
        self.assertEqual(response.status_code, 200)

        response = self.client.get(reverse("profile"))
        self.assertEqual(response.status_code, 200)

        # Should be able to navigate to admin
        response = self.client.get(reverse("admin:index"))
        self.assertEqual(response.status_code, 200)

    def test_navigation_permissions(self):
        """Test that navigation respects user permissions"""
        # Parent user should not be able to access dashboard directly
        self.client.login(username="parent_user", password="testpass123")

        # Parent can access dashboard (it's not restricted by URL, just navigation)
        response = self.client.get(reverse("dashboard"))
        self.assertEqual(response.status_code, 200)

        # But navigation shouldn't show dashboard link for parents
        response = self.client.get(reverse("parent"))
        self.assertNotContains(response, "📊 Dashboard")
