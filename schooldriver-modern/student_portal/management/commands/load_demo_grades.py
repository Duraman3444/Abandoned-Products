"""
Management command to create sample data for multiple school years
This helps test the semester filter and cumulative GPA functionality
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import date, timedelta
import random

from students.models import Student, SchoolYear
from academics.models import Course, CourseSection, Enrollment, Assignment, Grade, AssignmentCategory, Department


class Command(BaseCommand):
    help = 'Load demo grades for multiple school years for testing semester filter'

    def add_arguments(self, parser):
        parser.add_argument(
            '--student',
            type=str,
            default='test2',
            help='Username of the student to create demo grades for'
        )
        parser.add_argument(
            '--years',
            type=int,
            default=3,
            help='Number of past school years to create (default: 3)'
        )

    def handle(self, *args, **options):
        student_username = options['student']
        num_years = options['years']

        self.stdout.write(f'🎓 Creating demo grades for {num_years} school years for user: {student_username}')

        # Get or create the student
        try:
            user = User.objects.get(username=student_username)
            student = Student.objects.filter(
                primary_contact_email=user.email
            ).first()
            if not student:
                student = Student.objects.first()  # Fallback for demo
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'User {student_username} not found'))
            return

        if not student:
            self.stdout.write(self.style.ERROR('No student found'))
            return

        # Get or create a teacher user
        teacher, created = User.objects.get_or_create(
            username='demo_teacher',
            defaults={
                'first_name': 'Demo',
                'last_name': 'Teacher',
                'email': 'demo.teacher@school.edu'
            }
        )

        # Create school years
        current_year = timezone.now().year
        school_years = []
        
        for i in range(num_years, 0, -1):  # Create from oldest to newest
            year_start = current_year - i
            year_end = year_start + 1
            
            school_year, created = SchoolYear.objects.get_or_create(
                name=f'{year_start}-{year_end}',
                defaults={
                    'start_date': date(year_start, 8, 15),
                    'end_date': date(year_end, 6, 15),
                    'is_active': i == 1  # Only current year is active
                }
            )
            school_years.append(school_year)
            
            if created:
                self.stdout.write(f'📅 Created school year: {school_year.name}')

        # Create or get a department
        department, created = Department.objects.get_or_create(
            name='Demo Department',
            defaults={'description': 'Demo department for testing'}
        )
        
        # Create courses and assignments for each year
        course_templates = [
            ('Mathematics', 'MATH101', 4.0),
            ('English Literature', 'ENG201', 3.0),
            ('Chemistry', 'CHEM101', 4.0),
            ('World History', 'HIST101', 3.0),
            ('Physical Education', 'PE101', 1.0),
        ]

        for school_year in school_years:
            self.stdout.write(f'📚 Creating courses for {school_year.name}')
            
            year_gpa_variance = random.uniform(0.8, 1.2)  # Make some years better/worse
            
            for course_name, course_code, credit_hours in course_templates:
                # Create or get course
                course, created = Course.objects.get_or_create(
                    name=course_name,
                    course_code=course_code,
                    defaults={
                        'description': f'{course_name} - {school_year.name}',
                        'credit_hours': credit_hours,
                        'department': department
                    }
                )

                # Create course section
                section, created = CourseSection.objects.get_or_create(
                    course=course,
                    school_year=school_year,
                    teacher=teacher,
                    defaults={
                        'section_name': 'A',
                        'room': f'Room {random.randint(101, 299)}'
                    }
                )

                # Create enrollment
                enrollment, created = Enrollment.objects.get_or_create(
                    student=student,
                    section=section,
                    defaults={
                        'enrollment_date': school_year.start_date,
                        'is_active': True
                    }
                )

                # Create assignment categories
                categories = []
                for cat_name in ['Homework', 'Quiz', 'Test', 'Project']:
                    category, created = AssignmentCategory.objects.get_or_create(
                        name=cat_name,
                        defaults={'weight': 25.0}
                    )
                    categories.append(category)

                # Create assignments and grades
                assignment_templates = [
                    ('Homework 1', 'Homework', 10),
                    ('Homework 2', 'Homework', 10),
                    ('Quiz 1', 'Quiz', 20),
                    ('Quiz 2', 'Quiz', 20),
                    ('Midterm Test', 'Test', 100),
                    ('Final Project', 'Project', 50),
                    ('Final Test', 'Test', 100),
                ]

                for assign_name, assign_type, max_points in assignment_templates:
                    category = next(c for c in categories if c.name == assign_type)
                    
                    # Create assignment
                    due_date = school_year.start_date + timedelta(days=random.randint(30, 250))
                    assigned_date = due_date - timedelta(days=random.randint(7, 21))  # Assigned 1-3 weeks before due
                    
                    assignment, created = Assignment.objects.get_or_create(
                        name=assign_name,
                        section=section,
                        category=category,
                        defaults={
                            'description': f'{assign_name} for {course_name}',
                            'max_points': max_points,
                            'assigned_date': assigned_date,
                            'due_date': due_date,
                            'is_published': True
                        }
                    )

                    # Create grade with some randomness but trending based on year
                    if created:
                        # Generate grade percentage (make some years better/worse)
                        base_performance = random.uniform(75, 95)  # Base student performance
                        grade_percentage = base_performance * year_gpa_variance
                        grade_percentage = min(100, max(60, grade_percentage))  # Clamp between 60-100
                        
                        points_earned = (grade_percentage / 100) * max_points
                        
                        Grade.objects.create(
                            assignment=assignment,
                            enrollment=enrollment,
                            points_earned=points_earned,
                            percentage=grade_percentage,
                            is_late=random.choice([False, False, False, True]),  # 25% chance late
                            is_excused=False,
                            comments=f'Good work on {assign_name}!' if grade_percentage > 85 else 'Keep practicing!'
                        )

            self.stdout.write(
                self.style.SUCCESS(f'✅ Created courses and grades for {school_year.name}')
            )

        self.stdout.write(
            self.style.SUCCESS(
                f'🎉 Successfully created demo grades for {num_years} school years for student {student.first_name} {student.last_name}'
            )
        )
        self.stdout.write('💡 You can now test the semester filter on the grades page!')
