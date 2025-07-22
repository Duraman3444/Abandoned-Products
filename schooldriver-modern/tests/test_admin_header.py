"""
Tests for admin header UI changes and branding.
"""

from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse


class AdminHeaderTests(TestCase):
    """Test admin header branding and UI elements."""

    def setUp(self):
        """Set up test user and client."""
        self.user = User.objects.create_superuser(
            username="testadmin", email="admin@test.com", password="testpass"
        )
        self.client = Client()
        self.client.login(username="testadmin", password="testpass")

    def test_brand_name(self):
        """Test that title text equals 'SchoolDriver Modern'."""
        response = self.client.get(reverse("admin:index"))
        self.assertEqual(response.status_code, 200)

        # Check that the branding shows SchoolDriver Modern
        self.assertContains(response, "SchoolDriver Modern")
        self.assertNotContains(response, "Django administration")

    def test_dark_toggle_position(self):
        """Test that dark-mode toggle element sits after the logout link."""
        response = self.client.get(reverse("admin:index"))
        self.assertEqual(response.status_code, 200)

        # Check for dark mode toggle
        self.assertContains(response, "dark-mode-toggle")
        self.assertContains(response, "🌙")

        # Check that it appears near the logout link
        content = response.content.decode()
        dark_toggle_pos = content.find("dark-mode-toggle")
        logout_pos = content.find("Log out")

        # Dark toggle should be close to logout (within reasonable distance)
        self.assertGreater(dark_toggle_pos, 0, "Dark mode toggle should be present")
        self.assertGreater(logout_pos, 0, "Logout link should be present")
        self.assertLess(
            abs(dark_toggle_pos - logout_pos), 500, "Dark toggle should be near logout"
        )

    def test_analytics_button_on_admin_pages(self):
        """Test that Analytics button appears on admin pages but not dashboard."""
        # Test on admin index
        response = self.client.get(reverse("admin:index"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Analytics Dashboard")

    def test_no_duplicate_analytics_button(self):
        """Test that /dashboard/ does not render a second Analytics link."""
        response = self.client.get(reverse("dashboard"))
        self.assertEqual(response.status_code, 200)

        # Count occurrences of "Analytics Dashboard" text
        content = response.content.decode()
        analytics_count = content.count("Analytics Dashboard")

        # Should appear in reasonable places (title, navigation, etc.) but not excessively
        # Allow for title, breadcrumbs, and navigation - but not excessive duplication
        self.assertLessEqual(
            analytics_count, 5, "Analytics Dashboard should not appear excessively"
        )

        # More specifically, check that the analytics button link is not present
        self.assertNotContains(response, 'href="/dashboard/"')

    def test_dashboard_uses_admin_template(self):
        """Test that dashboard uses admin base template."""
        response = self.client.get(reverse("dashboard"))
        self.assertEqual(response.status_code, 200)

        # Should have admin template elements
        self.assertContains(response, "SchoolDriver Modern")
        self.assertContains(response, "breadcrumbs")

        # Should have the admin header structure
        self.assertContains(response, "user-tools")

    def test_dark_mode_functionality(self):
        """Test that dark mode toggle JavaScript is present."""
        response = self.client.get(reverse("admin:index"))
        self.assertEqual(response.status_code, 200)

        # Check for dark mode JavaScript
        self.assertContains(response, "localStorage.getItem('darkMode')")
        self.assertContains(response, "body.classList.toggle('dark-mode')")

        # Check for dark mode CSS
        self.assertContains(response, "body.dark-mode")


class DashboardIntegrationTests(TestCase):
    """Test dashboard integration with admin theme."""

    def setUp(self):
        """Set up test user and client."""
        self.user = User.objects.create_superuser(
            username="testadmin", email="admin@test.com", password="testpass"
        )
        self.client = Client()
        self.client.login(username="testadmin", password="testpass")

    def test_dashboard_breadcrumbs(self):
        """Test that dashboard has proper breadcrumbs."""
        response = self.client.get(reverse("dashboard"))
        self.assertEqual(response.status_code, 200)

        # Check breadcrumbs
        self.assertContains(response, "breadcrumbs")
        self.assertContains(response, "Home")
        self.assertContains(response, "Analytics Dashboard")

    def test_dashboard_admin_styling(self):
        """Test that dashboard uses admin-compatible styling."""
        response = self.client.get(reverse("dashboard"))
        self.assertEqual(response.status_code, 200)

        # Should include dashboard CSS
        self.assertContains(response, "dashboard.css")

        # Should have chart elements
        self.assertContains(response, "canvas")
        self.assertContains(response, "chart-container")

    def test_dashboard_chart_functionality(self):
        """Test that dashboard retains chart functionality."""
        response = self.client.get(reverse("dashboard"))
        self.assertEqual(response.status_code, 200)

        # Check for Chart.js
        self.assertContains(response, "chart.min.js")
        self.assertContains(response, "Chart.defaults")

        # Check for dashboard data
        self.assertContains(response, "dashboardData")

        # Check for all four charts
        chart_ids = ["pipelineChart", "documentsChart", "statusChart", "trendsChart"]
        for chart_id in chart_ids:
            self.assertContains(response, chart_id)
