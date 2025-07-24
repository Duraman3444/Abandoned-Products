from django.db import models
from django.contrib.auth.models import User
from django.db.models import Avg, Sum, Q
from decimal import Decimal
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

    def calculate_grade(self):
        """Calculate weighted grade based on assignment categories"""
        grades = self.grades.filter(
            points_earned__isnull=False,
            is_excused=False
        ).select_related('assignment__category')
        
        if not grades.exists():
            return None
            
        # Group grades by category
        category_totals = {}
        for grade in grades:
            category = grade.assignment.category
            if category not in category_totals:
                category_totals[category] = {
                    'earned': Decimal('0'),
                    'possible': Decimal('0'),
                    'weight': category.default_weight
                }
            
            category_totals[category]['earned'] += grade.points_earned * grade.assignment.weight
            category_totals[category]['possible'] += grade.assignment.max_points * grade.assignment.weight
        
        # Calculate weighted average
        total_weighted_score = Decimal('0')
        total_weight = Decimal('0')
        
        for category, totals in category_totals.items():
            if totals['possible'] > 0:
                category_percentage = (totals['earned'] / totals['possible']) * 100
                total_weighted_score += category_percentage * totals['weight']
                total_weight += totals['weight']
        
        if total_weight > 0:
            return total_weighted_score / total_weight
        return None

    def get_letter_grade(self, percentage=None):
        """Convert percentage to letter grade"""
        if percentage is None:
            percentage = self.calculate_grade()
        
        if percentage is None:
            return ""
            
        if percentage >= 97: return "A+"
        elif percentage >= 93: return "A"
        elif percentage >= 90: return "A-"
        elif percentage >= 87: return "B+"
        elif percentage >= 83: return "B"
        elif percentage >= 80: return "B-"
        elif percentage >= 77: return "C+"
        elif percentage >= 73: return "C"
        elif percentage >= 70: return "C-"
        elif percentage >= 67: return "D+"
        elif percentage >= 63: return "D"
        elif percentage >= 60: return "D-"
        else: return "F"

    def update_final_grade(self):
        """Update the final grade based on current assignments"""
        calculated_percentage = self.calculate_grade()
        if calculated_percentage is not None:
            self.final_percentage = calculated_percentage
            self.final_grade = self.get_letter_grade(calculated_percentage)
            self.save()

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


class CurriculumStandard(models.Model):
    """Curriculum standards for alignment"""
    
    code = models.CharField(max_length=50, unique=True)
    title = models.CharField(max_length=300)
    description = models.TextField()
    subject_area = models.CharField(max_length=100)
    grade_level = models.CharField(max_length=50)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.code}: {self.title}"
    
    class Meta:
        ordering = ['subject_area', 'grade_level', 'code']


class AssignmentTemplate(models.Model):
    """Reusable assignment templates"""
    
    name = models.CharField(max_length=200)
    description = models.TextField()
    category = models.ForeignKey(AssignmentCategory, on_delete=models.CASCADE)
    max_points = models.DecimalField(max_digits=6, decimal_places=2, default=100.0)
    weight = models.DecimalField(max_digits=5, decimal_places=2, default=1.0)
    instructions = models.TextField(blank=True)
    estimated_duration = models.PositiveIntegerField(null=True, blank=True, help_text="Duration in minutes")
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    is_public = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        ordering = ['name']


class LessonPlan(models.Model):
    """Lesson plans for curriculum integration"""
    
    LESSON_TYPES = [
        ('lecture', 'Lecture'),
        ('discussion', 'Discussion'),
        ('lab', 'Laboratory'),
        ('project', 'Project'),
        ('assessment', 'Assessment'),
        ('review', 'Review'),
        ('presentation', 'Presentation'),
    ]
    
    title = models.CharField(max_length=200)
    section = models.ForeignKey(CourseSection, on_delete=models.CASCADE, related_name="lesson_plans")
    lesson_type = models.CharField(max_length=20, choices=LESSON_TYPES, default='lecture')
    objectives = models.TextField(help_text="Learning objectives for this lesson")
    content = models.TextField(help_text="Lesson content and activities")
    materials = models.TextField(blank=True, help_text="Required materials and resources")
    duration = models.PositiveIntegerField(help_text="Duration in minutes")
    date = models.DateField()
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.section}: {self.title}"
    
    class Meta:
        ordering = ['date', 'title']


class Assignment(models.Model):
    """Assignment within a course section"""

    section = models.ForeignKey(
        CourseSection, on_delete=models.CASCADE, related_name="assignments"
    )
    category = models.ForeignKey(AssignmentCategory, on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    instructions = models.TextField(blank=True, help_text="Detailed instructions for students")
    assigned_date = models.DateField()
    due_date = models.DateField()
    due_time = models.TimeField(null=True, blank=True, help_text="Optional due time")
    max_points = models.DecimalField(max_digits=6, decimal_places=2, default=100.0)
    weight = models.DecimalField(max_digits=5, decimal_places=2, default=1.0)
    is_published = models.BooleanField(default=False)
    allow_late_submission = models.BooleanField(default=True)
    late_penalty = models.DecimalField(max_digits=5, decimal_places=2, default=0.0, 
                                     help_text="Penalty percentage per day late")
    estimated_duration = models.PositiveIntegerField(null=True, blank=True, 
                                                   help_text="Estimated time in minutes")
    # Curriculum alignment
    standards = models.ManyToManyField(CurriculumStandard, blank=True)
    lesson_plan = models.ForeignKey(LessonPlan, on_delete=models.SET_NULL, 
                                   null=True, blank=True, related_name="assignments")
    # Template reference
    template = models.ForeignKey(AssignmentTemplate, on_delete=models.SET_NULL, 
                               null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def is_overdue(self):
        """Check if assignment is past due date"""
        from datetime import datetime, time
        from django.utils import timezone
        
        if self.due_time:
            due_datetime = timezone.make_aware(
                datetime.combine(self.due_date, self.due_time)
            )
        else:
            due_datetime = timezone.make_aware(
                datetime.combine(self.due_date, time(23, 59, 59))
            )
        
        return timezone.now() > due_datetime

    def get_completion_rate(self):
        """Calculate assignment completion rate"""
        total_students = self.section.enrollments.filter(is_active=True).count()
        if total_students == 0:
            return 0.0
        
        completed_submissions = self.grades.filter(
            points_earned__isnull=False
        ).count()
        
        return (completed_submissions / total_students) * 100

    def get_average_score(self):
        """Calculate average score for this assignment"""
        grades = self.grades.filter(
            points_earned__isnull=False,
            is_excused=False
        )
        
        if not grades.exists():
            return None
            
        total_points = sum(grade.points_earned for grade in grades)
        return total_points / grades.count()

    def get_grade_distribution(self):
        """Get grade distribution for analytics"""
        grades = self.grades.filter(
            points_earned__isnull=False,
            is_excused=False
        )
        
        if not grades.exists():
            return {'A': 0, 'B': 0, 'C': 0, 'D': 0, 'F': 0}
        
        distribution = {'A': 0, 'B': 0, 'C': 0, 'D': 0, 'F': 0}
        
        for grade in grades:
            percentage = (grade.points_earned / self.max_points) * 100
            if percentage >= 90:
                distribution['A'] += 1
            elif percentage >= 80:
                distribution['B'] += 1
            elif percentage >= 70:
                distribution['C'] += 1
            elif percentage >= 60:
                distribution['D'] += 1
            else:
                distribution['F'] += 1
        
        return distribution

    def __str__(self):
        return f"{self.section.course.course_code}: {self.name}"

    class Meta:
        ordering = ["-due_date", "name"]


class AssignmentAttachment(models.Model):
    """File attachments for assignments"""
    
    assignment = models.ForeignKey(
        Assignment, on_delete=models.CASCADE, related_name="attachments"
    )
    file = models.FileField(upload_to='assignments/%Y/%m/')
    original_filename = models.CharField(max_length=255)
    file_size = models.PositiveIntegerField()
    content_type = models.CharField(max_length=100)
    description = models.CharField(max_length=200, blank=True)
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.assignment.name}: {self.original_filename}"
    
    class Meta:
        ordering = ['uploaded_at']


class StudentSubmission(models.Model):
    """Student submissions for assignments"""
    
    assignment = models.ForeignKey(
        Assignment, on_delete=models.CASCADE, related_name="submissions"
    )
    student = models.ForeignKey(
        'students.Student', on_delete=models.CASCADE, related_name="submissions"
    )
    content = models.TextField(blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)
    is_late = models.BooleanField(default=False)
    
    def save(self, *args, **kwargs):
        # Check if submission is late
        if not self.pk:  # Only on creation
            self.is_late = self.assignment.is_overdue
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.student} - {self.assignment.name}"
    
    class Meta:
        unique_together = ['assignment', 'student']
        ordering = ['-submitted_at']


class SubmissionAttachment(models.Model):
    """File attachments for student submissions"""
    
    submission = models.ForeignKey(
        StudentSubmission, on_delete=models.CASCADE, related_name="attachments"
    )
    file = models.FileField(upload_to='submissions/%Y/%m/')
    original_filename = models.CharField(max_length=255)
    file_size = models.PositiveIntegerField()
    content_type = models.CharField(max_length=100)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.submission}: {self.original_filename}"
    
    class Meta:
        ordering = ['uploaded_at']


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
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        # Create audit trail entry before saving
        if self.pk:
            old_grade = Grade.objects.get(pk=self.pk)
            if (old_grade.points_earned != self.points_earned or 
                old_grade.letter_grade != self.letter_grade):
                GradeHistory.objects.create(
                    grade=self,
                    old_points_earned=old_grade.points_earned,
                    old_percentage=old_grade.percentage,
                    old_letter_grade=old_grade.letter_grade,
                    new_points_earned=self.points_earned,
                    new_percentage=self.percentage,
                    new_letter_grade=self.letter_grade,
                    changed_by=self.graded_by,
                )
        
        # Auto-calculate percentage if points are provided
        if self.points_earned is not None and self.assignment.max_points > 0:
            self.percentage = (self.points_earned / self.assignment.max_points) * 100
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.enrollment.student} - {self.assignment.name}: {self.points_earned or 'N/A'}"

    class Meta:
        unique_together = ["enrollment", "assignment"]
        ordering = ["-assignment__due_date"]


class GradeHistory(models.Model):
    """Audit trail for grade changes"""
    
    grade = models.ForeignKey(
        Grade, on_delete=models.CASCADE, related_name="history"
    )
    old_points_earned = models.DecimalField(
        max_digits=6, decimal_places=2, null=True, blank=True
    )
    old_percentage = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True
    )
    old_letter_grade = models.CharField(max_length=2, blank=True)
    new_points_earned = models.DecimalField(
        max_digits=6, decimal_places=2, null=True, blank=True
    )
    new_percentage = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True
    )
    new_letter_grade = models.CharField(max_length=2, blank=True)
    changed_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True
    )
    changed_at = models.DateTimeField(auto_now_add=True)
    reason = models.TextField(blank=True)

    def __str__(self):
        return f"Grade change for {self.grade} at {self.changed_at}"

    class Meta:
        ordering = ["-changed_at"]
        verbose_name_plural = "Grade Histories"


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


class AbsenceReason(models.Model):
    """Reasons for student absences"""
    
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    is_excused = models.BooleanField(default=False)
    requires_documentation = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        ordering = ['name']


class EarlyDismissalRequest(models.Model):
    """Early dismissal requests from parents"""
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('denied', 'Denied'),
        ('completed', 'Completed'),
    ]
    
    student = models.ForeignKey(
        'students.Student', on_delete=models.CASCADE, related_name='dismissal_requests'
    )
    requested_by = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='dismissal_requests'
    )
    request_date = models.DateField()
    dismissal_time = models.TimeField()
    reason = models.TextField()
    pickup_person = models.CharField(max_length=100, help_text="Name of person picking up student")
    contact_phone = models.CharField(max_length=20)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # School office fields
    processed_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name='processed_dismissals'
    )
    processed_at = models.DateTimeField(null=True, blank=True)
    school_notes = models.TextField(blank=True)
    actual_dismissal_time = models.TimeField(null=True, blank=True)
    
    # Recurring request fields
    is_recurring = models.BooleanField(default=False)
    recurring_days = models.CharField(
        max_length=20, blank=True, 
        help_text="Comma-separated days: MON,TUE,WED,THU,FRI"
    )
    recurring_end_date = models.DateField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.student.display_name} - {self.request_date} at {self.dismissal_time}"
    
    @property
    def is_approved(self):
        return self.status == 'approved'
    
    @property 
    def is_pending(self):
        return self.status == 'pending'
        
    @property
    def is_overdue(self):
        from django.utils import timezone
        if self.status == 'pending':
            return timezone.now().date() > self.request_date
        return False
    
    class Meta:
        ordering = ['-request_date', '-dismissal_time']


class AttendanceNotification(models.Model):
    """Notifications sent to parents about attendance"""
    
    NOTIFICATION_TYPES = [
        ('absence', 'Absence Alert'),
        ('tardiness', 'Tardiness Alert'),
        ('pattern', 'Pattern Alert'),
        ('early_dismissal', 'Early Dismissal Confirmation'),
    ]
    
    DELIVERY_METHODS = [
        ('email', 'Email'),
        ('sms', 'SMS'),
        ('both', 'Email & SMS'),
    ]
    
    student = models.ForeignKey(
        'students.Student', on_delete=models.CASCADE, related_name='attendance_notifications'
    )
    recipient = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='received_notifications'
    )
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    message = models.TextField()
    delivery_method = models.CharField(max_length=10, choices=DELIVERY_METHODS, default='email')
    
    # Delivery tracking
    is_sent = models.BooleanField(default=False)
    sent_at = models.DateTimeField(null=True, blank=True)
    email_sent = models.BooleanField(default=False)
    sms_sent = models.BooleanField(default=False)
    
    # Reference fields
    attendance_record = models.ForeignKey(
        'Attendance', on_delete=models.CASCADE, null=True, blank=True, 
        related_name='notifications'
    )
    dismissal_request = models.ForeignKey(
        EarlyDismissalRequest, on_delete=models.CASCADE, null=True, blank=True,
        related_name='notifications'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.get_notification_type_display()} for {self.student.display_name} to {self.recipient.get_full_name()}"
    
    @classmethod
    def create_absence_notification(cls, attendance_record):
        """Create absence notification for parents"""
        student = attendance_record.enrollment.student
        
        for parent in student.family_access_users.all():
            message = f"{student.display_name} was marked absent on {attendance_record.date.strftime('%B %d, %Y')}."
            if attendance_record.absence_reason:
                message += f" Reason: {attendance_record.absence_reason.name}"
            
            notification = cls.objects.create(
                student=student,
                recipient=parent,
                notification_type='absence',
                message=message,
                attendance_record=attendance_record,
                delivery_method='email'  # Default to email for now
            )
            
            # Mark the attendance record as parent notified
            attendance_record.parent_notified = True
            attendance_record.parent_notified_at = timezone.now()
            attendance_record.save()
            
            return notification
    
    @classmethod
    def create_tardiness_notification(cls, attendance_record):
        """Create tardiness notification for parents"""
        student = attendance_record.enrollment.student
        
        for parent in student.family_access_users.all():
            message = f"{student.display_name} was marked tardy on {attendance_record.date.strftime('%B %d, %Y')}."
            if attendance_record.minutes_late:
                message += f" They were {attendance_record.minutes_late} minutes late."
            
            notification = cls.objects.create(
                student=student,
                recipient=parent,
                notification_type='tardiness',
                message=message,
                attendance_record=attendance_record,
                delivery_method='email'
            )
            
            return notification
    
    class Meta:
        ordering = ['-created_at']


class SchoolCalendarEvent(models.Model):
    """School calendar events like holidays, early dismissal days, etc."""
    
    EVENT_TYPES = [
        ('holiday', 'Holiday'),
        ('early_dismissal', 'Early Dismissal'),
        ('no_school', 'No School'),
        ('half_day', 'Half Day'),
        ('testing', 'Testing Day'),
        ('conference', 'Parent-Teacher Conference'),
        ('event', 'School Event'),
        ('break', 'School Break'),
    ]
    
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    event_type = models.CharField(max_length=20, choices=EVENT_TYPES)
    start_date = models.DateField()
    end_date = models.DateField()
    start_time = models.TimeField(null=True, blank=True, help_text="For events with specific times")
    end_time = models.TimeField(null=True, blank=True, help_text="For events with specific times")
    
    # For early dismissal days
    dismissal_time = models.TimeField(null=True, blank=True, help_text="Early dismissal time")
    
    # Display options
    is_public = models.BooleanField(default=True, help_text="Show to parents in portal")
    color = models.CharField(max_length=7, default='#007bff', help_text="Hex color code for calendar display")
    
    # Affected groups
    affects_all_students = models.BooleanField(default=True)
    specific_grades = models.CharField(
        max_length=100, blank=True, 
        help_text="Comma-separated grade levels if not affecting all (e.g., K,1,2)"
    )
    
    school_year = models.ForeignKey(
        'students.SchoolYear', on_delete=models.CASCADE, related_name='calendar_events'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True
    )
    
    def __str__(self):
        if self.start_date == self.end_date:
            return f"{self.title} - {self.start_date}"
        return f"{self.title} - {self.start_date} to {self.end_date}"
    
    @property
    def is_single_day(self):
        """Check if event is a single day event"""
        return self.start_date == self.end_date
    
    @property
    def is_ongoing(self):
        """Check if event is currently ongoing"""
        from django.utils import timezone
        today = timezone.now().date()
        return self.start_date <= today <= self.end_date
    
    @property
    def is_upcoming(self):
        """Check if event is upcoming"""
        from django.utils import timezone
        today = timezone.now().date()
        return self.start_date > today
    
    @property
    def duration_days(self):
        """Get the duration of the event in days"""
        return (self.end_date - self.start_date).days + 1
    
    def affects_student(self, student):
        """Check if this event affects a specific student"""
        if self.affects_all_students:
            return True
        
        if self.specific_grades:
            student_grade = student.grade_level.name if student.grade_level else ''
            affected_grades = [grade.strip() for grade in self.specific_grades.split(',')]
            return student_grade in affected_grades
        
        return False
    
    @classmethod
    def get_events_for_month(cls, year, month, school_year=None):
        """Get all events for a specific month"""
        from datetime import date
        from calendar import monthrange
        
        if not school_year:
            from students.models import SchoolYear
            school_year = SchoolYear.objects.filter(is_active=True).first()
        
        start_date = date(year, month, 1)
        end_date = date(year, month, monthrange(year, month)[1])
        
        return cls.objects.filter(
            school_year=school_year,
            is_public=True,
            start_date__lte=end_date,
            end_date__gte=start_date
        ).order_by('start_date')
    
    @classmethod
    def get_upcoming_events(cls, days=30, school_year=None):
        """Get upcoming events within specified days"""
        from datetime import date, timedelta
        from students.models import SchoolYear
        
        if not school_year:
            school_year = SchoolYear.objects.filter(is_active=True).first()
        
        today = date.today()
        end_date = today + timedelta(days=days)
        
        return cls.objects.filter(
            school_year=school_year,
            is_public=True,
            start_date__gte=today,
            start_date__lte=end_date
        ).order_by('start_date')
    
    class Meta:
        ordering = ['start_date', 'start_time']
        verbose_name = "School Calendar Event"
        verbose_name_plural = "School Calendar Events"


class Attendance(models.Model):
    """Student attendance records"""

    ATTENDANCE_CHOICES = [
        ("P", "Present"),
        ("A", "Absent"),
        ("T", "Tardy"),
        ("E", "Excused Absent"),
        ("L", "Late Excused"),
    ]

    enrollment = models.ForeignKey(
        Enrollment, on_delete=models.CASCADE, related_name="attendance_records"
    )
    date = models.DateField()
    status = models.CharField(max_length=1, choices=ATTENDANCE_CHOICES, default="P")
    absence_reason = models.ForeignKey(
        AbsenceReason, on_delete=models.SET_NULL, null=True, blank=True
    )
    minutes_late = models.PositiveIntegerField(null=True, blank=True)
    parent_notified = models.BooleanField(default=False)
    parent_notified_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)
    recorded_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True
    )
    recorded_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property 
    def is_absent(self):
        """Check if student was absent (any type of absence)"""
        return self.status in ['A', 'E']
    
    @property
    def is_tardy(self):
        """Check if student was tardy (any type of tardiness)"""
        return self.status in ['T', 'L']
        
    @classmethod
    def get_attendance_summary(cls, enrollment, start_date=None, end_date=None):
        """Get attendance summary for a student enrollment"""
        queryset = cls.objects.filter(enrollment=enrollment)
        
        if start_date:
            queryset = queryset.filter(date__gte=start_date)
        if end_date:
            queryset = queryset.filter(date__lte=end_date)
            
        total_days = queryset.count()
        if total_days == 0:
            return {
                'total_days': 0,
                'present_days': 0,
                'absent_days': 0,
                'tardy_days': 0,
                'excused_days': 0,
                'attendance_rate': 0.0
            }
        
        present_days = queryset.filter(status='P').count()
        absent_days = queryset.filter(status__in=['A', 'E']).count()
        tardy_days = queryset.filter(status__in=['T', 'L']).count()
        excused_days = queryset.filter(status__in=['E', 'L']).count()
        
        attendance_rate = (present_days / total_days) * 100 if total_days > 0 else 0
        
        return {
            'total_days': total_days,
            'present_days': present_days,
            'absent_days': absent_days,
            'tardy_days': tardy_days,
            'excused_days': excused_days,
            'attendance_rate': round(attendance_rate, 2)
        }
    
    @classmethod
    def get_attendance_patterns(cls, enrollment, days=30):
        """Analyze attendance patterns for a student"""
        from datetime import date, timedelta
        from django.db.models import Count
        
        end_date = date.today()
        start_date = end_date - timedelta(days=days)
        
        records = cls.objects.filter(
            enrollment=enrollment,
            date__gte=start_date,
            date__lte=end_date
        ).order_by('-date')
        
        # Pattern analysis
        patterns = {
            'consecutive_absences': 0,
            'frequent_tardiness': False,
            'monday_pattern': False,
            'friday_pattern': False,
            'recent_trend': 'stable'  # improving, declining, stable
        }
        
        if records.exists():
            # Check for consecutive absences
            consecutive_count = 0
            max_consecutive = 0
            
            for record in records:
                if record.is_absent:
                    consecutive_count += 1
                    max_consecutive = max(max_consecutive, consecutive_count)
                else:
                    consecutive_count = 0
            
            patterns['consecutive_absences'] = max_consecutive
            
            # Check for frequent tardiness (more than 20% of days)
            total_records = records.count()
            tardy_records = records.filter(status__in=['T', 'L']).count()
            patterns['frequent_tardiness'] = (tardy_records / total_records) > 0.2 if total_records > 0 else False
            
            # Check for Monday/Friday patterns
            monday_absences = records.filter(date__week_day=2, status__in=['A', 'E']).count()  # Monday is 2
            friday_absences = records.filter(date__week_day=6, status__in=['A', 'E']).count()  # Friday is 6
            total_absences = records.filter(status__in=['A', 'E']).count()
            
            if total_absences > 0:
                patterns['monday_pattern'] = (monday_absences / total_absences) > 0.3
                patterns['friday_pattern'] = (friday_absences / total_absences) > 0.3
        
        return patterns

    def __str__(self):
        return f"{self.enrollment.student} - {self.date}: {self.get_status_display()}"

    class Meta:
        unique_together = ["enrollment", "date"]
        ordering = ["-date"]


class Announcement(models.Model):
    """School announcements with enhanced targeting"""

    AUDIENCE_CHOICES = [
        ("ALL", "All Users"),
        ("STUDENTS", "Students Only"),
        ("PARENTS", "Parents Only"),
        ("TEACHERS", "Teachers Only"),
        ("ADMIN", "Administration Only"),
        ("STAFF", "All Staff"),
        ("SPECIFIC_CLASSES", "Specific Classes"),
        ("SPECIFIC_GRADES", "Specific Grades"),
    ]

    PRIORITY_CHOICES = [
        ("LOW", "Low Priority"),
        ("NORMAL", "Normal Priority"),
        ("HIGH", "High Priority"),
        ("URGENT", "Urgent - Immediate Attention"),
    ]

    title = models.CharField(max_length=200)
    content = models.TextField()
    audience = models.CharField(max_length=20, choices=AUDIENCE_CHOICES, default="ALL")
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default="NORMAL")
    is_published = models.BooleanField(default=False)
    is_urgent = models.BooleanField(default=False)  # Kept for backward compatibility
    publish_date = models.DateTimeField()
    expire_date = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Enhanced targeting fields
    target_classes = models.ManyToManyField(
        'Course', 
        blank=True, 
        help_text="Select specific classes (used when audience is 'Specific Classes')"
    )
    target_grades = models.CharField(
        max_length=50, 
        blank=True,
        help_text="Comma-separated grade levels (e.g., '9,10,11' for grades 9-11)"
    )
    
    # Email and SMS notification options
    send_email_notification = models.BooleanField(
        default=False,
        help_text="Send email notifications to targeted audience"
    )
    send_sms_notification = models.BooleanField(
        default=False,
        help_text="Send SMS notifications to targeted audience"
    )
    send_push_notification = models.BooleanField(
        default=True,
        help_text="Send push notifications to targeted audience"
    )
    
    # Tracking fields
    email_sent_at = models.DateTimeField(null=True, blank=True)
    sms_sent_at = models.DateTimeField(null=True, blank=True)
    push_sent_at = models.DateTimeField(null=True, blank=True)

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
    
    # Threading support
    thread_id = models.CharField(
        max_length=50, 
        blank=True,
        help_text="Messages with same thread_id are part of the same conversation"
    )
    parent_message = models.ForeignKey(
        'self', 
        null=True, 
        blank=True,
        on_delete=models.CASCADE,
        related_name='replies',
        help_text="The message this is replying to"
    )
    
    # Additional metadata
    student_context = models.ForeignKey(
        'students.Student',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        help_text="Student this message is about (optional)"
    )

    def __str__(self):
        return f"From {self.sender} to {self.recipient}: {self.subject}"

    def mark_as_read(self):
        """Mark message as read and set read timestamp"""
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save()
    
    def get_thread_messages(self):
        """Get all messages in this thread"""
        if self.thread_id:
            return Message.objects.filter(thread_id=self.thread_id).order_by('sent_at')
        return Message.objects.filter(id=self.id)
    
    def generate_thread_id(self):
        """Generate a unique thread ID for this message"""
        import uuid
        return f"thread_{uuid.uuid4().hex[:8]}"
    
    def save(self, *args, **kwargs):
        # Generate thread_id if not provided and not a reply
        if not self.thread_id and not self.parent_message:
            self.thread_id = self.generate_thread_id()
        elif self.parent_message and not self.thread_id:
            # Use parent's thread_id for replies
            self.thread_id = self.parent_message.thread_id
        
        super().save(*args, **kwargs)

    class Meta:
        ordering = ["-sent_at"]


class MessageAttachment(models.Model):
    """File attachments for messages"""
    
    message = models.ForeignKey(
        Message, on_delete=models.CASCADE, related_name='attachments'
    )
    file = models.FileField(
        upload_to='message_attachments/%Y/%m/',
        help_text="Supported files: PDF, DOC, DOCX, JPG, PNG, TXT (max 10MB)"
    )
    original_filename = models.CharField(max_length=255)
    file_size = models.PositiveIntegerField(help_text="File size in bytes")
    content_type = models.CharField(max_length=100)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    # Download tracking
    download_count = models.PositiveIntegerField(default=0)
    last_downloaded_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"Attachment: {self.original_filename} for {self.message.subject}"
    
    def get_file_size_display(self):
        """Return human readable file size"""
        size = self.file_size
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"
    
    def is_image(self):
        """Check if attachment is an image"""
        image_types = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
        return self.content_type.lower() in image_types
    
    def record_download(self):
        """Record when file was downloaded"""
        self.download_count += 1
        self.last_downloaded_at = timezone.now()
        self.save()
    
    @classmethod
    def get_allowed_extensions(cls):
        """Get list of allowed file extensions"""
        return ['.pdf', '.doc', '.docx', '.txt', '.jpg', '.jpeg', '.png', '.gif']
    
    @classmethod
    def get_max_file_size(cls):
        """Get maximum file size in bytes (10MB)"""
        return 10 * 1024 * 1024  # 10MB
    
    class Meta:
        ordering = ['-uploaded_at']


class StudentProgressNote(models.Model):
    """Individual student progress notes from teachers"""
    
    NOTE_TYPES = [
        ('ACADEMIC', 'Academic Progress'),
        ('BEHAVIORAL', 'Behavioral Note'),
        ('ATTENDANCE', 'Attendance Concern'),
        ('ACHIEVEMENT', 'Achievement/Recognition'),
        ('CONCERN', 'General Concern'),
        ('PARENT_CONFERENCE', 'Parent Conference Request'),
    ]
    
    VISIBILITY_CHOICES = [
        ('PARENTS_ONLY', 'Parents Only'),
        ('STAFF_ONLY', 'Staff Only'), 
        ('PARENTS_AND_STAFF', 'Parents and Staff'),
        ('ADMIN_ONLY', 'Administration Only'),
    ]
    
    student = models.ForeignKey(
        'students.Student', 
        on_delete=models.CASCADE,
        related_name='progress_notes'
    )
    teacher = models.ForeignKey(
        User, 
        on_delete=models.CASCADE,
        related_name='written_progress_notes'
    )
    course = models.ForeignKey(
        'Course',
        on_delete=models.CASCADE,
        null=True, 
        blank=True,
        help_text="Course this note relates to (optional)"
    )
    
    note_type = models.CharField(max_length=20, choices=NOTE_TYPES)
    title = models.CharField(max_length=200)
    content = models.TextField()
    visibility = models.CharField(max_length=20, choices=VISIBILITY_CHOICES, default='PARENTS_AND_STAFF')
    
    # Actions and follow-up
    requires_follow_up = models.BooleanField(default=False)
    follow_up_date = models.DateField(null=True, blank=True)
    follow_up_completed = models.BooleanField(default=False)
    follow_up_notes = models.TextField(blank=True)
    
    # Parent engagement
    parent_notified = models.BooleanField(default=False)
    parent_notification_sent_at = models.DateTimeField(null=True, blank=True)
    parent_response = models.TextField(blank=True)
    parent_responded_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.student.first_name} {self.student.last_name} - {self.title}"
    
    class Meta:
        ordering = ['-created_at']
