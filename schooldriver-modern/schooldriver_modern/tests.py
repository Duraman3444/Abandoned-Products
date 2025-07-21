from django.test import TestCase
from django.urls import reverse
import json


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
        
    def test_dashboard_contains_student_chart_container(self):
        """Test that the dashboard contains the student chart canvas element."""
        response = self.client.get(reverse('dashboard'))
        self.assertContains(response, 'id="studentChart"')
        self.assertContains(response, '<canvas')
        
    def test_dashboard_contains_student_data(self):
        """Test that the dashboard view includes student enrollment data."""
        response = self.client.get(reverse('dashboard'))
        
        # Check that student data is present in context
        self.assertIn('student_data', response.context)
        self.assertIn('student_data_json', response.context)
        
        student_data = response.context['student_data']
        self.assertIn('labels', student_data)
        self.assertIn('counts', student_data)
        self.assertIn('total_students', student_data)
        
        # Verify the dummy data structure
        self.assertEqual(len(student_data['labels']), 5)
        self.assertEqual(len(student_data['counts']), 5)
        self.assertEqual(student_data['total_students'], 600)
        
    def test_dashboard_contains_chart_title(self):
        """Test that the dashboard contains the correct chart title."""
        response = self.client.get(reverse('dashboard'))
        self.assertContains(response, 'Student Enrollment by Grade Level')
        self.assertContains(response, 'Total Students: 600')
