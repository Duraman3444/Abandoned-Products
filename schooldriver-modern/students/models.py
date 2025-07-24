from django.db import models
from django.core.validators import (
    RegexValidator,
    MinLengthValidator,
)
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
import uuid
import secrets
import string


class GradeLevel(models.Model):
    """Grade levels like K, 1st, 2nd, etc."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=50, unique=True)
    order = models.PositiveIntegerField(help_text="1=Kindergarten, 2=1st grade, etc.")

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return self.name


class SchoolYear(models.Model):
    """Academic year like 2024-2025"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=50, unique=True, help_text="e.g. 2024-2025")
    start_date = models.DateField()
    end_date = models.DateField()
    is_active = models.BooleanField(default=False)

    class Meta:
        ordering = ["-start_date"]

    def __str__(self):
        return self.name


class EmergencyContact(models.Model):
    """Parent/Guardian contact information - modernized version of legacy model"""

    RELATIONSHIP_CHOICES = [
        ("mother", "Mother"),
        ("father", "Father"),
        ("guardian", "Legal Guardian"),
        ("grandparent", "Grandparent"),
        ("other", "Other Relative"),
        ("emergency", "Emergency Contact"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    first_name = models.CharField(
        max_length=100,
        validators=[
            RegexValidator(
                regex=r"^[a-zA-Z\s\-\'\.]+$",
                message="Name can only contain letters, spaces, hyphens, apostrophes, and periods",
            ),
            MinLengthValidator(1, message="First name is required"),
        ],
    )
    last_name = models.CharField(
        max_length=100,
        validators=[
            RegexValidator(
                regex=r"^[a-zA-Z\s\-\'\.]+$",
                message="Name can only contain letters, spaces, hyphens, apostrophes, and periods",
            ),
            MinLengthValidator(1, message="Last name is required"),
        ],
    )
    relationship = models.CharField(max_length=20, choices=RELATIONSHIP_CHOICES)

    # Contact information
    email = models.EmailField(blank=True)
    phone_primary = models.CharField(
        max_length=20,
        blank=True,
        validators=[
            RegexValidator(
                regex=r"^\+?1?[-.\s]?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}$",
                message="Enter a valid phone number (e.g., (555) 123-4567 or 555-123-4567)",
            )
        ],
    )
    phone_secondary = models.CharField(
        max_length=20,
        blank=True,
        validators=[
            RegexValidator(
                regex=r"^\+?1?[-.\s]?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}$",
                message="Enter a valid phone number (e.g., (555) 123-4567 or 555-123-4567)",
            )
        ],
    )

    # Address
    street = models.CharField(
        max_length=200,
        blank=True,
        validators=[
            RegexValidator(
                regex=r"^[a-zA-Z0-9\s\-\.\,\#]+$",
                message="Street address can only contain letters, numbers, spaces, hyphens, periods, commas, and #",
            )
        ],
    )
    city = models.CharField(
        max_length=100,
        blank=True,
        validators=[
            RegexValidator(
                regex=r"^[a-zA-Z\s\-\.]+$",
                message="City can only contain letters, spaces, hyphens, and periods",
            )
        ],
    )
    state = models.CharField(
        max_length=50,
        blank=True,
        validators=[
            RegexValidator(
                regex=r"^[a-zA-Z\s]+$",
                message="State can only contain letters and spaces",
            )
        ],
    )
    zip_code = models.CharField(
        max_length=10,
        blank=True,
        validators=[
            RegexValidator(
                regex=r"^\d{5}(-\d{4})?$",
                message="Enter a valid ZIP code (e.g., 12345 or 12345-6789)",
            )
        ],
    )

    # Primary contact designation
    is_primary = models.BooleanField(
        default=False, help_text="Primary contact for school communications"
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["last_name", "first_name"]

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.get_relationship_display()})"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"


class AuthorizedPickupPerson(models.Model):
    """Authorized pickup persons for students"""
    
    RELATIONSHIP_CHOICES = [
        ("parent", "Parent"),
        ("guardian", "Legal Guardian"),
        ("grandparent", "Grandparent"),
        ("sibling", "Sibling"),
        ("family_friend", "Family Friend"),
        ("childcare", "Childcare Provider"),
        ("other", "Other"),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.ForeignKey(
        'Student', on_delete=models.CASCADE, related_name='authorized_pickup_persons'
    )
    first_name = models.CharField(
        max_length=100,
        validators=[
            RegexValidator(
                regex=r"^[a-zA-Z\s\-\'\.]+$",
                message="Name can only contain letters, spaces, hyphens, apostrophes, and periods",
            ),
            MinLengthValidator(1, message="First name is required"),
        ],
    )
    last_name = models.CharField(
        max_length=100,
        validators=[
            RegexValidator(
                regex=r"^[a-zA-Z\s\-\'\.]+$",
                message="Name can only contain letters, spaces, hyphens, apostrophes, and periods",
            ),
            MinLengthValidator(1, message="Last name is required"),
        ],
    )
    relationship = models.CharField(max_length=20, choices=RELATIONSHIP_CHOICES)
    phone = models.CharField(
        max_length=20,
        validators=[
            RegexValidator(
                regex=r"^\+?1?[-.\s]?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}$",
                message="Enter a valid phone number (e.g., (555) 123-4567 or 555-123-4567)",
            )
        ],
    )
    email = models.EmailField(blank=True)
    id_requirements = models.TextField(
        blank=True, 
        help_text="Special ID requirements or notes for pickup verification"
    )
    is_emergency_contact = models.BooleanField(
        default=False,
        help_text="Can this person be contacted in emergencies?"
    )
    is_active = models.BooleanField(default=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ["last_name", "first_name"]
        verbose_name = "Authorized Pickup Person"
        verbose_name_plural = "Authorized Pickup Persons"
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.get_relationship_display()}) - {self.student.full_name}"
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"


class MedicalInformation(models.Model):
    """Medical information and health details for students"""
    
    SEVERITY_CHOICES = [
        ("low", "Low"),
        ("moderate", "Moderate"), 
        ("high", "High"),
        ("life_threatening", "Life Threatening"),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.OneToOneField(
        'Student', on_delete=models.CASCADE, related_name='medical_information'
    )
    
    # Medical conditions and allergies
    allergies = models.TextField(
        blank=True,
        help_text="List all known allergies and severity"
    )
    medical_conditions = models.TextField(
        blank=True,
        help_text="Ongoing medical conditions (asthma, diabetes, etc.)"
    )
    medications = models.TextField(
        blank=True,
        help_text="Current medications and dosages"
    )
    
    # Emergency medical information
    primary_physician = models.CharField(max_length=200, blank=True)
    primary_physician_phone = models.CharField(
        max_length=20,
        blank=True,
        validators=[
            RegexValidator(
                regex=r"^\+?1?[-.\s]?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}$",
                message="Enter a valid phone number (e.g., (555) 123-4567 or 555-123-4567)",
            )
        ],
    )
    preferred_hospital = models.CharField(max_length=200, blank=True)
    insurance_provider = models.CharField(max_length=200, blank=True)
    
    # Special accommodations
    dietary_restrictions = models.TextField(
        blank=True,
        help_text="Food allergies, dietary restrictions, or special meal requirements"
    )
    physical_limitations = models.TextField(
        blank=True,
        help_text="Physical limitations or accommodations needed"
    )
    emergency_action_plan = models.TextField(
        blank=True,
        help_text="Specific emergency procedures for this student"
    )
    
    # School health room permissions
    can_self_medicate = models.BooleanField(
        default=False,
        help_text="Student is authorized to carry and self-administer medication"
    )
    nurse_notes = models.TextField(
        blank=True,
        help_text="Private notes for school nurse (not visible to parents)"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_updated_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        help_text="User who last updated this information"
    )
    
    class Meta:
        verbose_name = "Medical Information"
        verbose_name_plural = "Medical Information"
    
    def __str__(self):
        return f"Medical Info - {self.student.full_name}"


class Student(models.Model):
    """Modernized student model preserving legacy business logic"""

    GENDER_CHOICES = [
        ("M", "Male"),
        ("F", "Female"),
        ("O", "Other"),
        ("N", "Prefer not to say"),
    ]

    # Core identification
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student_id = models.CharField(
        max_length=20,
        unique=True,
        blank=True,
        help_text="School-specific student ID number",
        validators=[
            RegexValidator(
                regex=r"^[A-Za-z0-9\-]+$",
                message="Student ID can only contain letters, numbers, and hyphens",
            )
        ],
    )

    # Personal information
    first_name = models.CharField(
        max_length=100,
        validators=[
            RegexValidator(
                regex=r"^[a-zA-Z\s\-\'\.]+$",
                message="Name can only contain letters, spaces, hyphens, apostrophes, and periods",
            ),
            MinLengthValidator(1, message="First name is required"),
        ],
    )
    middle_name = models.CharField(
        max_length=100,
        blank=True,
        validators=[
            RegexValidator(
                regex=r"^[a-zA-Z\s\-\'\.]*$",
                message="Name can only contain letters, spaces, hyphens, apostrophes, and periods",
            )
        ],
    )
    last_name = models.CharField(
        max_length=100,
        validators=[
            RegexValidator(
                regex=r"^[a-zA-Z\s\-\'\.]+$",
                message="Name can only contain letters, spaces, hyphens, apostrophes, and periods",
            ),
            MinLengthValidator(1, message="Last name is required"),
        ],
    )
    preferred_name = models.CharField(
        max_length=100,
        blank=True,
        help_text="Name student prefers to be called",
        validators=[
            RegexValidator(
                regex=r"^[a-zA-Z\s\-\'\.]*$",
                message="Name can only contain letters, spaces, hyphens, apostrophes, and periods",
            )
        ],
    )

    date_of_birth = models.DateField()
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, blank=True)

    # Profile photo
    photo = models.ImageField(
        upload_to="student_photos/",
        blank=True,
        null=True,
        help_text="Student photo for ID purposes",
    )

    # Academic information
    grade_level = models.ForeignKey(
        GradeLevel, on_delete=models.PROTECT, null=True, blank=True
    )
    graduation_year = models.IntegerField(null=True, blank=True)
    enrollment_date = models.DateField()
    graduation_date = models.DateField(null=True, blank=True)

    # Status
    is_active = models.BooleanField(default=True)
    withdrawal_date = models.DateField(null=True, blank=True)
    withdrawal_reason = models.TextField(blank=True)

    # Contact relationships
    emergency_contacts = models.ManyToManyField(
        EmergencyContact,
        blank=True,
        help_text="Parents, guardians, and emergency contacts",
    )
    
    # Parent portal access - users who can view this student's information
    family_access_users = models.ManyToManyField(
        'auth.User',
        blank=True,
        related_name='accessible_students',
        help_text="Parent/Guardian users who can access this student's information via the parent portal",
    )

    # Additional information
    special_needs = models.TextField(
        blank=True, help_text="IEP, 504 plan, allergies, medical needs"
    )
    notes = models.TextField(blank=True, help_text="Administrative notes")

    # Cached primary contact info (for performance)
    primary_contact_name = models.CharField(max_length=200, blank=True, editable=False)
    primary_contact_email = models.EmailField(blank=True, editable=False)
    primary_contact_phone = models.CharField(max_length=20, blank=True, editable=False)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["last_name", "first_name"]
        indexes = [
            models.Index(fields=["student_id"]),
            models.Index(fields=["is_active", "grade_level"]),
            models.Index(fields=["graduation_year"]),
        ]

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.student_id})"

    @property
    def full_name(self):
        if self.middle_name:
            return f"{self.first_name} {self.middle_name} {self.last_name}"
        return f"{self.first_name} {self.last_name}"

    @property
    def display_name(self):
        """Name to display in UI - preferred name if available"""
        if self.preferred_name:
            return f"{self.preferred_name} {self.last_name}"
        return self.full_name

    def save(self, *args, **kwargs):
        # Auto-generate student ID if not provided
        if not self.student_id:
            # Simple format: year + 4-digit sequence
            year = str(self.enrollment_date.year)[2:]  # Last 2 digits of year
            last_student = (
                Student.objects.filter(student_id__startswith=year)
                .order_by("student_id")
                .last()
            )

            if last_student:
                try:
                    last_num = int(last_student.student_id[2:])
                    next_num = last_num + 1
                except (ValueError, IndexError):
                    next_num = 1
            else:
                next_num = 1

            self.student_id = f"{year}{next_num:04d}"

        # Update cached contact info
        primary_contact = self.emergency_contacts.filter(is_primary=True).first()
        if primary_contact:
            self.primary_contact_name = primary_contact.full_name
            self.primary_contact_email = primary_contact.email
            self.primary_contact_phone = primary_contact.phone_primary

        super().save(*args, **kwargs)

    def get_primary_contact(self):
        """Get primary emergency contact"""
        return self.emergency_contacts.filter(is_primary=True).first()

    def get_age(self):
        """Calculate student's current age"""
        from datetime import date

        today = date.today()
        return (
            today.year
            - self.date_of_birth.year
            - (
                (today.month, today.day)
                < (self.date_of_birth.month, self.date_of_birth.day)
            )
        )


class ParentVerificationCode(models.Model):
    """Verification codes for parent account linking"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='verification_codes')
    code = models.CharField(max_length=8, unique=True, editable=False)
    parent_email = models.EmailField(help_text="Email address of the parent requesting access")
    parent_name = models.CharField(max_length=200, help_text="Full name of the parent requesting access")
    
    # Code status
    is_used = models.BooleanField(default=False)
    used_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='used_verification_codes')
    used_at = models.DateTimeField(null=True, blank=True)
    
    # Expiration
    expires_at = models.DateTimeField()
    
    # Audit trail
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_verification_codes')
    created_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True, help_text="Administrative notes about this verification request")
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['parent_email']),
            models.Index(fields=['expires_at']),
        ]
    
    def __str__(self):
        return f"Verification code {self.code} for {self.student.full_name} (expires {self.expires_at})"
    
    def save(self, *args, **kwargs):
        if not self.code:
            self.code = self.generate_code()
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(days=7)  # 7-day expiration
        super().save(*args, **kwargs)
    
    def generate_code(self):
        """Generate a unique 8-character verification code"""
        while True:
            # Generate code with letters and numbers, avoiding confusing characters
            alphabet = string.ascii_uppercase + string.digits
            alphabet = alphabet.translate(str.maketrans('', '', '0O1IL'))  # Remove confusing chars
            code = ''.join(secrets.choice(alphabet) for _ in range(8))
            
            # Ensure uniqueness
            if not ParentVerificationCode.objects.filter(code=code).exists():
                return code
    
    def is_expired(self):
        """Check if the verification code has expired"""
        return timezone.now() > self.expires_at
    
    def is_valid(self):
        """Check if the verification code is valid for use"""
        return not self.is_used and not self.is_expired()
    
    def use_code(self, user):
        """Mark the code as used by a specific user"""
        if not self.is_valid():
            return False
        
        self.is_used = True
        self.used_by = user
        self.used_at = timezone.now()
        self.save()
        
        # Add the user to the student's family_access_users
        self.student.family_access_users.add(user)
        
        return True
