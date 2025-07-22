"""
Tests for the grades page semester filtering functionality
"""

from django.test import TestCase, Client
from django.contrib.auth.models import User, Group
from django.urls import reverse
from datetime import date

from students.models import Student, SchoolYear
from academics.models import Course, CourseSection, Enrollment, Assignment, Grade, AssignmentCategory


class GradesFilterTest(TestCase):
    def setUp(self):
        """Set up test data"""
        # Create student group
        student_group, _ = Group.objects.get_or_create(name='Students')
        
        # Create test user and student
        self.user = User.objects.create_user(
            username='test_student',
            email='test@example.com',
            password='testpass123'
        )
        self.user.groups.add(student_group)
        
        self.student = Student.objects.create(
            first_name='Test',
            last_name='Student',
            primary_contact_email='test@example.com',
            date_of_birth=date(2005, 1, 1),
            enrollment_date=date(2020, 8, 15)
        )
        
        # Create teacher user
        self.teacher = User.objects.create_user(
            username='teacher',
            email='teacher@example.com',
            first_name='Test',
            last_name='Teacher'
        )
        
        # Create two school years
        self.current_year = SchoolYear.objects.create(
            name='2024-2025',
            start_date=date(2024, 8, 15),
            end_date=date(2025, 6, 15),
            is_active=True
        )
        
        self.past_year = SchoolYear.objects.create(
            name='2023-2024',
            start_date=date(2023, 8, 15),
            end_date=date(2024, 6, 15),
            is_active=False
        )
        
        # Create courses and enrollments for both years
        self.setup_courses_and_grades()
        
        self.client = Client()

    def setup_courses_and_grades(self):
        """Create courses, enrollments, and grades for both years"""
        # Create course
        course = Course.objects.create(
            name='Mathematics',
            code='MATH101',
            description='Basic Mathematics',
            credit_hours=4.0
        )
        
        # Create assignment category
        category = AssignmentCategory.objects.create(
            name='Test',
            weight=100.0
        )
        
        # Setup for current year
        current_section = CourseSection.objects.create(
            course=course,
            school_year=self.current_year,
            teacher=self.teacher,
            section_name='A',
            room='Room 101'
        )
        
        current_enrollment = Enrollment.objects.create(
            student=self.student,
            section=current_section,
            enrollment_date=self.current_year.start_date,
            is_active=True
        )
        
        current_assignment = Assignment.objects.create(
            name='Current Year Test',
            section=current_section,
            category=category,
            description='Test for current year',
            max_points=100,
            due_date=date(2024, 10, 15),
            is_published=True
        )
        
        Grade.objects.create(
            assignment=current_assignment,
            enrollment=current_enrollment,
            points_earned=90,
            percentage=90.0,
            date_turned_in=date(2024, 10, 14)
        )
        
        # Setup for past year
        past_section = CourseSection.objects.create(
            course=course,
            school_year=self.past_year,
            teacher=self.teacher,
            section_name='A',
            room='Room 102'
        )
        
        past_enrollment = Enrollment.objects.create(
            student=self.student,
            section=past_section,
            enrollment_date=self.past_year.start_date,
            is_active=True
        )
        
        past_assignment = Assignment.objects.create(
            name='Past Year Test',
            section=past_section,
            category=category,
            description='Test for past year',
            max_points=100,
            due_date=date(2023, 10, 15),
            is_published=True
        )
        
        Grade.objects.create(
            assignment=past_assignment,
            enrollment=past_enrollment,
            points_earned=85,
            percentage=85.0,
            date_turned_in=date(2023, 10, 14)
        )

    def test_default_shows_current_year(self):
        """Test that the grades page shows current year by default"""
        self.client.force_login(self.user)
        response = self.client.get(reverse('student_portal:grades'))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Current Year Test')
        self.assertNotContains(response, 'Past Year Test')
        self.assertContains(response, '2024-2025')

    def test_semester_filter_past_year(self):
        """Test that filtering by past year works correctly"""
        self.client.force_login(self.user)
        url = reverse('student_portal:grades') + f'?year={self.past_year.id}'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Past Year Test')
        self.assertNotContains(response, 'Current Year Test')
        self.assertContains(response, '2023-2024')

    def test_invalid_year_param(self):
        """Test that invalid year parameter defaults to current year"""
        self.client.force_login(self.user)
        
        # Test with non-existent year ID
        url = reverse('student_portal:grades') + '?year=9999'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)  # Should 404 with get_object_or_404
        
        # Test with non-numeric year
        url = reverse('student_portal:grades') + '?year=invalid'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Current Year Test')

    def test_cumulative_gpa_calculation(self):
        """Test that cumulative GPA includes all years"""
        self.client.force_login(self.user)
        response = self.client.get(reverse('student_portal:grades'))
        
        self.assertEqual(response.status_code, 200)
        
        # Check that both semester and cumulative GPA are present
        self.assertContains(response, 'Semester GPA')
        self.assertContains(response, 'Cumulative GPA')
        
        # Cumulative should be average of 90% and 85% = 87.5%
        context = response.context
        self.assertAlmostEqual(float(context['cumulative_gpa']), 87.5, places=1)
        
        # Semester GPA should be 90% (current year only)
        self.assertAlmostEqual(float(context['semester_gpa']), 90.0, places=1)

    def test_year_dropdown_populated(self):
        """Test that all years appear in the dropdown"""
        self.client.force_login(self.user)
        response = self.client.get(reverse('student_portal:grades'))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '2024-2025')
        self.assertContains(response, '2023-2024')
        
        # Check that the correct year is selected
        context = response.context
        self.assertEqual(context['selected_year'], self.current_year)
        self.assertIn(self.current_year, context['all_years'])
        self.assertIn(self.past_year, context['all_years'])

    def test_unauthenticated_access(self):
        """Test that unauthenticated users are redirected"""
        response = self.client.get(reverse('student_portal:grades'))
        self.assertRedirects(response, '/auth/login/?next=/student/grades/')

    def test_non_student_access(self):
        """Test that non-student users can't access the page"""
        # Create a user without student group
        non_student = User.objects.create_user(
            username='non_student',
            email='non@example.com',
            password='testpass123'
        )
        
        self.client.force_login(non_student)
        response = self.client.get(reverse('student_portal:grades'))
        # Should redirect or show error due to role_required decorator
        self.assertNotEqual(response.status_code, 200)
