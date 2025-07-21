from django.db import models
from django.core.validators import RegexValidator
from students.models import GradeLevel, SchoolYear, EmergencyContact, Student
import uuid


class FeederSchool(models.Model):
    """Schools that commonly send applicants"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200, unique=True)
    school_type = models.CharField(max_length=50, blank=True, help_text="Public, Private, Charter, etc.")
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=50, blank=True)
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['name']
        
    def __str__(self):
        return self.name


class AdmissionLevel(models.Model):
    """Stages in the admission process (Inquiry -> Application -> Interview -> Decision)"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(
        max_length=100, 
        unique=True,
        validators=[RegexValidator(r'^[a-zA-Z0-9\s\-]+$', 'Must be alphanumeric')]
    )
    order = models.PositiveIntegerField(unique=True, help_text="Order in admission process, 1 being first")
    description = models.TextField(blank=True, help_text="What happens at this level")
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['order']
        
    def __str__(self):
        return self.name


class AdmissionCheck(models.Model):
    """Required items/documents for each admission level"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    level = models.ForeignKey(AdmissionLevel, on_delete=models.CASCADE, related_name='checks')
    is_required = models.BooleanField(
        default=True, 
        help_text="When true, applicant cannot advance past this level without completing this check"
    )
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['level__order', 'name']
        unique_together = ['name', 'level']
        
    def __str__(self):
        return f"{self.name} ({self.level})"


class ApplicationDecision(models.Model):
    """Possible admission decisions"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    is_positive = models.BooleanField(default=True, help_text="Indicates acceptance vs rejection")
    order = models.PositiveIntegerField(help_text="Display order")
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['order']
        
    def __str__(self):
        return self.name


class Applicant(models.Model):
    """Prospective student in the admission process - modernized from legacy"""
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
        ('N', 'Prefer not to say'),
    ]
    
    LIVING_SITUATION_CHOICES = [
        ('both_parents', 'Both Parents'),
        ('mother', 'Mother'),
        ('father', 'Father'),
        ('guardians', 'Guardian(s)'),
        ('other', 'Other'),
    ]
    
    # Core identification
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    applicant_id = models.CharField(max_length=20, unique=True, blank=True)
    
    # Personal information
    first_name = models.CharField(max_length=100)
    middle_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100)
    preferred_name = models.CharField(max_length=100, blank=True)
    
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, blank=True)
    
    # Photo
    photo = models.ImageField(upload_to='applicant_photos/', blank=True, null=True)
    
    # Contact information
    email = models.EmailField(blank=True, help_text="Student's email if available")
    street = models.CharField(max_length=200, blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=50, blank=True)
    zip_code = models.CharField(max_length=10, blank=True)
    
    # Academic information
    applying_for_grade = models.ForeignKey(GradeLevel, on_delete=models.PROTECT, null=True, blank=True)
    school_year = models.ForeignKey(SchoolYear, on_delete=models.PROTECT, null=True, blank=True)
    current_school = models.ForeignKey(FeederSchool, on_delete=models.SET_NULL, null=True, blank=True)
    current_school_name = models.CharField(
        max_length=200, 
        blank=True, 
        help_text="If current school not in our feeder list"
    )
    
    # Family information
    living_situation = models.CharField(max_length=20, choices=LIVING_SITUATION_CHOICES, blank=True)
    parent_guardians = models.ManyToManyField(
        EmergencyContact, 
        blank=True, 
        help_text="Parent/guardian contacts"
    )
    siblings = models.ManyToManyField(
        Student, 
        blank=True, 
        help_text="Current students who are siblings"
    )
    
    # Admission process tracking
    level = models.ForeignKey(
        AdmissionLevel, 
        on_delete=models.PROTECT, 
        null=True, 
        blank=True,
        help_text="Current stage in admission process"
    )
    completed_checks = models.ManyToManyField(
        AdmissionCheck, 
        blank=True,
        help_text="Requirements completed by applicant"
    )
    
    # Application decision
    decision = models.ForeignKey(
        ApplicationDecision, 
        on_delete=models.PROTECT, 
        null=True, 
        blank=True
    )
    decision_date = models.DateField(null=True, blank=True)
    decision_by = models.CharField(max_length=200, blank=True, help_text="Who made the decision")
    
    # Status tracking
    is_ready_for_enrollment = models.BooleanField(default=False)
    is_from_online_inquiry = models.BooleanField(default=False)
    follow_up_date = models.DateField(null=True, blank=True)
    
    # Connection to student record
    enrolled_student = models.OneToOneField(
        Student, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='application',
        help_text="Student record if applicant was enrolled"
    )
    
    # Notes and additional info
    notes = models.TextField(blank=True, help_text="Internal notes about applicant")
    special_circumstances = models.TextField(blank=True)
    
    # Cached parent info (for performance)
    primary_parent_name = models.CharField(max_length=200, blank=True, editable=False)
    primary_parent_email = models.EmailField(blank=True, editable=False)
    primary_parent_phone = models.CharField(max_length=20, blank=True, editable=False)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['applicant_id']),
            models.Index(fields=['school_year', 'level']),
            models.Index(fields=['is_ready_for_enrollment']),
            models.Index(fields=['created_at']),
        ]
        
    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.applicant_id or 'New'})"
        
    @property
    def full_name(self):
        if self.middle_name:
            return f"{self.first_name} {self.middle_name} {self.last_name}"
        return f"{self.first_name} {self.last_name}"
    
    @property
    def display_name(self):
        """Name to display in UI"""
        if self.preferred_name:
            return f"{self.preferred_name} {self.last_name}"
        return self.full_name
        
    def save(self, *args, **kwargs):
        # Auto-generate applicant ID if not provided
        if not self.applicant_id:
            year = str(self.created_at.year if self.created_at else 2024)[2:]
            last_applicant = Applicant.objects.filter(
                applicant_id__startswith=f"A{year}"
            ).order_by('applicant_id').last()
            
            if last_applicant:
                try:
                    last_num = int(last_applicant.applicant_id[3:])
                    next_num = last_num + 1
                except (ValueError, IndexError):
                    next_num = 1
            else:
                next_num = 1
                
            self.applicant_id = f"A{year}{next_num:04d}"
            
        # Update admission level based on completed checks
        if self.pk:  # Only for existing records
            self._update_admission_level()
            
        # Cache primary parent info
        primary_parent = self.parent_guardians.first()  # Will need to be called after save
        
        super().save(*args, **kwargs)
        
    def _update_admission_level(self):
        """Automatically advance applicant to appropriate level based on completed requirements"""
        levels = AdmissionLevel.objects.filter(is_active=True).order_by('order')
        
        current_level = None
        for level in levels:
            required_checks = level.checks.filter(is_required=True, is_active=True)
            completed_required = required_checks.filter(
                id__in=self.completed_checks.values_list('id', flat=True)
            ).count()
            
            if completed_required >= required_checks.count():
                current_level = level
            else:
                break
                
        if current_level != self.level:
            self.level = current_level
            
    def get_next_required_checks(self):
        """Get list of required checks not yet completed for current level"""
        if not self.level:
            return AdmissionCheck.objects.none()
            
        completed_ids = self.completed_checks.values_list('id', flat=True)
        return self.level.checks.filter(
            is_required=True, 
            is_active=True
        ).exclude(id__in=completed_ids)
        
    def can_advance_to_next_level(self):
        """Check if applicant has completed all requirements for current level"""
        return not self.get_next_required_checks().exists()
        
    def get_completion_percentage(self):
        """Calculate what percentage of the admission process is complete"""
        if not self.level:
            return 0
            
        total_levels = AdmissionLevel.objects.filter(is_active=True).count()
        if total_levels == 0:
            return 100
            
        current_position = self.level.order
        return min(100, (current_position / total_levels) * 100)


class ContactLog(models.Model):
    """Log of communications with applicants/families"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    applicant = models.ForeignKey(Applicant, on_delete=models.CASCADE, related_name='contact_logs')
    contact_date = models.DateTimeField(auto_now_add=True)
    contact_type = models.CharField(
        max_length=20,
        choices=[
            ('phone', 'Phone Call'),
            ('email', 'Email'),
            ('meeting', 'In-Person Meeting'),
            ('mail', 'Mail'),
            ('other', 'Other'),
        ]
    )
    contacted_by = models.CharField(max_length=200, help_text="Staff member who made contact")
    summary = models.TextField(help_text="Summary of communication")
    follow_up_needed = models.BooleanField(default=False)
    follow_up_date = models.DateField(null=True, blank=True)
    
    class Meta:
        ordering = ['-contact_date']
        
    def __str__(self):
        return f"{self.contact_type} - {self.applicant} ({self.contact_date.date()})"


class OpenHouse(models.Model):
    """School open house events"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    date = models.DateTimeField()
    description = models.TextField(blank=True)
    capacity = models.PositiveIntegerField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    
    # Track attendance
    attendees = models.ManyToManyField(Applicant, blank=True, help_text="Applicants who attended")
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-date']
        
    def __str__(self):
        return f"{self.name} - {self.date.strftime('%B %d, %Y')}"
        
    def get_attendance_count(self):
        return self.attendees.count()
        
    def get_capacity_percentage(self):
        if not self.capacity:
            return 0
        return min(100, (self.get_attendance_count() / self.capacity) * 100)
