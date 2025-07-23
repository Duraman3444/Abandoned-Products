from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User


class DemoPageTest(TestCase):
    """Test cases for the demo page functionality"""
    
    def setUp(self):
        self.client = Client()
        self.demo_url = reverse('demo')
        
    def test_demo_page_accessible(self):
        """Test that demo page returns 200 status"""
        response = self.client.get(self.demo_url)
        self.assertEqual(response.status_code, 200)
        
    def test_demo_page_uses_correct_template(self):
        """Test that demo page uses the correct template"""
        response = self.client.get(self.demo_url)
        self.assertTemplateUsed(response, 'demo.html')
        
    def test_demo_page_contains_all_features(self):
        """Test that demo page contains all six flagship features"""
        response = self.client.get(self.demo_url)
        content = response.content.decode()
        
        # Check for all six feature sections
        feature_titles = [
            'Schedule Export / Print System',
            'Modern Authentication System',
            'Mobile-Responsive Design', 
            'Real-time Dashboard Analytics',
            'Advanced Search & Filtering',
            'API-First Architecture'
        ]
        
        for title in feature_titles:
            self.assertIn(title, content, f"Feature '{title}' not found on demo page")
            
    def test_demo_page_context_data(self):
        """Test that demo page provides required context data"""
        response = self.client.get(self.demo_url)
        context = response.context
        
        # Check required context variables
        self.assertIn('total_students', context)
        self.assertIn('total_applicants', context)
        self.assertIn('total_users', context)
        self.assertIn('demo_role', context)
        self.assertIn('gpa_data', context)
        self.assertIn('api_endpoints', context)
        self.assertIn('features', context)
        
    def test_demo_page_gpa_chart_data(self):
        """Test that GPA chart data is properly formatted JSON"""
        response = self.client.get(self.demo_url)
        context = response.context
        
        import json
        gpa_data = json.loads(context['gpa_data'])
        
        self.assertIn('labels', gpa_data)
        self.assertIn('datasets', gpa_data)
        self.assertTrue(len(gpa_data['labels']) > 0)
        self.assertTrue(len(gpa_data['datasets']) > 0)
        
    def test_demo_page_api_endpoints(self):
        """Test that API endpoints are provided"""
        response = self.client.get(self.demo_url)
        context = response.context
        
        api_endpoints = context['api_endpoints']
        self.assertTrue(len(api_endpoints) > 0)
        
        # Check endpoint structure
        for endpoint in api_endpoints:
            self.assertIn('name', endpoint)
            self.assertIn('url', endpoint)
            self.assertIn('method', endpoint)
            
    def test_demo_page_features_structure(self):
        """Test that features data has correct structure"""
        response = self.client.get(self.demo_url)
        context = response.context
        
        features = context['features']
        self.assertEqual(len(features), 6)
        
        # Check each feature has required fields
        for feature_key, feature_data in features.items():
            self.assertIn('title', feature_data)
            self.assertIn('description', feature_data)
            self.assertIn('icon', feature_data)
            self.assertIn('demo_action', feature_data)
            
    def test_demo_page_no_authentication_required(self):
        """Test that demo page is accessible without authentication"""
        # Make sure no user is logged in
        self.client.logout()
        
        response = self.client.get(self.demo_url)
        self.assertEqual(response.status_code, 200)
        
    def test_demo_page_responsive_elements(self):
        """Test that demo page contains responsive design elements"""
        response = self.client.get(self.demo_url)
        content = response.content.decode()
        
        # Check for Bootstrap responsive classes
        self.assertIn('col-lg-', content)
        self.assertIn('col-md-', content)
        self.assertIn('d-md-', content)
        
    def test_demo_page_chart_js_integration(self):
        """Test that Chart.js is properly integrated"""
        response = self.client.get(self.demo_url)
        content = response.content.decode()
        
        # Check for Chart.js elements
        self.assertIn('canvas id="gpaChart"', content)
        self.assertIn('chart.js', content)
        self.assertIn('demo.js', content)
        
    def test_demo_page_call_to_action_links(self):
        """Test that call-to-action links are present"""
        response = self.client.get(self.demo_url)
        content = response.content.decode()
        
        # Check for important navigation links
        self.assertIn('/accounts/login/', content)
        self.assertIn('/admin/', content)
        self.assertIn('github.com', content)
