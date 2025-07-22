from django.contrib.auth.models import User
from django.db import models
import uuid
import os


def user_avatar_path(instance, filename):
    """Generate path for user avatar uploads"""
    ext = filename.split('.')[-1]
    filename = f"{instance.user.id}_avatar.{ext}"
    return os.path.join('avatars', filename)


class UserProfile(models.Model):
    """User profile model for additional user information"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    avatar = models.ImageField(upload_to=user_avatar_path, blank=True, null=True)
    
    # Personal Information
    date_of_birth = models.DateField(blank=True, null=True)
    phone_number = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    
    # Emergency Contacts
    emergency_contact_1_name = models.CharField(max_length=100, blank=True, verbose_name="Primary Contact Name")
    emergency_contact_1_relationship = models.CharField(max_length=50, blank=True, verbose_name="Primary Contact Relationship")
    emergency_contact_1_phone = models.CharField(max_length=20, blank=True, verbose_name="Primary Contact Phone")
    
    emergency_contact_2_name = models.CharField(max_length=100, blank=True, verbose_name="Secondary Contact Name")
    emergency_contact_2_relationship = models.CharField(max_length=50, blank=True, verbose_name="Secondary Contact Relationship")
    emergency_contact_2_phone = models.CharField(max_length=20, blank=True, verbose_name="Secondary Contact Phone")
    
    emergency_address = models.TextField(blank=True, verbose_name="Emergency Contact Address")
    
    # Account Settings
    email_notifications = models.BooleanField(default=True, verbose_name="Email Notifications")
    sms_notifications = models.BooleanField(default=False, verbose_name="SMS Notifications")
    parent_portal_access = models.BooleanField(default=True, verbose_name="Parent Portal Access")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} Profile"

    @property
    def avatar_url(self):
        """Return avatar URL or default placeholder"""
        if self.avatar and hasattr(self.avatar, 'url'):
            return self.avatar.url
        return '/static/img/default-avatar.png'  # Default avatar placeholder


# Signal to create profile when user is created
from django.db.models.signals import post_save
from django.dispatch import receiver


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Create UserProfile when User is created"""
    if created:
        UserProfile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Save UserProfile when User is saved"""
    if hasattr(instance, 'profile'):
        instance.profile.save()


class SecurityEvent(models.Model):
    """Security audit log model"""
    EVENT_TYPES = [
        ('LOGIN_SUCCESS', 'Successful Login'),
        ('LOGIN_FAILED', 'Failed Login Attempt'),
        ('PASSWORD_CHANGE', 'Password Changed'),
        ('ACCOUNT_LOCKED', 'Account Locked'),
        ('ACCOUNT_UNLOCKED', 'Account Unlocked'),
        ('LOGOUT', 'Logout'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    username = models.CharField(max_length=150, help_text="Username attempted (for failed logins)")
    event_type = models.CharField(max_length=20, choices=EVENT_TYPES)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    details = models.JSONField(default=dict, blank=True)
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user', 'event_type']),
            models.Index(fields=['username', 'event_type']),
            models.Index(fields=['timestamp']),
            models.Index(fields=['ip_address']),
        ]
    
    def __str__(self):
        user_identifier = self.user.username if self.user else self.username
        return f"{self.get_event_type_display()} - {user_identifier} at {self.timestamp}"
    
    @classmethod
    def log_event(cls, event_type, user=None, username=None, request=None, **extra_details):
        """Helper method to log security events"""
        ip_address = None
        user_agent = ''
        
        if request:
            # Get real IP address
            x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
            if x_forwarded_for:
                ip_address = x_forwarded_for.split(',')[0].strip()
            else:
                ip_address = request.META.get('REMOTE_ADDR')
            
            user_agent = request.META.get('HTTP_USER_AGENT', '')
        
        if not username and user:
            username = user.username
            
        return cls.objects.create(
            user=user,
            username=username,
            event_type=event_type,
            ip_address=ip_address,
            user_agent=user_agent,
            details=extra_details
        )
