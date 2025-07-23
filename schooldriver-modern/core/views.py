from django.views.generic import TemplateView
from django.http import JsonResponse
from django.contrib.auth.models import User
from students.models import Student
from admissions.models import Applicant
import json


class DemoPageView(TemplateView):
    """Public demo page showcasing SchoolDriver-Modern flagship features"""
    template_name = 'demo.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Demo metrics (cached/hardcoded for performance)
        context.update({
            'total_students': Student.objects.count() or 32,
            'total_applicants': Applicant.objects.count() or 20,
            'total_users': User.objects.count() or 25,
            'demo_role': 'Guest',
            'exported_pdfs_count': 47,  # Mock data
            
            # Chart data for real-time analytics
            'gpa_data': json.dumps({
                'labels': ['Grade K', 'Grade 1', 'Grade 2', 'Grade 3', 'Grade 4', 'Grade 5'],
                'datasets': [{
                    'label': 'Average GPA',
                    'data': [3.2, 3.1, 3.4, 2.9, 3.3, 3.0],  # Ensure all values are well within 4.0 limit
                    'backgroundColor': 'rgba(54, 162, 235, 0.2)',
                    'borderColor': 'rgba(54, 162, 235, 1)',
                    'borderWidth': 2
                }]
            }),
            
            # API endpoints for showcase
            'api_endpoints': [
                {'name': 'Students API', 'url': '/api/students/', 'method': 'GET'},
                {'name': 'Applicants API', 'url': '/api/applicants/', 'method': 'GET'},
                {'name': 'Admissions API', 'url': '/api/admissions/', 'method': 'GET'},
                {'name': 'Auth Token', 'url': '/api/auth/token/', 'method': 'POST'},
            ],
            
            # Feature showcase data
            'features': {
                'schedule_export': {
                    'title': 'Schedule Export / Print System',
                    'description': 'Export student schedules to CSV/PDF with print-optimized templates and teacher contact integration.',
                    'icon': 'bi-download',
                    'demo_action': 'View Export Options'
                },
                'authentication': {
                    'title': 'Modern Authentication System', 
                    'description': 'Role-based access control with secure session management for Students, Parents, Teachers, and Admins.',
                    'icon': 'bi-shield-check',
                    'demo_action': 'Try Login Portal'
                },
                'responsive_design': {
                    'title': 'Mobile-Responsive Design',
                    'description': 'Bootstrap 5 responsive layouts with mobile-first design and touch-friendly interface components.',
                    'icon': 'bi-phone',
                    'demo_action': 'View Mobile Demo'
                },
                'analytics': {
                    'title': 'Real-time Dashboard Analytics',
                    'description': 'Interactive performance metrics, grade trends, and attendance tracking with Chart.js visualizations.',
                    'icon': 'bi-graph-up',
                    'demo_action': 'View Analytics'
                },
                'search_filtering': {
                    'title': 'Advanced Search & Filtering',
                    'description': 'Global search across students, courses, and teachers with advanced filtering and status management.',
                    'icon': 'bi-search',
                    'demo_action': 'Try Search'
                },
                'api_architecture': {
                    'title': 'API-First Architecture',
                    'description': 'RESTful API with Django REST Framework, token authentication, and comprehensive documentation.',
                    'icon': 'bi-code-slash',
                    'demo_action': 'Explore API'
                }
            }
        })
        
        return context
