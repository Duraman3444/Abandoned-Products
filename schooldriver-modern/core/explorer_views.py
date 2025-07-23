from django.views.generic import TemplateView
from django.shortcuts import redirect
from django.conf import settings
from django.urls import reverse


class ApiLandingView(TemplateView):
    """
    API Explorer landing page
    - In production: redirects to Swagger UI
    - In DEBUG mode: shows index page with all documentation options
    """
    template_name = 'api/landing.html'
    
    def get(self, request, *args, **kwargs):
        # In production, redirect directly to Swagger UI
        if not settings.DEBUG:
            return redirect('swagger-ui')
        
        # In DEBUG mode, show the landing page
        return super().get(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Add API documentation URLs
        context.update({
            'schema_url': reverse('schema'),
            'swagger_ui_url': reverse('swagger-ui'),
            'redoc_url': reverse('redoc'),
            'api_endpoints': [
                {'name': 'Students', 'url': '/api/v1/students/', 'description': 'Student records and management'},
                {'name': 'Applicants', 'url': '/api/v1/applicants/', 'description': 'Admission applications'},
                {'name': 'Grade Levels', 'url': '/api/v1/grade-levels/', 'description': 'Academic grade levels'},
                {'name': 'School Years', 'url': '/api/v1/school-years/', 'description': 'Academic year management'},
                {'name': 'Emergency Contacts', 'url': '/api/v1/emergency-contacts/', 'description': 'Student emergency contacts'},
                {'name': 'Feeder Schools', 'url': '/api/v1/feeder-schools/', 'description': 'Feeder school management'},
                {'name': 'Admission Levels', 'url': '/api/v1/admission-levels/', 'description': 'Admission process stages'},
                {'name': 'Admission Checks', 'url': '/api/v1/admission-checks/', 'description': 'Admission requirements'},
                {'name': 'Applicant Documents', 'url': '/api/v1/applicant-documents/', 'description': 'Document management'},
            ]
        })
        
        return context
