from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from decimal import Decimal


class LunchAccount(models.Model):
    """Student lunch account management"""
    
    student = models.OneToOneField('students.Student', on_delete=models.CASCADE, related_name='lunch_account')
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    low_balance_threshold = models.DecimalField(max_digits=10, decimal_places=2, default=5.00)
    auto_reload_enabled = models.BooleanField(default=False)
    auto_reload_amount = models.DecimalField(max_digits=10, decimal_places=2, default=25.00)
    auto_reload_threshold = models.DecimalField(max_digits=10, decimal_places=2, default=10.00)
    
    # Payment methods
    default_payment_method = models.CharField(max_length=50, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.student.display_name} - ${self.balance}"
    
    @property
    def is_low_balance(self):
        return self.balance <= self.low_balance_threshold
    
    def add_funds(self, amount, payment_method="Manual", description=""):
        """Add funds to the account"""
        transaction = LunchTransaction.objects.create(
            lunch_account=self,
            transaction_type='CREDIT',
            amount=amount,
            description=description or f"Funds added via {payment_method}",
            payment_method=payment_method
        )
        self.balance += amount
        self.save()
        return transaction
    
    def deduct_funds(self, amount, description="Lunch purchase"):
        """Deduct funds from the account"""
        if self.balance >= amount:
            transaction = LunchTransaction.objects.create(
                lunch_account=self,
                transaction_type='DEBIT',
                amount=amount,
                description=description
            )
            self.balance -= amount
            self.save()
            
            # Check for auto-reload
            if self.auto_reload_enabled and self.balance <= self.auto_reload_threshold:
                self.trigger_auto_reload()
            
            return transaction
        else:
            raise ValueError("Insufficient funds")
    
    def trigger_auto_reload(self):
        """Trigger automatic reload if enabled"""
        if self.auto_reload_enabled and self.default_payment_method:
            return self.add_funds(
                self.auto_reload_amount,
                self.default_payment_method,
                "Auto-reload triggered"
            )


class LunchTransaction(models.Model):
    """Lunch account transaction history"""
    
    TRANSACTION_TYPES = [
        ('CREDIT', 'Credit (Money Added)'),
        ('DEBIT', 'Debit (Money Spent)'),
    ]
    
    lunch_account = models.ForeignKey(LunchAccount, on_delete=models.CASCADE, related_name='transactions')
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.CharField(max_length=200)
    payment_method = models.CharField(max_length=50, blank=True)
    transaction_date = models.DateTimeField(auto_now_add=True)
    
    # Optional transaction details
    reference_number = models.CharField(max_length=100, blank=True)
    processed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        ordering = ['-transaction_date']
    
    def __str__(self):
        return f"{self.lunch_account.student.display_name} - {self.transaction_type} ${self.amount}"


class TransportationInfo(models.Model):
    """Student transportation information"""
    
    TRANSPORT_TYPES = [
        ('BUS', 'School Bus'),
        ('PARENT', 'Parent Pickup'),
        ('WALKER', 'Walker'),
        ('OTHER', 'Other'),
    ]
    
    student = models.OneToOneField('students.Student', on_delete=models.CASCADE, related_name='transportation')
    transport_type = models.CharField(max_length=20, choices=TRANSPORT_TYPES, default='PARENT')
    
    # Bus information
    bus_route = models.CharField(max_length=50, blank=True)
    bus_number = models.CharField(max_length=20, blank=True)
    pickup_time = models.TimeField(null=True, blank=True)
    pickup_location = models.CharField(max_length=200, blank=True)
    dropoff_time = models.TimeField(null=True, blank=True)
    dropoff_location = models.CharField(max_length=200, blank=True)
    
    # Emergency contacts for transportation
    emergency_transport_contact = models.CharField(max_length=100, blank=True)
    emergency_transport_phone = models.CharField(max_length=20, blank=True)
    
    # Special notes
    special_instructions = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.student.display_name} - {self.get_transport_type_display()}"


class TransportationAlert(models.Model):
    """Transportation alerts and notifications"""
    
    ALERT_TYPES = [
        ('DELAY', 'Bus Delay'),
        ('CANCELLATION', 'Route Cancellation'),
        ('ROUTE_CHANGE', 'Route Change'),
        ('WEATHER', 'Weather Related'),
        ('EMERGENCY', 'Emergency'),
    ]
    
    alert_type = models.CharField(max_length=20, choices=ALERT_TYPES)
    title = models.CharField(max_length=200)
    message = models.TextField()
    affected_routes = models.CharField(max_length=200, help_text="Comma-separated route numbers")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.get_alert_type_display()}: {self.title}"
    
    def affects_route(self, route_number):
        """Check if this alert affects a specific route"""
        if not self.affected_routes:
            return True  # Affects all routes
        return str(route_number) in self.affected_routes.split(',')


class Activity(models.Model):
    """Extracurricular activities"""
    
    ACTIVITY_TYPES = [
        ('SPORTS', 'Sports'),
        ('ACADEMIC', 'Academic Club'),
        ('ARTS', 'Arts & Music'),
        ('SERVICE', 'Community Service'),
        ('OTHER', 'Other'),
    ]
    
    name = models.CharField(max_length=100)
    description = models.TextField()
    activity_type = models.CharField(max_length=20, choices=ACTIVITY_TYPES)
    supervisor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Schedule and logistics
    meeting_days = models.CharField(max_length=50, help_text="e.g., 'Monday, Wednesday, Friday'")
    meeting_time = models.CharField(max_length=50, help_text="e.g., '3:30 PM - 5:00 PM'")
    location = models.CharField(max_length=100)
    
    # Enrollment details
    max_participants = models.IntegerField(default=0, help_text="0 means no limit")
    grade_levels = models.CharField(max_length=50, help_text="e.g., '9,10,11,12'")
    registration_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    # Dates
    registration_start = models.DateField()
    registration_end = models.DateField()
    activity_start = models.DateField()
    activity_end = models.DateField()
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name
    
    @property
    def is_registration_open(self):
        today = timezone.now().date()
        return self.registration_start <= today <= self.registration_end
    
    @property
    def available_spots(self):
        if self.max_participants == 0:
            return float('inf')
        return max(0, self.max_participants - self.enrollments.count())
    
    def can_student_enroll(self, student):
        """Check if a student can enroll in this activity"""
        # Check grade level
        if self.grade_levels:
            student_grade = getattr(student, 'grade_level', None)
            if student_grade and str(student_grade) not in self.grade_levels.split(','):
                return False, "Grade level not eligible"
        
        # Check if registration is open
        if not self.is_registration_open:
            return False, "Registration is closed"
        
        # Check available spots
        if self.available_spots <= 0:
            return False, "Activity is full"
        
        # Check if already enrolled
        if self.enrollments.filter(student=student, status='ENROLLED').exists():
            return False, "Already enrolled"
        
        return True, "Eligible to enroll"


class ActivityEnrollment(models.Model):
    """Student enrollment in activities"""
    
    STATUS_CHOICES = [
        ('PENDING', 'Pending Approval'),
        ('ENROLLED', 'Enrolled'),
        ('WAITLIST', 'Waitlisted'),
        ('DECLINED', 'Declined'),
        ('WITHDRAWN', 'Withdrawn'),
    ]
    
    activity = models.ForeignKey(Activity, on_delete=models.CASCADE, related_name='enrollments')
    student = models.ForeignKey('students.Student', on_delete=models.CASCADE, related_name='activity_enrollments')
    enrolled_by = models.ForeignKey(User, on_delete=models.CASCADE)  # Parent who enrolled
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    
    enrollment_date = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)
    
    # Payment information
    fee_paid = models.BooleanField(default=False)
    payment_date = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        unique_together = ['activity', 'student']
    
    def __str__(self):
        return f"{self.student.display_name} - {self.activity.name}"


class SupplyList(models.Model):
    """School supply lists by grade/class"""
    
    grade_level = models.CharField(max_length=20)
    subject = models.CharField(max_length=100, blank=True)
    teacher = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    school_year = models.ForeignKey('students.SchoolYear', on_delete=models.CASCADE)
    
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    
    # Optional external shopping integration
    shopping_url = models.URLField(blank=True, help_text="Link to pre-built shopping cart")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.title} - Grade {self.grade_level}"


class SupplyItem(models.Model):
    """Individual items in supply lists"""
    
    supply_list = models.ForeignKey(SupplyList, on_delete=models.CASCADE, related_name='items')
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    quantity = models.CharField(max_length=50, default="1")
    estimated_cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Shopping details
    brand_preference = models.CharField(max_length=100, blank=True)
    store_suggestions = models.CharField(max_length=200, blank=True)
    online_link = models.URLField(blank=True)
    
    is_required = models.BooleanField(default=True)
    order = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['order', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.quantity})"


class EventRSVP(models.Model):
    """RSVP tracking for school events"""
    
    RSVP_STATUS = [
        ('YES', 'Yes, attending'),
        ('NO', 'Not attending'),
        ('MAYBE', 'Maybe attending'),
    ]
    
    event = models.ForeignKey('academics.SchoolCalendarEvent', on_delete=models.CASCADE, related_name='rsvps')
    student = models.ForeignKey('students.Student', on_delete=models.CASCADE)
    parent = models.ForeignKey(User, on_delete=models.CASCADE)
    
    rsvp_status = models.CharField(max_length=10, choices=RSVP_STATUS)
    number_attending = models.IntegerField(default=1, help_text="Total number of family members attending")
    notes = models.TextField(blank=True, help_text="Dietary restrictions, special needs, etc.")
    
    rsvp_date = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['event', 'student', 'parent']
    
    def __str__(self):
        return f"{self.student.display_name} - {self.event.title} ({self.rsvp_status})"


class VolunteerOpportunity(models.Model):
    """Volunteer opportunities for parents"""
    
    VOLUNTEER_TYPES = [
        ('EVENT', 'Event Volunteer'),
        ('CLASSROOM', 'Classroom Helper'),
        ('CHAPERONING', 'Chaperoning'),
        ('FUNDRAISING', 'Fundraising'),
        ('ADMINISTRATIVE', 'Administrative'),
        ('OTHER', 'Other'),
    ]
    
    title = models.CharField(max_length=200)
    description = models.TextField()
    volunteer_type = models.CharField(max_length=20, choices=VOLUNTEER_TYPES)
    coordinator = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Schedule
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    location = models.CharField(max_length=200)
    
    # Requirements
    volunteers_needed = models.IntegerField(default=1)
    special_requirements = models.TextField(blank=True, help_text="Background check, special skills, etc.")
    
    # Contact and logistics
    contact_email = models.EmailField(blank=True)
    contact_phone = models.CharField(max_length=20, blank=True)
    preparation_notes = models.TextField(blank=True)
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.title} - {self.date}"
    
    @property
    def volunteers_signed_up(self):
        return self.signups.filter(status='CONFIRMED').count()
    
    @property
    def spots_remaining(self):
        return max(0, self.volunteers_needed - self.volunteers_signed_up)


class VolunteerSignup(models.Model):
    """Parent volunteer signups"""
    
    STATUS_CHOICES = [
        ('PENDING', 'Pending Confirmation'),
        ('CONFIRMED', 'Confirmed'),
        ('DECLINED', 'Declined'),
        ('CANCELLED', 'Cancelled'),
    ]
    
    opportunity = models.ForeignKey(VolunteerOpportunity, on_delete=models.CASCADE, related_name='signups')
    volunteer = models.ForeignKey(User, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    
    signup_date = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True, help_text="Additional information or questions")
    
    # Contact information (in case it differs from user profile)
    contact_phone = models.CharField(max_length=20, blank=True)
    emergency_contact = models.CharField(max_length=100, blank=True)
    
    class Meta:
        unique_together = ['opportunity', 'volunteer']
    
    def __str__(self):
        return f"{self.volunteer.get_full_name()} - {self.opportunity.title}"
