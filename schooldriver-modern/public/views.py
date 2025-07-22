from django.shortcuts import render
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta
from students.models import Student, GradeLevel, SchoolYear
from admissions.models import OpenHouse, Applicant, AdmissionLevel
import logging

logger = logging.getLogger(__name__)


def home_view(request):
    """Public home page with recent news/announcements and school statistics"""
    try:
        # Get school statistics from real data
        current_school_year = SchoolYear.objects.filter(is_active=True).first()
        total_students = Student.objects.filter(is_active=True).count()
        grade_levels_count = GradeLevel.objects.count()
        
        # Get recent admissions activity
        recent_applications = Applicant.objects.filter(
            created_at__gte=timezone.now() - timedelta(days=30)
        ).count()
        
        # Get upcoming events
        upcoming_events = OpenHouse.objects.filter(
            date__gte=timezone.now(),
            is_active=True
        ).order_by('date')[:3]
        
        # Grade level distribution for statistics
        grade_distribution = Student.objects.filter(
            is_active=True
        ).values(
            'grade_level__name'
        ).annotate(
            count=Count('id')
        ).order_by('grade_level__order')
        
        context = {
            'current_school_year': current_school_year,
            'total_students': total_students,
            'grade_levels_count': grade_levels_count,
            'recent_applications': recent_applications,
            'upcoming_events': upcoming_events,
            'grade_distribution': grade_distribution,
            'last_updated': timezone.now(),
        }
        
    except Exception as e:
        logger.error(f"Error loading home page data: {e}")
        context = {
            'error': 'Unable to load school statistics at this time.'
        }
    
    return render(request, 'public/home.html', context)


def about_view(request):
    """About page with school information"""
    try:
        # Get real school data
        current_school_year = SchoolYear.objects.filter(is_active=True).first()
        total_students = Student.objects.filter(is_active=True).count()
        
        # Get faculty count (you may need to implement faculty model)
        # For now, using a placeholder
        faculty_count = 25  # Placeholder
        
        # Years in operation (assuming school started in 2000)
        years_operating = timezone.now().year - 2000
        
        context = {
            'current_school_year': current_school_year,
            'total_students': total_students,
            'faculty_count': faculty_count,
            'years_operating': years_operating,
            'accreditation_info': 'WASC Accredited',
            'mission_statement': 'Empowering students to achieve academic excellence and personal growth in a supportive learning environment.',
        }
        
    except Exception as e:
        logger.error(f"Error loading about page data: {e}")
        context = {}
    
    return render(request, 'public/about.html', context)


def admissions_view(request):
    """Admissions information page with real admission data"""
    try:
        # Get admission statistics
        total_applicants = Applicant.objects.count()
        current_year_applicants = Applicant.objects.filter(
            created_at__year=timezone.now().year
        ).count()
        
        # Get admission levels for process overview
        admission_levels = AdmissionLevel.objects.filter(
            is_active=True
        ).order_by('order')
        
        # Get upcoming open houses
        upcoming_events = OpenHouse.objects.filter(
            date__gte=timezone.now(),
            is_active=True
        ).order_by('date')
        
        # Application deadlines (you may want to create a model for this)
        application_deadlines = [
            {'deadline': 'February 1', 'description': 'Regular Decision Applications Due'},
            {'deadline': 'March 15', 'description': 'Financial Aid Applications Due'},
            {'deadline': 'April 10', 'description': 'Decision Letters Sent'},
        ]
        
        context = {
            'total_applicants': total_applicants,
            'current_year_applicants': current_year_applicants,
            'admission_levels': admission_levels,
            'upcoming_events': upcoming_events,
            'application_deadlines': application_deadlines,
        }
        
    except Exception as e:
        logger.error(f"Error loading admissions page data: {e}")
        context = {}
    
    return render(request, 'public/admissions.html', context)


def contact_view(request):
    """Contact page with school contact information"""
    context = {
        'school_name': 'Private School',
        'address': '123 Education Way, Learning City, CA 90210',
        'phone': '(555) 123-4567',
        'email': 'info@privateschool.edu',
        'office_hours': 'Monday - Friday: 8:00 AM - 5:00 PM',
        'departments': [
            {'name': 'Admissions Office', 'phone': '(555) 123-4568', 'email': 'admissions@privateschool.edu'},
            {'name': 'Student Services', 'phone': '(555) 123-4569', 'email': 'students@privateschool.edu'},
            {'name': 'Parent Relations', 'phone': '(555) 123-4570', 'email': 'parents@privateschool.edu'},
        ]
    }
    
    return render(request, 'public/contact.html', context)


def programs_view(request):
    """Academic programs page with grade-level information"""
    try:
        # Get grade levels grouped by school division
        grade_levels = GradeLevel.objects.all().order_by('order')
        
        # Group grades by division
        elementary_grades = grade_levels.filter(order__lte=6)  # K-5
        middle_grades = grade_levels.filter(order__gte=7, order__lte=9)  # 6-8
        high_school_grades = grade_levels.filter(order__gte=10)  # 9-12
        
        # Get student counts per division
        elementary_count = Student.objects.filter(
            grade_level__in=elementary_grades,
            is_active=True
        ).count()
        
        middle_count = Student.objects.filter(
            grade_level__in=middle_grades,
            is_active=True
        ).count()
        
        high_school_count = Student.objects.filter(
            grade_level__in=high_school_grades,
            is_active=True
        ).count()
        
        context = {
            'elementary_grades': elementary_grades,
            'middle_grades': middle_grades,
            'high_school_grades': high_school_grades,
            'elementary_count': elementary_count,
            'middle_count': middle_count,
            'high_school_count': high_school_count,
            'programs': [
                {
                    'name': 'STEM Program',
                    'description': 'Advanced science, technology, engineering, and mathematics curriculum',
                    'grades': 'Grades 6-12'
                },
                {
                    'name': 'Arts Integration',
                    'description': 'Creative arts integrated across all academic subjects',
                    'grades': 'Grades K-12'
                },
                {
                    'name': 'Advanced Placement',
                    'description': 'College-level courses for high school students',
                    'grades': 'Grades 10-12'
                },
            ]
        }
        
    except Exception as e:
        logger.error(f"Error loading programs page data: {e}")
        context = {}
    
    return render(request, 'public/programs.html', context)
