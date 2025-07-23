"""
Detail views for various entities in the system.
These views provide individual detail pages for students, courses, teachers, etc.
"""

from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import Http404
from students.models import Student
from academics.models import Course, CourseSection, Assignment
from django.contrib.auth.models import User


@login_required
def student_detail_view(request, student_id):
    """Display detailed information about a specific student."""
    student = get_object_or_404(Student, id=student_id)
    
    # Get student's enrollments and grades
    enrollments = student.enrollments.all().select_related('section__course')
    
    context = {
        'student': student,
        'enrollments': enrollments,
        'page_title': f'Student: {student.name}',
    }
    
    return render(request, 'core/student_detail.html', context)


@login_required
def course_detail_view(request, course_id):
    """Display detailed information about a specific course."""
    course = get_object_or_404(Course, id=course_id)
    
    # Get course sections
    sections = course.sections.all()
    
    context = {
        'course': course,
        'sections': sections,
        'page_title': f'Course: {course.name}',
    }
    
    return render(request, 'core/course_detail.html', context)


@login_required
def teacher_detail_view(request, teacher_id):
    """Display detailed information about a specific teacher."""
    teacher = get_object_or_404(User, id=teacher_id, is_staff=True)
    
    # Get courses taught by this teacher
    sections = teacher.taught_sections.all().select_related('course')
    
    context = {
        'teacher': teacher,
        'sections': sections,
        'page_title': f'Teacher: {teacher.get_full_name() or teacher.username}',
    }
    
    return render(request, 'core/teacher_detail.html', context)


@login_required
def assignment_detail_view(request, assignment_id):
    """Display detailed information about a specific assignment."""
    assignment = get_object_or_404(Assignment, id=assignment_id)
    
    context = {
        'assignment': assignment,
        'page_title': f'Assignment: {assignment.name}',
    }
    
    return render(request, 'core/assignment_detail.html', context)
