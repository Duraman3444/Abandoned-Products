from django.db import models
from django.contrib.auth.models import User
from students.models import Student, SchoolYear


class Department(models.Model):
    """Academic department"""

    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    head = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name="dept_head"
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ["name"]


class Course(models.Model):
    """Course definition"""

    name = models.CharField(max_length=100)
    course_code = models.CharField(max_length=20, unique=True)
    description = models.TextField(blank=True)
    department = models.ForeignKey(
        Department, on_delete=models.CASCADE, related_name="courses"
    )
    credit_hours = models.DecimalField(max_digits=3, decimal_places=1, default=1.0)
    prerequisites = models.ManyToManyField(
        "self", blank=True, symmetrical=False, related_name="prerequisite_for"
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.course_code}: {self.name}"

    class Meta:
        ordering = ["course_code"]


class CourseSection(models.Model):
    """Specific section of a course offered in a school year"""

    course = models.ForeignKey(
        Course, on_delete=models.CASCADE, related_name="sections"
    )
    school_year = models.ForeignKey(SchoolYear, on_delete=models.CASCADE)
    section_name = models.CharField(max_length=10, default="A")  # A, B, C, etc.
    teacher = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="taught_sections"
    )
    room = models.CharField(max_length=50, blank=True)
    max_students = models.PositiveIntegerField(default=25)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.course.course_code}-{self.section_name} ({self.school_year})"

    class Meta:
        ordering = ["course__course_code", "section_name"]
        unique_together = ["course", "school_year", "section_name"]


class Enrollment(models.Model):
    """Student enrollment in a course section"""

    student = models.ForeignKey(
        Student, on_delete=models.CASCADE, related_name="enrollments"
    )
    section = models.ForeignKey(
        CourseSection, on_delete=models.CASCADE, related_name="enrollments"
    )
    enrollment_date = models.DateField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    final_grade = models.CharField(max_length=2, blank=True)  # A+, A, A-, B+, etc.
    final_percentage = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True
    )

    def __str__(self):
        return f"{self.student} in {self.section}"

    class Meta:
        unique_together = ["student", "section"]
        ordering = ["section__course__course_code"]


class AssignmentCategory(models.Model):
    """Categories for assignments (Test, Quiz, Homework, Project, etc.)"""

    name = models.CharField(max_length=50)
    description = models.TextField(blank=True)
    default_weight = models.DecimalField(
        max_digits=5, decimal_places=2, default=1.0
    )  # Grading weight
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "Assignment Categories"


class Assignment(models.Model):
    """Assignment within a course section"""

    section = models.ForeignKey(
        CourseSection, on_delete=models.CASCADE, related_name="assignments"
    )
    category = models.ForeignKey(AssignmentCategory, on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    assigned_date = models.DateField()
    due_date = models.DateField()
    max_points = models.DecimalField(max_digits=6, decimal_places=2, default=100.0)
    weight = models.DecimalField(max_digits=5, decimal_places=2, default=1.0)
    is_published = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.section.course.course_code}: {self.name}"

    class Meta:
        ordering = ["-due_date", "name"]


class Grade(models.Model):
    """Individual grade for a student on an assignment"""

    enrollment = models.ForeignKey(
        Enrollment, on_delete=models.CASCADE, related_name="grades"
    )
    assignment = models.ForeignKey(
        Assignment, on_delete=models.CASCADE, related_name="grades"
    )
    points_earned = models.DecimalField(
        max_digits=6, decimal_places=2, null=True, blank=True
    )
    percentage = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True
    )
    letter_grade = models.CharField(max_length=2, blank=True)
    is_excused = models.BooleanField(default=False)
    is_late = models.BooleanField(default=False)
    comments = models.TextField(blank=True)
    graded_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True
    )
    graded_date = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        # Auto-calculate percentage if points are provided
        if self.points_earned is not None and self.assignment.max_points > 0:
            self.percentage = (self.points_earned / self.assignment.max_points) * 100
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.enrollment.student} - {self.assignment.name}: {self.points_earned or 'N/A'}"

    class Meta:
        unique_together = ["enrollment", "assignment"]
        ordering = ["-assignment__due_date"]


class Schedule(models.Model):
    """Class schedule/timetable"""

    DAYS_OF_WEEK = [
        ("MON", "Monday"),
        ("TUE", "Tuesday"),
        ("WED", "Wednesday"),
        ("THU", "Thursday"),
        ("FRI", "Friday"),
        ("SAT", "Saturday"),
        ("SUN", "Sunday"),
    ]

    section = models.ForeignKey(
        CourseSection, on_delete=models.CASCADE, related_name="schedules"
    )
    day_of_week = models.CharField(max_length=3, choices=DAYS_OF_WEEK)
    start_time = models.TimeField()
    end_time = models.TimeField()
    room = models.CharField(max_length=50, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.section} - {self.get_day_of_week_display()} {self.start_time}-{self.end_time}"

    class Meta:
        ordering = ["day_of_week", "start_time"]


class Attendance(models.Model):
    """Student attendance records"""

    ATTENDANCE_CHOICES = [
        ("P", "Present"),
        ("A", "Absent"),
        ("T", "Tardy"),
        ("E", "Excused"),
    ]

    enrollment = models.ForeignKey(
        Enrollment, on_delete=models.CASCADE, related_name="attendance_records"
    )
    date = models.DateField()
    status = models.CharField(max_length=1, choices=ATTENDANCE_CHOICES, default="P")
    notes = models.TextField(blank=True)
    recorded_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True
    )
    recorded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.enrollment.student} - {self.date}: {self.get_status_display()}"

    class Meta:
        unique_together = ["enrollment", "date"]
        ordering = ["-date"]


class Announcement(models.Model):
    """School announcements"""

    AUDIENCE_CHOICES = [
        ("ALL", "All Users"),
        ("STUDENTS", "Students Only"),
        ("PARENTS", "Parents Only"),
        ("TEACHERS", "Teachers Only"),
    ]

    title = models.CharField(max_length=200)
    content = models.TextField()
    audience = models.CharField(max_length=10, choices=AUDIENCE_CHOICES, default="ALL")
    is_published = models.BooleanField(default=False)
    is_urgent = models.BooleanField(default=False)
    publish_date = models.DateTimeField()
    expire_date = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

    class Meta:
        ordering = ["-publish_date"]


class Message(models.Model):
    """Messages between users (teacher-parent, admin-parent, etc.)"""

    sender = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="sent_messages"
    )
    recipient = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="received_messages"
    )
    subject = models.CharField(max_length=200)
    content = models.TextField()
    is_read = models.BooleanField(default=False)
    is_urgent = models.BooleanField(default=False)
    sent_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"From {self.sender} to {self.recipient}: {self.subject}"

    class Meta:
        ordering = ["-sent_at"]
