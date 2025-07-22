from typing import Dict, Any, Optional
from django import forms
from django.core.validators import RegexValidator, EmailValidator
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from datetime import date, timedelta
import re


class StudentProfileForm(forms.Form):
    """
    Comprehensive form for student profile editing with validation.
    """

    # Personal Information
    first_name = forms.CharField(
        max_length=30,
        required=True,
        validators=[
            RegexValidator(
                regex=r"^[a-zA-Z\s\'-\.]+$",
                message="Name can only contain letters, spaces, hyphens, apostrophes, and periods.",
            )
        ],
        widget=forms.TextInput(
            attrs={
                "class": "form-control bg-dark border-secondary text-light",
                "placeholder": "Enter your first name",
            }
        ),
    )

    last_name = forms.CharField(
        max_length=30,
        required=True,
        validators=[
            RegexValidator(
                regex=r"^[a-zA-Z\s\'-\.]+$",
                message="Name can only contain letters, spaces, hyphens, apostrophes, and periods.",
            )
        ],
        widget=forms.TextInput(
            attrs={
                "class": "form-control bg-dark border-secondary text-light",
                "placeholder": "Enter your last name",
            }
        ),
    )

    email = forms.EmailField(
        required=True,
        validators=[EmailValidator(message="Please enter a valid email address.")],
        widget=forms.EmailInput(
            attrs={
                "class": "form-control bg-dark border-secondary text-light",
                "placeholder": "your.email@example.com",
            }
        ),
    )

    date_of_birth = forms.DateField(
        required=False,
        widget=forms.DateInput(
            attrs={
                "class": "form-control bg-dark border-secondary text-light",
                "type": "date",
            }
        ),
    )

    phone_number = forms.CharField(
        max_length=20,
        required=False,
        validators=[
            RegexValidator(
                regex=r"^\+?1?[-.\s]?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})$",
                message="Phone number must be in format: (555) 123-4567 or 555-123-4567",
            )
        ],
        widget=forms.TextInput(
            attrs={
                "class": "form-control bg-dark border-secondary text-light",
                "placeholder": "(555) 123-4567",
            }
        ),
    )

    address = forms.CharField(
        max_length=200,
        required=False,
        validators=[
            RegexValidator(
                regex=r"^[a-zA-Z0-9\s\',.-]+$",
                message="Address contains invalid characters.",
            )
        ],
        widget=forms.Textarea(
            attrs={
                "class": "form-control bg-dark border-secondary text-light",
                "rows": 3,
                "placeholder": "123 Main St, City, State ZIP",
            }
        ),
    )

    # Emergency Contact 1
    emergency_contact_1_name = forms.CharField(
        max_length=100,
        required=False,
        validators=[
            RegexValidator(
                regex=r"^[a-zA-Z\s\'-\.]+$",
                message="Name can only contain letters, spaces, hyphens, apostrophes, and periods.",
            )
        ],
        widget=forms.TextInput(
            attrs={
                "class": "form-control bg-dark border-secondary text-light",
                "placeholder": "Mary Anderson",
            }
        ),
    )

    emergency_contact_1_relationship = forms.ChoiceField(
        choices=[
            ("", "Select relationship"),
            ("Mother", "Mother"),
            ("Father", "Father"),
            ("Guardian", "Guardian"),
            ("Grandmother", "Grandmother"),
            ("Grandfather", "Grandfather"),
            ("Aunt", "Aunt"),
            ("Uncle", "Uncle"),
            ("Sibling", "Sibling"),
            ("Other", "Other"),
        ],
        required=False,
        widget=forms.Select(
            attrs={"class": "form-select bg-dark border-secondary text-light"}
        ),
    )

    emergency_contact_1_phone = forms.CharField(
        max_length=20,
        required=False,
        validators=[
            RegexValidator(
                regex=r"^\+?1?[-.\s]?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})$",
                message="Phone number must be in format: (555) 123-4567 or 555-123-4567",
            )
        ],
        widget=forms.TextInput(
            attrs={
                "class": "form-control bg-dark border-secondary text-light",
                "placeholder": "(555) 987-6543",
            }
        ),
    )

    # Emergency Contact 2
    emergency_contact_2_name = forms.CharField(
        max_length=100,
        required=False,
        validators=[
            RegexValidator(
                regex=r"^[a-zA-Z\s\'-\.]+$",
                message="Name can only contain letters, spaces, hyphens, apostrophes, and periods.",
            )
        ],
        widget=forms.TextInput(
            attrs={
                "class": "form-control bg-dark border-secondary text-light",
                "placeholder": "David Johnson",
            }
        ),
    )

    emergency_contact_2_relationship = forms.ChoiceField(
        choices=[
            ("", "Select relationship"),
            ("Mother", "Mother"),
            ("Father", "Father"),
            ("Guardian", "Guardian"),
            ("Grandmother", "Grandmother"),
            ("Grandfather", "Grandfather"),
            ("Aunt", "Aunt"),
            ("Uncle", "Uncle"),
            ("Sibling", "Sibling"),
            ("Other", "Other"),
        ],
        required=False,
        widget=forms.Select(
            attrs={"class": "form-select bg-dark border-secondary text-light"}
        ),
    )

    emergency_contact_2_phone = forms.CharField(
        max_length=20,
        required=False,
        validators=[
            RegexValidator(
                regex=r"^\+?1?[-.\s]?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})$",
                message="Phone number must be in format: (555) 123-4567 or 555-123-4567",
            )
        ],
        widget=forms.TextInput(
            attrs={
                "class": "form-control bg-dark border-secondary text-light",
                "placeholder": "(555) 987-6544",
            }
        ),
    )

    emergency_address = forms.CharField(
        max_length=200,
        required=False,
        validators=[
            RegexValidator(
                regex=r"^[a-zA-Z0-9\s\',.-]+$",
                message="Address contains invalid characters.",
            )
        ],
        widget=forms.Textarea(
            attrs={
                "class": "form-control bg-dark border-secondary text-light",
                "rows": 3,
                "placeholder": "123 Emergency Street, City, State ZIP",
            }
        ),
    )

    # Account Settings
    email_notifications = forms.BooleanField(
        required=False, widget=forms.CheckboxInput(attrs={"class": "form-check-input"})
    )

    sms_notifications = forms.BooleanField(
        required=False, widget=forms.CheckboxInput(attrs={"class": "form-check-input"})
    )

    parent_portal_access = forms.BooleanField(
        required=False, widget=forms.CheckboxInput(attrs={"class": "form-check-input"})
    )

    def clean_email(self) -> str:
        """Custom validation for email uniqueness."""
        email = self.cleaned_data.get("email")
        if email:
            # Check if email is already in use by another user
            existing_user = (
                User.objects.filter(email=email)
                .exclude(pk=getattr(self, "user_pk", None))
                .first()
            )
            if existing_user:
                raise ValidationError(
                    "This email address is already in use by another account."
                )
        return email

    def clean_date_of_birth(self):
        """Custom validation for date of birth."""
        dob = self.cleaned_data.get("date_of_birth")
        if dob:
            today = date.today()

            # Check if date is not in the future
            if dob > today:
                raise ValidationError("Date of birth cannot be in the future.")

            # Check reasonable age limits (5-100 years)
            min_date = today - timedelta(days=365 * 100)  # 100 years ago
            max_date = today - timedelta(days=365 * 5)  # 5 years ago

            if dob < min_date:
                raise ValidationError("Please enter a valid date of birth.")

            if dob > max_date:
                raise ValidationError("Student must be at least 5 years old.")

        return dob

    def clean_phone_number(self):
        """Normalize phone number format."""
        phone = self.cleaned_data.get("phone_number")
        if phone:
            # Remove all non-digits
            digits_only = re.sub(r"\D", "", phone)

            # Add country code if not present
            if len(digits_only) == 10:
                digits_only = "1" + digits_only

            # Format as (XXX) XXX-XXXX
            if len(digits_only) == 11 and digits_only.startswith("1"):
                area_code = digits_only[1:4]
                exchange = digits_only[4:7]
                number = digits_only[7:11]
                return f"({area_code}) {exchange}-{number}"

        return phone

    def clean_emergency_contact_1_phone(self):
        """Normalize emergency contact 1 phone number."""
        return self.clean_phone_number_generic(
            self.cleaned_data.get("emergency_contact_1_phone")
        )

    def clean_emergency_contact_2_phone(self):
        """Normalize emergency contact 2 phone number."""
        return self.clean_phone_number_generic(
            self.cleaned_data.get("emergency_contact_2_phone")
        )

    def clean_phone_number_generic(self, phone):
        """Generic phone number cleaning method."""
        if phone:
            # Remove all non-digits
            digits_only = re.sub(r"\D", "", phone)

            # Add country code if not present
            if len(digits_only) == 10:
                digits_only = "1" + digits_only

            # Format as (XXX) XXX-XXXX
            if len(digits_only) == 11 and digits_only.startswith("1"):
                area_code = digits_only[1:4]
                exchange = digits_only[4:7]
                number = digits_only[7:11]
                return f"({area_code}) {exchange}-{number}"

        return phone

    def clean(self):
        """Cross-field validation."""
        cleaned_data = super().clean()

        # Check if at least one emergency contact is provided
        ec1_name = cleaned_data.get("emergency_contact_1_name")
        ec1_phone = cleaned_data.get("emergency_contact_1_phone")
        ec2_name = cleaned_data.get("emergency_contact_2_name")
        ec2_phone = cleaned_data.get("emergency_contact_2_phone")

        # If emergency contact name is provided, phone should be provided too
        if ec1_name and not ec1_phone:
            self.add_error(
                "emergency_contact_1_phone",
                "Phone number is required when emergency contact name is provided.",
            )

        if ec2_name and not ec2_phone:
            self.add_error(
                "emergency_contact_2_phone",
                "Phone number is required when emergency contact name is provided.",
            )

        # If emergency contact phone is provided, name should be provided too
        if ec1_phone and not ec1_name:
            self.add_error(
                "emergency_contact_1_name",
                "Contact name is required when phone number is provided.",
            )

        if ec2_phone and not ec2_name:
            self.add_error(
                "emergency_contact_2_name",
                "Contact name is required when phone number is provided.",
            )

        return cleaned_data


class ContactForm(forms.Form):
    """
    Form for public contact page with comprehensive validation and spam protection.
    """

    name = forms.CharField(
        max_length=100,
        required=True,
        validators=[
            RegexValidator(
                regex=r"^[a-zA-Z\s\'-\.]+$",
                message="Name can only contain letters, spaces, hyphens, apostrophes, and periods.",
            )
        ],
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "Your full name"}
        ),
    )

    email = forms.EmailField(
        required=True,
        validators=[EmailValidator(message="Please enter a valid email address.")],
        widget=forms.EmailInput(
            attrs={"class": "form-control", "placeholder": "your.email@example.com"}
        ),
    )

    phone = forms.CharField(
        max_length=20,
        required=False,
        validators=[
            RegexValidator(
                regex=r"^\+?1?[-.\s]?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})$",
                message="Phone number must be in format: (555) 123-4567 or 555-123-4567",
            )
        ],
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "(555) 123-4567 (optional)"}
        ),
    )

    subject = forms.ChoiceField(
        choices=[
            ("", "Select a subject"),
            ("admissions", "Admissions Inquiry"),
            ("academics", "Academic Information"),
            ("support", "Technical Support"),
            ("billing", "Billing Questions"),
            ("other", "Other"),
        ],
        required=True,
        widget=forms.Select(attrs={"class": "form-select"}),
    )

    message = forms.CharField(
        min_length=10,
        max_length=1000,
        required=True,
        widget=forms.Textarea(
            attrs={
                "class": "form-control",
                "rows": 5,
                "placeholder": "Please provide details about your inquiry...",
            }
        ),
    )

    # Honeypot field for spam protection (hidden from users)
    honeypot = forms.CharField(required=False, widget=forms.HiddenInput())

    def clean_message(self):
        """Validate message content for spam and inappropriate content."""
        message = self.cleaned_data.get("message")
        if message:
            # Check for spam indicators
            spam_words = [
                "viagra",
                "casino",
                "lottery",
                "winner",
                "congratulations",
                "click here",
                "free money",
                "make money",
                "work from home",
            ]

            message_lower = message.lower()
            for spam_word in spam_words:
                if spam_word in message_lower:
                    raise ValidationError(
                        "Your message contains inappropriate content."
                    )

            # Check for excessive capitalization
            if len([c for c in message if c.isupper()]) > len(message) * 0.5:
                raise ValidationError("Please avoid excessive use of capital letters.")

            # Check for excessive links
            url_pattern = r"http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+"
            urls = re.findall(url_pattern, message)
            if len(urls) > 2:
                raise ValidationError("Messages cannot contain more than 2 links.")

        return message

    def clean_honeypot(self):
        """Check honeypot field for spam bots."""
        honeypot = self.cleaned_data.get("honeypot")
        if honeypot:
            raise ValidationError("Bot detected. Please try again.")
        return honeypot

    def clean(self):
        """Cross-field validation."""
        cleaned_data = super().clean()

        # Additional anti-spam measures
        name = cleaned_data.get("name", "")
        email = cleaned_data.get("email", "")

        # Check if name and email are too similar (potential spam)
        if name and email:
            name_clean = re.sub(r"[^a-zA-Z]", "", name.lower())
            email_prefix = email.split("@")[0].lower() if "@" in email else ""

            if name_clean == email_prefix:
                self.add_error("name", "Please provide your actual name.")

        return cleaned_data
