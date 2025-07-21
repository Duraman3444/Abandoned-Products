from django.test import TestCase
from django.urls import reverse


class DashboardViewTest(TestCase):
    def test_dashboard_view_returns_200(self):
        """Test that the dashboard view returns HTTP 200."""
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        
    def test_dashboard_view_uses_correct_template(self):
        """Test that the dashboard view uses the correct template."""
        response = self.client.get(reverse('dashboard'))
        self.assertTemplateUsed(response, 'dashboard.html')
        
    def test_dashboard_view_contains_chart_script(self):
        """Test that the dashboard view contains Chart.js script."""
        response = self.client.get(reverse('dashboard'))
        self.assertContains(response, 'chart.min.js')
        self.assertContains(response, 'Chart(')
