from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
from students.models import Student, ParentVerificationCode, EmergencyContact, AuthorizedPickupPerson, MedicalInformation
from academics.models import EarlyDismissalRequest, Message, MessageAttachment
from datetime import datetime, date, timedelta
import re


class MultipleFileInput(forms.ClearableFileInput):
    """Custom widget for multiple file uploads"""
    allow_multiple_selected = True


class MultipleFileField(forms.FileField):
    """Field for handling multiple file uploads"""
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultipleFileInput())
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        single_file_clean = super().clean
        if isinstance(data, (list, tuple)):
            result = [single_file_clean(d, initial) for d in data]
        else:
            result = single_file_clean(data, initial)
        return result


class ParentRegistrationForm(UserCreationForm):
    """Parent registration form with verification code"""
    
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    email = forms.EmailField(required=True)
    verification_code = forms.CharField(
        max_length=20,
        help_text="Enter the verification code provided by the school"
    )
    
    class Meta:
        model = User
        fields = ("username", "first_name", "last_name", "email", "password1", "password2", "verification_code")
    
    def clean_email(self):
        email = self.cleaned_data['email']
        if User.objects.filter(email=email).exists():
            raise ValidationError("A user with this email already exists.")
        return email
    
    def clean_verification_code(self):
        code = self.cleaned_data['verification_code']
        
        try:
            verification = ParentVerificationCode.objects.get(
                code=code,
                is_used=False,
                expires_at__gt=datetime.now()
            )
            self._verification = verification
            return code
        except ParentVerificationCode.DoesNotExist:
            raise ValidationError("Invalid or expired verification code.")
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        
        if commit:
            user.save()
            # Mark verification as used and link parent to student
            verification = self._verification
            verification.is_used = True
            verification.used_at = datetime.now()
            verification.save()
            
            # Add user to student's family access
            student = verification.student
            student.family_access_users.add(user)
        
        return user


class VerificationCodeForm(forms.Form):
    """Simple verification code form for existing users"""
    
    verification_code = forms.CharField(
        max_length=20,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter verification code'
        }),
        help_text="Enter the verification code provided by the school"
    )
    
    def clean_verification_code(self):
        code = self.cleaned_data['verification_code']
        
        try:
            verification = ParentVerificationCode.objects.get(
                code=code,
                is_used=False,
                expires_at__gt=datetime.now()
            )
            self._verification = verification
            return code
        except ParentVerificationCode.DoesNotExist:
            raise ValidationError("Invalid or expired verification code.")


class ParentAccountLinkForm(forms.Form):
    """Form for linking parent account to child via verification code"""
    
    verification_code = forms.CharField(
        max_length=20,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter verification code'
        }),
        help_text="Enter the verification code provided by the school to link your account to a student"
    )
    
    def clean_verification_code(self):
        code = self.cleaned_data['verification_code']
        
        try:
            verification = ParentVerificationCode.objects.get(
                code=code,
                is_used=False,
                expires_at__gt=datetime.now()
            )
            self._verification = verification
            return code
        except ParentVerificationCode.DoesNotExist:
            raise ValidationError("Invalid or expired verification code.")


class VerificationRequestForm(forms.Form):
    """Form for requesting new verification codes"""
    
    student_name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter student full name'
        }),
        help_text="Enter the full name of your child"
    )
    student_id = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Student ID (if known)'
        }),
        help_text="If you know your child's student ID, please enter it"
    )
    parent_email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Your email address'
        }),
        help_text="Email address where you can be contacted"
    )
    message = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'Please explain your request...'
        }),
        help_text="Please provide any additional information that might help us verify your identity"
    )


class EarlyDismissalRequestForm(forms.ModelForm):
    """Form for parents to request early dismissal"""
    
    class Meta:
        model = EarlyDismissalRequest
        fields = [
            'request_date', 'dismissal_time', 'reason', 'pickup_person', 
            'contact_phone', 'is_recurring', 'recurring_days', 'recurring_end_date'
        ]
        widgets = {
            'request_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control',
                'min': date.today().isoformat()
            }),
            'dismissal_time': forms.TimeInput(attrs={
                'type': 'time',
                'class': 'form-control'
            }),
            'reason': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Please provide the reason for early dismissal...'
            }),
            'pickup_person': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Name of person picking up student'
            }),
            'contact_phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '(555) 123-4567'
            }),
            'is_recurring': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'recurring_days': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., MON,WED,FRI',
                'help_text': 'For recurring requests, specify days (MON,TUE,WED,THU,FRI)'
            }),
            'recurring_end_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control'
            })
        }
    
    def __init__(self, *args, **kwargs):
        self.student = kwargs.pop('student', None)
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Set minimum date to today
        self.fields['request_date'].widget.attrs['min'] = date.today().isoformat()
        
        # Make recurring fields optional initially
        self.fields['recurring_days'].required = False
        self.fields['recurring_end_date'].required = False
    
    def clean_request_date(self):
        request_date = self.cleaned_data['request_date']
        if request_date < date.today():
            raise ValidationError("Cannot request dismissal for past dates.")
        
        # Don't allow requests too far in advance (e.g., more than 30 days)
        if request_date > date.today() + timedelta(days=30):
            raise ValidationError("Cannot request dismissal more than 30 days in advance.")
        
        return request_date
    
    def clean_contact_phone(self):
        phone = self.cleaned_data['contact_phone']
        # Basic phone number validation
        phone_pattern = re.compile(r'^\+?1?[-.\s]?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})$')
        if not phone_pattern.match(phone):
            raise ValidationError("Please enter a valid phone number.")
        return phone
    
    def clean_recurring_days(self):
        is_recurring = self.cleaned_data.get('is_recurring', False)
        recurring_days = self.cleaned_data.get('recurring_days', '')
        
        if is_recurring and not recurring_days:
            raise ValidationError("Please specify recurring days for recurring requests.")
        
        if recurring_days:
            valid_days = {'MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT', 'SUN'}
            days = [day.strip().upper() for day in recurring_days.split(',')]
            
            for day in days:
                if day not in valid_days:
                    raise ValidationError(f"Invalid day: {day}. Use MON, TUE, WED, THU, FRI, SAT, SUN")
            
            return ','.join(days)
        
        return recurring_days
    
    def clean_recurring_end_date(self):
        is_recurring = self.cleaned_data.get('is_recurring', False)
        recurring_end_date = self.cleaned_data.get('recurring_end_date')
        request_date = self.cleaned_data.get('request_date')
        
        if is_recurring and not recurring_end_date:
            raise ValidationError("Please specify an end date for recurring requests.")
        
        if recurring_end_date and request_date and recurring_end_date <= request_date:
            raise ValidationError("Recurring end date must be after the request date.")
        
        return recurring_end_date
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.student = self.student
        instance.requested_by = self.user
        
        if commit:
            instance.save()
        
        return instance


class MessageForm(forms.ModelForm):
    """Form for sending messages with file attachments"""
    
    attachments = MultipleFileField(
        required=False,
        help_text="Upload files (PDF, DOC, DOCX, JPG, PNG, TXT). Max 10MB per file."
    )
    
    class Meta:
        model = Message
        fields = ['recipient', 'subject', 'content', 'is_urgent', 'student_context']
        widgets = {
            'recipient': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'subject': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Message subject...',
                'required': True
            }),
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 6,
                'placeholder': 'Type your message here...',
                'required': True
            }),
            'is_urgent': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'student_context': forms.Select(attrs={
                'class': 'form-select'
            })
        }
    
    def __init__(self, *args, **kwargs):
        self.sender = kwargs.pop('sender', None)
        self.available_recipients = kwargs.pop('available_recipients', None)
        self.student_context_options = kwargs.pop('student_context_options', None)
        super().__init__(*args, **kwargs)
        
        # Set recipient choices (teachers for this parent's children)
        if self.available_recipients:
            self.fields['recipient'].queryset = self.available_recipients
            self.fields['recipient'].empty_label = "Select a teacher..."
        
        # Set student context options
        if self.student_context_options:
            self.fields['student_context'].queryset = self.student_context_options
            self.fields['student_context'].empty_label = "Select student (optional)..."
        else:
            self.fields['student_context'].widget = forms.HiddenInput()
    
    def clean_attachments(self):
        """Validate file attachments"""
        files = self.files.getlist('attachments')
        
        if files:
            allowed_extensions = MessageAttachment.get_allowed_extensions()
            max_size = MessageAttachment.get_max_file_size()
            
            for file in files:
                # Check file extension
                file_ext = '.' + file.name.split('.')[-1].lower()
                if file_ext not in allowed_extensions:
                    raise ValidationError(
                        f"File type '{file_ext}' not allowed. "
                        f"Allowed types: {', '.join(allowed_extensions)}"
                    )
                
                # Check file size
                if file.size > max_size:
                    raise ValidationError(
                        f"File '{file.name}' is too large. "
                        f"Maximum size: {MessageAttachment.get_max_file_size() // (1024*1024)}MB"
                    )
        
        return files
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.sender = self.sender
        
        if commit:
            instance.save()
            
            # Handle file attachments
            files = self.cleaned_data.get('attachments', [])
            if files:
                for file in files:
                    attachment = MessageAttachment(
                        message=instance,
                        file=file,
                        original_filename=file.name,
                        file_size=file.size,
                        content_type=file.content_type or 'application/octet-stream'
                    )
                    attachment.save()
        
        return instance


class MessageReplyForm(forms.ModelForm):
    """Form for replying to messages"""
    
    attachments = MultipleFileField(
        required=False,
        help_text="Upload files (PDF, DOC, DOCX, JPG, PNG, TXT). Max 10MB per file."
    )
    
    class Meta:
        model = Message
        fields = ['content', 'is_urgent']
        widgets = {
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Type your reply...',
                'required': True
            }),
            'is_urgent': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }
    
    def __init__(self, *args, **kwargs):
        self.sender = kwargs.pop('sender', None)
        self.original_message = kwargs.pop('original_message', None)
        super().__init__(*args, **kwargs)
    
    def clean_attachments(self):
        """Validate file attachments"""
        files = self.files.getlist('attachments')
        
        if files:
            allowed_extensions = MessageAttachment.get_allowed_extensions()
            max_size = MessageAttachment.get_max_file_size()
            
            for file in files:
                # Check file extension
                file_ext = '.' + file.name.split('.')[-1].lower()
                if file_ext not in allowed_extensions:
                    raise ValidationError(
                        f"File type '{file_ext}' not allowed. "
                        f"Allowed types: {', '.join(allowed_extensions)}"
                    )
                
                # Check file size
                if file.size > max_size:
                    raise ValidationError(
                        f"File '{file.name}' is too large. "
                        f"Maximum size: {MessageAttachment.get_max_file_size() // (1024*1024)}MB"
                    )
        
        return files
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.sender = self.sender
        
        if self.original_message:
            # Set up reply relationship
            instance.recipient = self.original_message.sender
            instance.subject = f"Re: {self.original_message.subject}"
            instance.parent_message = self.original_message
            instance.thread_id = self.original_message.thread_id
            instance.student_context = self.original_message.student_context
        
        if commit:
            instance.save()
            
            # Handle file attachments
            files = self.cleaned_data.get('attachments', [])
            if files:
                for file in files:
                    attachment = MessageAttachment(
                        message=instance,
                        file=file,
                        original_filename=file.name,
                        file_size=file.size,
                        content_type=file.content_type or 'application/octet-stream'
                    )
                    attachment.save()
        
        return instance



class EmergencyContactForm(forms.ModelForm):
    """Form for parents to update emergency contact information"""
    
    class Meta:
        model = EmergencyContact
        fields = [
            "first_name", "last_name", "relationship", "email",
            "phone_primary", "phone_secondary", "street", "city", "state", "zip_code",
            "is_primary"
        ]
        widgets = {
            "first_name": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "First Name"
            }),
            "last_name": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Last Name"
            }),
            "relationship": forms.Select(attrs={
                "class": "form-select"
            }),
            "email": forms.EmailInput(attrs={
                "class": "form-control",
                "placeholder": "email@example.com"
            }),
            "phone_primary": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "(555) 123-4567"
            }),
            "phone_secondary": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "(555) 123-4567"
            }),
            "street": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "123 Main Street"
            }),
            "city": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "City"
            }),
            "state": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "State"
            }),
            "zip_code": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "12345"
            }),
            "is_primary": forms.CheckboxInput(attrs={
                "class": "form-check-input"
            })
        }


class AuthorizedPickupPersonForm(forms.ModelForm):
    """Form for parents to manage authorized pickup persons"""
    
    class Meta:
        model = AuthorizedPickupPerson
        fields = [
            "first_name", "last_name", "relationship", "phone", "email",
            "id_requirements", "is_emergency_contact", "is_active"
        ]
        widgets = {
            "first_name": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "First Name"
            }),
            "last_name": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Last Name"
            }),
            "relationship": forms.Select(attrs={
                "class": "form-select"
            }),
            "phone": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "(555) 123-4567"
            }),
            "email": forms.EmailInput(attrs={
                "class": "form-control",
                "placeholder": "email@example.com"
            }),
            "id_requirements": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 3,
                "placeholder": "Special ID requirements or notes for pickup verification"
            }),
            "is_emergency_contact": forms.CheckboxInput(attrs={
                "class": "form-check-input"
            }),
            "is_active": forms.CheckboxInput(attrs={
                "class": "form-check-input"
            })
        }


class MedicalInformationForm(forms.ModelForm):
    """Form for parents to update medical information"""
    
    class Meta:
        model = MedicalInformation
        fields = [
            "allergies", "medical_conditions", "medications",
            "primary_physician", "primary_physician_phone", "preferred_hospital",
            "insurance_provider", "dietary_restrictions", "physical_limitations",
            "emergency_action_plan", "can_self_medicate"
        ]
        widgets = {
            "allergies": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 3,
                "placeholder": "List all known allergies and severity"
            }),
            "medical_conditions": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 3,
                "placeholder": "Ongoing medical conditions (asthma, diabetes, etc.)"
            }),
            "medications": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 3,
                "placeholder": "Current medications and dosages"
            }),
            "primary_physician": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Child's primary physician name"
            }),
            "primary_physician_phone": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "(555) 123-4567"
            }),
            "preferred_hospital": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Preferred hospital name"
            }),
            "insurance_provider": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Health insurance provider"
            }),
            "dietary_restrictions": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 3,
                "placeholder": "Food allergies, dietary restrictions, or special meal requirements"
            }),
            "physical_limitations": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 3,
                "placeholder": "Physical limitations or accommodations needed"
            }),
            "emergency_action_plan": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 4,
                "placeholder": "Specific emergency procedures for this student"
            }),
            "can_self_medicate": forms.CheckboxInput(attrs={
                "class": "form-check-input"
            })
        }
