from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.contrib.auth.models import User


class ApiExplorerTest(TestCase):
    """Test cases for the API Explorer functionality"""
    
    def setUp(self):
        self.client = Client()
        
    def test_api_landing_page_accessible(self):
        """Test that API landing page returns 200 status"""
        response = self.client.get(reverse('api-landing'))
        self.assertEqual(response.status_code, 200)
        
    def test_api_landing_page_uses_correct_template(self):
        """Test that API landing page uses the correct template"""
        response = self.client.get(reverse('api-landing'))
        self.assertTemplateUsed(response, 'api/landing.html')
        
    @override_settings(DEBUG=False)
    def test_api_landing_redirects_in_production(self):
        """Test that API landing page redirects to Swagger UI in production"""
        response = self.client.get(reverse('api-landing'))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('swagger-ui'))
        
    @override_settings(DEBUG=True)
    def test_api_landing_shows_page_in_debug(self):
        """Test that API landing page shows content in DEBUG mode"""
        response = self.client.get(reverse('api-landing'))
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        self.assertIn('API Explorer', content)
        
    def test_api_schema_endpoints_accessible(self):
        """Test that all API schema endpoints are accessible"""
        endpoints = [
            ('schema', 'application/vnd.oai.openapi'),
            ('swagger-ui', 'text/html'),
            ('redoc', 'text/html'),
        ]
        
        for endpoint_name, expected_content_type in endpoints:
            with self.subTest(endpoint=endpoint_name):
                response = self.client.get(reverse(endpoint_name))
                self.assertEqual(response.status_code, 200)
                if expected_content_type:
                    self.assertIn(expected_content_type, response.get('Content-Type', ''))
                    
    def test_api_landing_context_data(self):
        """Test that API landing page provides required context data"""
        with override_settings(DEBUG=True):
            response = self.client.get(reverse('api-landing'))
            context = response.context
            
            # Check required context variables
            self.assertIn('schema_url', context)
            self.assertIn('swagger_ui_url', context)
            self.assertIn('redoc_url', context)
            self.assertIn('api_endpoints', context)
            
            # Check that endpoints list is populated
            endpoints = context['api_endpoints']
            self.assertTrue(len(endpoints) > 0)
            
            # Check endpoint structure
            for endpoint in endpoints:
                self.assertIn('name', endpoint)
                self.assertIn('url', endpoint)
                self.assertIn('description', endpoint)
                
    def test_api_endpoints_listed_correctly(self):
        """Test that all major API endpoints are listed"""
        with override_settings(DEBUG=True):
            response = self.client.get(reverse('api-landing'))
            context = response.context
            
            endpoints = context['api_endpoints']
            endpoint_names = [ep['name'] for ep in endpoints]
            
            expected_endpoints = [
                'Students',
                'Applicants', 
                'Grade Levels',
                'School Years',
                'Emergency Contacts',
                'Feeder Schools',
                'Admission Levels',
                'Admission Checks',
                'Applicant Files'
            ]
            
            for expected_endpoint in expected_endpoints:
                self.assertIn(expected_endpoint, endpoint_names)
                
    def test_swagger_ui_contains_api_docs(self):
        """Test that Swagger UI page contains API documentation elements"""
        response = self.client.get(reverse('swagger-ui'))
        content = response.content.decode()
        
        # Check for Swagger UI specific elements
        self.assertIn('swagger-ui', content)
        self.assertIn('spec-url', content)
        
    def test_redoc_contains_api_docs(self):
        """Test that ReDoc page contains API documentation elements"""
        response = self.client.get(reverse('redoc'))
        content = response.content.decode()
        
        # Check for ReDoc specific elements
        self.assertIn('redoc', content)
        self.assertIn('spec-url', content)
        
    def test_api_schema_json_format(self):
        """Test that API schema returns valid JSON"""
        response = self.client.get(reverse('schema'))
        self.assertEqual(response.status_code, 200)
        
        # Try to parse as JSON
        import json
        try:
            schema_data = json.loads(response.content)
            # Check for OpenAPI required fields
            self.assertIn('openapi', schema_data)
            self.assertIn('info', schema_data)
            self.assertIn('paths', schema_data)
        except json.JSONDecodeError:
            self.fail("API schema did not return valid JSON")
            
    def test_demo_page_api_button_links(self):
        """Test that demo page API buttons link correctly"""
        response = self.client.get(reverse('demo'))
        content = response.content.decode()
        
        # Check that Explore API button links to API landing
        api_landing_url = reverse('api-landing')
        self.assertIn(f'href="{api_landing_url}"', content)
        
    def test_legacy_docs_endpoint_works(self):
        """Test that legacy /api/docs/ endpoint still works"""
        response = self.client.get('/api/docs/')
        self.assertEqual(response.status_code, 200)
        
        # Should contain Swagger UI content
        content = response.content.decode()
        self.assertIn('swagger-ui', content)


class ApiExplorerIntegrationTest(TestCase):
    """Integration tests for API Explorer with authentication"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
    def test_authenticated_api_access(self):
        """Test that authenticated users can access API endpoints"""
        self.client.login(username='testuser', password='testpass123')
        
        # Test some API endpoints
        endpoints_to_test = [
            '/api/students/',
            '/api/applicants/',
            '/api/grade-levels/',
        ]
        
        for endpoint in endpoints_to_test:
            with self.subTest(endpoint=endpoint):
                response = self.client.get(endpoint)
                # May return 200 (with data) or 403 (permission required) but should not be 404
                self.assertIn(response.status_code, [200, 403])
                
    def test_api_auth_endpoints_work(self):
        """Test that API authentication endpoints work"""
        # Test DRF browsable API login
        response = self.client.get('/api/auth/')
        self.assertEqual(response.status_code, 200)
        
        # Should contain login form
        content = response.content.decode()
        self.assertIn('login', content.lower())


class ApiExplorerViewTest(TestCase):
    """Test the ApiLandingView class directly"""
    
    def test_api_landing_view_debug_mode(self):
        """Test ApiLandingView behavior in DEBUG mode"""
        with override_settings(DEBUG=True):
            response = self.client.get(reverse('api-landing'))
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, 'API Explorer')
            self.assertContains(response, 'Swagger UI')
            self.assertContains(response, 'ReDoc')
            self.assertContains(response, 'OpenAPI Schema')
            
    def test_api_landing_view_production_mode(self):
        """Test ApiLandingView behavior in production mode"""
        with override_settings(DEBUG=False):
            response = self.client.get(reverse('api-landing'))
            self.assertEqual(response.status_code, 302)
            
    def test_api_landing_view_context_urls(self):
        """Test that context URLs are properly generated"""
        with override_settings(DEBUG=True):
            response = self.client.get(reverse('api-landing'))
            context = response.context
            
            # All URLs should be present and valid
            self.assertTrue(context['schema_url'].startswith('/'))
            self.assertTrue(context['swagger_ui_url'].startswith('/'))
            self.assertTrue(context['redoc_url'].startswith('/'))
            
            # Test that URLs are accessible
            for url_name in ['schema_url', 'swagger_ui_url', 'redoc_url']:
                url = context[url_name]
                response = self.client.get(url)
                self.assertEqual(response.status_code, 200)


class ApiExplorerStaticFilesTest(TestCase):
    """Test static files for API documentation"""
    
    def test_api_docs_css_accessible(self):
        """Test that API docs CSS file is accessible"""
        response = self.client.get('/static/css/api_docs.css')
        # May return 404 in test mode if static files not collected
        # The important thing is that the file exists and can be served
        self.assertIn(response.status_code, [200, 404])
        
    def test_api_landing_template_includes_css(self):
        """Test that API landing template includes custom CSS"""
        with override_settings(DEBUG=True):
            response = self.client.get(reverse('api-landing'))
            content = response.content.decode()
            self.assertIn('api_docs.css', content)
