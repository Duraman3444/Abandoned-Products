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
