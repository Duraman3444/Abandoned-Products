from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
import json

# Import auth tests
from .auth_tests import AuthTests, PasswordValidationTests


class DashboardTemplateTests(TestCase):
    def setUp(self):
        """Create staff user for template tests."""
        self.staff_user = User.objects.create_user(
            username='staffuser',
            email='staff@example.com',
            password='testpass123',
            is_staff=True
        )
        self.client.login(username='staffuser', password='testpass123')
    
    def test_dashboard_status_200(self):
        """Test that the dashboard view returns HTTP 200."""
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        
    def test_dashboard_view_uses_correct_template(self):
        """Test that the dashboard view uses the correct template."""
        response = self.client.get(reverse('dashboard'))
        self.assertTemplateUsed(response, 'dashboard.html')
        
    def test_dashboard_renders_all_charts(self):
        """Test that the dashboard contains all 4 chart canvas elements."""
        response = self.client.get(reverse('dashboard'))
        
        # Check for all 4 chart canvases
        self.assertContains(response, 'id="pipelineChart"')
        self.assertContains(response, 'id="documentsChart"')
        self.assertContains(response, 'id="statusChart"')
        self.assertContains(response, 'id="trendsChart"')
        
        # Count canvas elements (should be 4)
        canvas_count = response.content.decode().count('<canvas')
        self.assertEqual(canvas_count, 4)
        
    def test_dashboard_contains_chart_titles(self):
        """Test that the dashboard contains all chart titles."""
        response = self.client.get(reverse('dashboard'))
        
        self.assertContains(response, 'Admission Pipeline Progress')
        self.assertContains(response, 'Document Completion Rates')
        self.assertContains(response, 'Applicant Status Distribution')
        self.assertContains(response, 'Monthly Admission Trends')
        
    def test_dashboard_view_contains_chart_script(self):
        """Test that the dashboard view contains Chart.js script."""
        response = self.client.get(reverse('dashboard'))
        self.assertContains(response, 'chart.min.js')
        self.assertContains(response, 'Chart(')
        
    def test_dashboard_contains_complete_data_structure(self):
        """Test that the dashboard view includes all required chart data."""
        response = self.client.get(reverse('dashboard'))
        
        # Check that dashboard data is present in context
        self.assertIn('dashboard_data', response.context)
        self.assertIn('dashboard_data_json', response.context)
        
        dashboard_data = response.context['dashboard_data']
        
        # Verify all chart data sections exist
        self.assertIn('pipeline', dashboard_data)
        self.assertIn('documents', dashboard_data)
        self.assertIn('status', dashboard_data)
        self.assertIn('trends', dashboard_data)
        self.assertIn('summary', dashboard_data)
        
        # Verify pipeline data structure
        pipeline = dashboard_data['pipeline']
        self.assertIn('labels', pipeline)
        self.assertIn('values', pipeline)
        self.assertIn('colors', pipeline)
        self.assertEqual(len(pipeline['labels']), 4)  # Applied, Reviewed, Interviewed, Accepted
        
        # Verify documents data structure
        documents = dashboard_data['documents']
        self.assertIn('labels', documents)
        self.assertIn('completion_rates', documents)
        self.assertEqual(len(documents['labels']), 5)  # 5 document types
        
        # Verify status data structure
        status = dashboard_data['status']
        self.assertIn('labels', status)
        self.assertIn('values', status)
        self.assertEqual(len(status['labels']), 6)  # 6 status types
        
        # Verify trends data structure
        trends = dashboard_data['trends']
        self.assertIn('labels', trends)
        self.assertIn('applications', trends)
        self.assertIn('acceptances', trends)
        self.assertEqual(len(trends['labels']), 12)  # 12 months
        
    def test_dashboard_summary_statistics(self):
        """Test that summary statistics are calculated correctly."""
        response = self.client.get(reverse('dashboard'))
        
        dashboard_data = response.context['dashboard_data']
        summary = dashboard_data['summary']
        
        # Check summary fields exist
        self.assertIn('total_applications', summary)
        self.assertIn('total_acceptances', summary)
        self.assertIn('acceptance_rate', summary)
        self.assertIn('pending_applications', summary)
        
        # Verify calculations make sense
        self.assertGreater(summary['total_applications'], 0)
        self.assertGreater(summary['total_acceptances'], 0)
        self.assertGreater(summary['acceptance_rate'], 0)
        self.assertLess(summary['acceptance_rate'], 100)
        
    def test_dashboard_responsive_layout(self):
        """Test that the dashboard includes responsive styling."""
        response = self.client.get(reverse('dashboard'))
        
        # Check for Tailwind CSS classes
        self.assertContains(response, 'grid')
        self.assertContains(response, 'lg:grid-cols-2')
        self.assertContains(response, 'max-w-7xl')
        self.assertContains(response, 'mx-auto')
        
    def test_dashboard_realtime_update_functionality(self):
        """Test that realtime update JavaScript is included."""
        response = self.client.get(reverse('dashboard'))
        
        # Check for realtime update functions
        self.assertContains(response, 'updateChartData')
        self.assertContains(response, 'setInterval')
        self.assertContains(response, '15000')  # 15 second interval
        
    def test_dashboard_tailwind_integration(self):
        """Test that Tailwind CSS is properly integrated."""
        response = self.client.get(reverse('dashboard'))
        
        # Check for Tailwind CDN
        self.assertContains(response, 'tailwindcss.com')
        
        # Check for common Tailwind classes
        self.assertContains(response, 'bg-white')
        self.assertContains(response, 'rounded-lg')
        self.assertContains(response, 'shadow')


class DashboardAdminIntegrationTests(TestCase):
    """Tests for Step 1.4: Admin integration and staff access."""
    
    def setUp(self):
        """Create test users for authentication tests."""
        # Staff user
        self.staff_user = User.objects.create_user(
            username='staffuser',
            email='staff@example.com',
            password='testpass123',
            is_staff=True
        )
        
        # Regular user (non-staff)
        self.regular_user = User.objects.create_user(
            username='regularuser',
            email='regular@example.com',
            password='testpass123',
            is_staff=False
        )
    
    def test_dashboard_staff_access(self):
        """Test that staff user gets HTTP 200 for dashboard."""
        self.client.login(username='staffuser', password='testpass123')
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Analytics Dashboard')
        
    def test_dashboard_nonstaff_redirect(self):
        """Test that non-staff user is redirected to login."""
        self.client.login(username='regularuser', password='testpass123')
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/admin/login/', response.url)
        
    def test_dashboard_anonymous_redirect(self):
        """Test that anonymous user is redirected to login."""
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/admin/login/', response.url)
        
    def test_admin_link_present(self):
        """Test that admin index contains the Dashboard link."""
        self.client.login(username='staffuser', password='testpass123')
        response = self.client.get('/admin/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Analytics Dashboard')
        self.assertContains(response, reverse('dashboard'))
        
    def test_dashboard_quick_actions_present(self):
        """Test that dashboard contains all three quick-action buttons."""
        self.client.login(username='staffuser', password='testpass123')
        response = self.client.get(reverse('dashboard'))
        
        # Check for quick action buttons
        self.assertContains(response, 'Download CSV')
        self.assertContains(response, 'Refresh Data')
        self.assertContains(response, 'Admissions Report')
        
        # Check for button functions
        self.assertContains(response, 'downloadCSV()')
        self.assertContains(response, 'refreshDataNow()')
        self.assertContains(response, '/admin/admissions/applicant/')
        
    def test_dashboard_responsive_design(self):
        """Test that dashboard includes responsive design elements."""
        self.client.login(username='staffuser', password='testpass123')
        response = self.client.get(reverse('dashboard'))
        
        # Check for responsive classes
        self.assertContains(response, 'flex-wrap')
        self.assertContains(response, 'md:justify-start')
        self.assertContains(response, 'justify-center')


class DashboardViewTest(TestCase):
    """Legacy tests for backward compatibility."""
    
    def setUp(self):
        """Create staff user for legacy tests."""
        self.staff_user = User.objects.create_user(
            username='staffuser',
            email='staff@example.com',
            password='testpass123',
            is_staff=True
        )
    
    def test_dashboard_view_returns_200(self):
        """Test that the dashboard view returns HTTP 200 for staff."""
        self.client.login(username='staffuser', password='testpass123')
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
