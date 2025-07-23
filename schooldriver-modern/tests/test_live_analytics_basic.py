from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse


class LiveAnalyticsBasicTest(TestCase):
    """Basic tests for Live Analytics widget integration"""
    
    def setUp(self):
        self.client = Client()
        
        # Create test user
        self.user = User.objects.create_user(
            username='teststudent',
            password='testpass123',
            first_name='Test',
            last_name='Student'
        )
        self.user.profile.role = 'Student'
        self.user.profile.save()

    def test_student_dashboard_includes_live_analytics_widget(self):
        """Test that student dashboard contains live analytics widget elements"""
        # Login as student
        self.client.login(username='teststudent', password='testpass123')
        
        # Get dashboard page
        response = self.client.get('/student/')
        self.assertEqual(response.status_code, 200)
        
        content = response.content.decode()
        
        # Check for live analytics widget elements
        self.assertIn('liveAnalyticsChart', content, 
                     "Dashboard should contain live analytics chart canvas")
        self.assertIn('pauseLiveAnalytics', content,
                     "Dashboard should contain pause button")
        self.assertIn('Live Analytics', content,
                     "Dashboard should contain live analytics title")
        
    def test_dashboard_includes_chartjs_and_live_analytics_script(self):
        """Test that dashboard includes required JavaScript files"""
        self.client.login(username='teststudent', password='testpass123')
        
        response = self.client.get('/student/')
        content = response.content.decode()
        
        # Check for Chart.js CDN
        self.assertIn('chart.js', content,
                     "Dashboard should include Chart.js library")
        
        # Check for live analytics JavaScript
        self.assertIn('live_analytics.js', content,
                     "Dashboard should include live analytics JavaScript")
        
        # Check for initialization call
        self.assertIn('initializeLiveAnalytics', content,
                     "Dashboard should call live analytics initialization")

    def test_live_analytics_widget_responsive_structure(self):
        """Test that widget has proper responsive Bootstrap structure"""
        self.client.login(username='teststudent', password='testpass123')
        
        response = self.client.get('/student/')
        content = response.content.decode()
        
        # Check for responsive grid classes
        self.assertIn('col-lg-4', content,
                     "Widget should use responsive grid layout")
        self.assertIn('card h-100', content,
                     "Widget should be in a card with full height")

    def test_widget_configuration_parameters(self):
        """Test that widget is configured with proper parameters"""
        self.client.login(username='teststudent', password='testpass123')
        
        response = self.client.get('/student/')
        content = response.content.decode()
        
        # Check configuration parameters
        self.assertIn('maxDataPoints: 50', content,
                     "Widget should be configured with 50 data points")
        self.assertIn('updateInterval: 2000', content,
                     "Widget should update every 2 seconds")
        self.assertIn('maxFPS: 30', content,
                     "Widget should limit to 30 FPS")

    def test_live_analytics_static_file_exists(self):
        """Test that live analytics JavaScript file is accessible"""
        self.client.login(username='teststudent', password='testpass123')
        
        # Try to access the static file
        response = self.client.get('/static/js/live_analytics.js')
        self.assertEqual(response.status_code, 200,
                        "Live analytics JavaScript file should be accessible")
        
        content = response.content.decode()
        
        # Check for key functions
        self.assertIn('class LiveAnalytics', content,
                     "File should contain LiveAnalytics class")
        self.assertIn('initializeLiveAnalytics', content,
                     "File should contain initialization function")
        self.assertIn('Chart.js', content,
                     "File should contain Chart.js integration")

    def test_widget_visual_elements(self):
        """Test that widget contains required visual elements"""
        self.client.login(username='teststudent', password='testpass123')
        
        response = self.client.get('/student/')
        content = response.content.decode()
        
        # Check for visual elements
        self.assertIn('bi-graph-up', content,
                     "Widget should have graph icon")
        self.assertIn('Updates every 2 seconds', content,
                     "Widget should show update frequency")
        self.assertIn('Last 50 data points', content,
                     "Widget should show data point limit")
        self.assertIn('height: 200px', content,
                     "Canvas should have fixed height")

    def test_pause_button_configuration(self):
        """Test that pause button is properly configured"""
        self.client.login(username='teststudent', password='testpass123')
        
        response = self.client.get('/student/')
        content = response.content.decode()
        
        # Check pause button
        self.assertIn('id="pauseLiveAnalytics"', content,
                     "Pause button should have correct ID")
        self.assertIn('btn-outline-warning', content,
                     "Pause button should have warning style")
        self.assertIn('>Pause<', content,
                     "Button should show 'Pause' text initially")

    def test_widget_container_structure(self):
        """Test that widget has proper container structure"""
        self.client.login(username='teststudent', password='testpass123')
        
        response = self.client.get('/student/')
        content = response.content.decode()
        
        # Check container structure
        self.assertIn('card-header', content,
                     "Widget should have card header")
        self.assertIn('card-body', content,
                     "Widget should have card body")
        self.assertIn('position: relative', content,
                     "Canvas container should have relative positioning")


class LiveAnalyticsJavaScriptIntegrationTest(TestCase):
    """Test JavaScript integration aspects"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='teststudent',
            password='testpass123'
        )
        self.user.profile.role = 'Student'
        self.user.profile.save()

    def test_javascript_initialization_code(self):
        """Test that proper JavaScript initialization code is generated"""
        self.client.login(username='teststudent', password='testpass123')
        
        response = self.client.get('/student/')
        content = response.content.decode()
        
        # Check initialization code structure
        self.assertIn('DOMContentLoaded', content,
                     "Should wait for DOM to load")
        self.assertIn('typeof initializeLiveAnalytics === \'function\'', content,
                     "Should check if function exists before calling")
        
        # Check configuration object
        init_code = content[content.find('initializeLiveAnalytics'):content.find(');', content.find('initializeLiveAnalytics'))]
        self.assertIn('liveAnalyticsChart', init_code,
                     "Should pass canvas ID")
        self.assertIn('maxDataPoints', init_code,
                     "Should configure max data points")
        self.assertIn('updateInterval', init_code,
                     "Should configure update interval")
        self.assertIn('maxFPS', init_code,
                     "Should configure max FPS")

    def test_error_handling_code(self):
        """Test that JavaScript includes error handling"""
        response = self.client.get('/static/js/live_analytics.js')
        content = response.content.decode()
        
        # Check for error handling
        self.assertIn('console.error', content,
                     "Should include error logging")
        self.assertIn('try', content,
                     "Should include try-catch blocks")
        self.assertIn('if (!this.canvas', content,
                     "Should check for canvas existence")

    def test_performance_optimizations(self):
        """Test that performance optimizations are included"""
        response = self.client.get('/static/js/live_analytics.js')
        content = response.content.decode()
        
        # Check for performance features
        self.assertIn('requestAnimationFrame', content,
                     "Should use requestAnimationFrame")
        self.assertIn('frameInterval', content,
                     "Should limit frame rate")
        self.assertIn('shift()', content,
                     "Should use sliding window with shift")
        self.assertIn('cancelAnimationFrame', content,
                     "Should cancel animation frames when paused")

    def test_cleanup_functionality(self):
        """Test that cleanup functionality is implemented"""
        response = self.client.get('/static/js/live_analytics.js')
        content = response.content.decode()
        
        # Check cleanup methods
        self.assertIn('destroy()', content,
                     "Should have destroy method")
        self.assertIn('clearInterval', content,
                     "Should clear intervals on cleanup")
        self.assertIn('beforeunload', content,
                     "Should cleanup on page unload")


class LiveAnalyticsFileStructureTest(TestCase):
    """Test file structure and organization"""
    
    def test_static_files_organization(self):
        """Test that static files are properly organized"""
        from django.conf import settings
        import os
        
        # Check that live_analytics.js exists
        js_file = os.path.join(settings.BASE_DIR, 'static', 'js', 'live_analytics.js')
        self.assertTrue(os.path.exists(js_file),
                       "live_analytics.js should exist in static/js/")
        
        # Check test files exist
        test_file = os.path.join(settings.BASE_DIR, 'static', 'js', 'tests', 'live_analytics.test.js')
        self.assertTrue(os.path.exists(test_file),
                       "Test file should exist")
        
        # Check test runner exists
        runner_file = os.path.join(settings.BASE_DIR, 'static', 'js', 'tests', 'test_runner.html')
        self.assertTrue(os.path.exists(runner_file),
                       "Test runner should exist")

    def test_javascript_file_content_structure(self):
        """Test that JavaScript file has proper structure"""
        response = self.client.get('/static/js/live_analytics.js')
        content = response.content.decode()
        
        # Check class structure
        self.assertIn('class LiveAnalytics {', content,
                     "Should define LiveAnalytics class")
        self.assertIn('constructor(canvasId, options', content,
                     "Should have proper constructor")
        
        # Check key methods
        required_methods = [
            'initializeChart',
            'generateDataPoint',
            'addDataPoint',
            'update',
            'pause',
            'resume',
            'toggle',
            'destroy'
        ]
        
        for method in required_methods:
            self.assertIn(f'{method}(', content,
                         f"Should have {method} method")

    def test_export_functionality(self):
        """Test that module exports are properly configured"""
        response = self.client.get('/static/js/live_analytics.js')
        content = response.content.decode()
        
        # Check exports
        self.assertIn('window.LiveAnalytics', content,
                     "Should export LiveAnalytics to window")
        self.assertIn('window.initializeLiveAnalytics', content,
                     "Should export initialization function to window")
        self.assertIn('module.exports', content,
                     "Should support CommonJS exports for testing")
