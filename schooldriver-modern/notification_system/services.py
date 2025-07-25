"""
Notification service for handling email, SMS, and push notifications
"""

import logging
from typing import List, Dict, Any, Optional
from django.conf import settings
from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.template import Template, Context
from django.utils import timezone
import json
import requests

# Optional Twilio import
try:
    from twilio.rest import Client as TwilioClient
    from twilio.base.exceptions import TwilioException
    TWILIO_AVAILABLE = True
except ImportError:
    TwilioClient = None
    TwilioException = Exception
    TWILIO_AVAILABLE = False

from .models import (
    Notification, NotificationTemplate, NotificationPreference, 
    NotificationLog, NotificationBatch
)

logger = logging.getLogger(__name__)


class NotificationService:
    """Centralized notification service"""
    
    def __init__(self):
        self.twilio_client = self._get_twilio_client()
        self.push_service = PushNotificationService()
    
    def _get_twilio_client(self):
        """Initialize Twilio client if credentials are available"""
        if not TWILIO_AVAILABLE:
            logger.warning("Twilio package not installed. SMS notifications disabled.")
            return None
            
        try:
            account_sid = getattr(settings, 'TWILIO_ACCOUNT_SID', None)
            auth_token = getattr(settings, 'TWILIO_AUTH_TOKEN', None)
            
            if account_sid and auth_token:
                return TwilioClient(account_sid, auth_token)
        except Exception as e:
            logger.warning(f"Twilio client initialization failed: {e}")
        
        return None
    
    def send_notification(self, 
                         recipient, 
                         template_name: str, 
                         context: Dict[str, Any],
                         delivery_methods: Optional[List[str]] = None,
                         priority: str = 'normal',
                         related_student=None,
                         schedule_for=None) -> List[Notification]:
        """
        Send notification using specified template and delivery methods
        
        Args:
            recipient: User object
            template_name: Name of notification template
            context: Variables for template rendering
            delivery_methods: List of delivery methods ['email', 'sms', 'push']
            priority: Notification priority
            related_student: Student object if applicable
            schedule_for: DateTime to schedule notification
        
        Returns:
            List of created Notification objects
        """
        try:
            # Get template
            template = NotificationTemplate.objects.get(name=template_name, is_active=True)
        except NotificationTemplate.DoesNotExist:
            logger.error(f"Template '{template_name}' not found")
            return []
        
        # Get user preferences
        try:
            preferences = recipient.notification_preferences
        except NotificationPreference.DoesNotExist:
            # Create default preferences
            preferences = NotificationPreference.objects.create(user=recipient)
        
        # Determine delivery methods based on preferences
        if delivery_methods is None:
            delivery_methods = self._get_preferred_delivery_methods(preferences, template.category)
        
        notifications = []
        
        for method in delivery_methods:
            notification = self._create_notification(
                recipient=recipient,
                template=template,
                context=context,
                delivery_method=method,
                priority=priority,
                related_student=related_student,
                schedule_for=schedule_for
            )
            
            if notification:
                notifications.append(notification)
                
                # Send immediately if not scheduled
                if not schedule_for:
                    self._send_notification(notification)
        
        return notifications
    
    def _get_preferred_delivery_methods(self, preferences: NotificationPreference, category: str) -> List[str]:
        """Get preferred delivery methods based on user preferences and category"""
        
        # Map category to preference field
        category_mapping = {
            'grade': (preferences.grade_frequency, preferences.grade_delivery),
            'attendance': (preferences.attendance_frequency, preferences.attendance_delivery),
            'assignment': (preferences.assignment_frequency, preferences.assignment_delivery),
            'emergency': (preferences.emergency_frequency, preferences.emergency_delivery),
            'announcement': (preferences.announcement_frequency, preferences.announcement_delivery),
            'message': (preferences.message_frequency, preferences.message_delivery),
        }
        
        frequency, delivery = category_mapping.get(category, ('immediate', 'email'))
        
        # Skip if disabled
        if frequency == 'disabled':
            return []
        
        # Convert delivery preference to method list
        delivery_map = {
            'email': ['email'],
            'sms': ['sms'],
            'push': ['push'],
            'email_sms': ['email', 'sms'],
            'email_push': ['email', 'push'],
            'sms_push': ['sms', 'push'],
            'all': ['email', 'sms', 'push'],
        }
        
        return delivery_map.get(delivery, ['email'])
    
    def _create_notification(self, recipient, template, context, delivery_method, 
                           priority, related_student, schedule_for) -> Optional[Notification]:
        """Create notification record"""
        
        try:
            # Render template content
            rendered_content = self._render_template(template, context, delivery_method)
            
            notification = Notification.objects.create(
                recipient=recipient,
                title=rendered_content['title'],
                message=rendered_content['message'],
                category=template.category,
                priority=priority,
                delivery_method=delivery_method,
                related_student=related_student,
                scheduled_for=schedule_for,
                metadata=context
            )
            
            return notification
            
        except Exception as e:
            logger.error(f"Failed to create notification: {e}")
            return None
    
    def _render_template(self, template: NotificationTemplate, context: Dict[str, Any], method: str) -> Dict[str, str]:
        """Render template content for specific delivery method"""
        
        django_context = Context(context)
        
        if method == 'email':
            subject = Template(template.email_subject).render(django_context)
            message = Template(template.email_body).render(django_context)
            return {'title': subject, 'message': message}
            
        elif method == 'sms':
            message = Template(template.sms_body).render(django_context)
            return {'title': 'SMS', 'message': message}
            
        elif method == 'push':
            title = Template(template.push_title).render(django_context)
            message = Template(template.push_body).render(django_context)
            return {'title': title, 'message': message}
        
        return {'title': 'Notification', 'message': 'No content'}
    
    def _send_notification(self, notification: Notification) -> bool:
        """Send individual notification"""
        
        try:
            if notification.delivery_method == 'email':
                return self._send_email(notification)
            elif notification.delivery_method == 'sms':
                return self._send_sms(notification)
            elif notification.delivery_method == 'push':
                return self._send_push(notification)
            elif notification.delivery_method == 'in_app':
                return self._send_in_app(notification)
            
        except Exception as e:
            self._log_notification_error(notification, 'send_failed', str(e))
            return False
        
        return False
    
    def _send_email(self, notification: Notification) -> bool:
        """Send email notification"""
        
        try:
            # Get template for HTML email
            template_obj = NotificationTemplate.objects.get(category=notification.category)
            
            # Create email
            email = EmailMultiAlternatives(
                subject=notification.title,
                body=notification.message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[notification.recipient.email]
            )
            
            # Add HTML version if available
            if template_obj.email_html_body:
                html_content = Template(template_obj.email_html_body).render(
                    Context(notification.metadata)
                )
                email.attach_alternative(html_content, "text/html")
            
            email.send()
            
            # Update notification status
            notification.status = 'sent'
            notification.sent_at = timezone.now()
            notification.save()
            
            self._log_notification_action(notification, 'email_sent', 'Email sent successfully')
            return True
            
        except Exception as e:
            self._log_notification_error(notification, 'email_failed', str(e))
            notification.status = 'failed'
            notification.save()
            return False
    
    def _send_sms(self, notification: Notification) -> bool:
        """Send SMS notification"""
        
        if not self.twilio_client:
            self._log_notification_error(notification, 'sms_failed', 'Twilio not configured')
            return False
        
        try:
            # Get user's phone number
            preferences = notification.recipient.notification_preferences
            phone_number = preferences.phone_number
            
            if not phone_number:
                self._log_notification_error(notification, 'sms_failed', 'No phone number configured')
                return False
            
            # Send SMS
            message = self.twilio_client.messages.create(
                body=notification.message,
                from_=getattr(settings, 'TWILIO_PHONE_NUMBER', None),
                to=phone_number
            )
            
            # Update notification status
            notification.status = 'sent'
            notification.sent_at = timezone.now()
            notification.save()
            
            self._log_notification_action(
                notification, 
                'sms_sent', 
                f'SMS sent successfully. SID: {message.sid}'
            )
            return True
            
        except TwilioException as e:
            self._log_notification_error(notification, 'sms_failed', f'Twilio error: {e}')
            notification.status = 'failed'
            notification.save()
            return False
        except Exception as e:
            self._log_notification_error(notification, 'sms_failed', str(e))
            notification.status = 'failed'
            notification.save()
            return False
    
    def _send_push(self, notification: Notification) -> bool:
        """Send push notification"""
        
        try:
            preferences = notification.recipient.notification_preferences
            push_token = preferences.push_token
            
            if not push_token:
                self._log_notification_error(notification, 'push_failed', 'No push token configured')
                return False
            
            success = self.push_service.send_push_notification(
                token=push_token,
                title=notification.title,
                body=notification.message,
                data=notification.metadata
            )
            
            if success:
                notification.status = 'sent'
                notification.sent_at = timezone.now()
                notification.save()
                self._log_notification_action(notification, 'push_sent', 'Push notification sent')
                return True
            else:
                self._log_notification_error(notification, 'push_failed', 'Push service failed')
                return False
                
        except Exception as e:
            self._log_notification_error(notification, 'push_failed', str(e))
            notification.status = 'failed'
            notification.save()
            return False
    
    def _send_in_app(self, notification: Notification) -> bool:
        """Send in-app notification (just mark as sent since it's stored)"""
        notification.status = 'sent'
        notification.sent_at = timezone.now()
        notification.save()
        
        self._log_notification_action(notification, 'in_app_created', 'In-app notification created')
        return True
    
    def _log_notification_action(self, notification: Notification, action: str, details: str):
        """Log successful notification action"""
        NotificationLog.objects.create(
            notification=notification,
            action=action,
            details=details
        )
    
    def _log_notification_error(self, notification: Notification, action: str, error: str):
        """Log notification error"""
        NotificationLog.objects.create(
            notification=notification,
            action=action,
            error_message=error
        )
        logger.error(f"Notification {notification.id} {action}: {error}")
    
    def send_batch_notification(self, batch: NotificationBatch) -> bool:
        """Send batch notification"""
        # This would implement batch sending logic
        # For now, just mark as sent
        batch.status = 'completed'
        batch.completed_at = timezone.now()
        batch.save()
        return True
    
    def process_scheduled_notifications(self):
        """Process notifications scheduled for sending"""
        scheduled_notifications = Notification.objects.filter(
            status='pending',
            scheduled_for__lte=timezone.now()
        )
        
        for notification in scheduled_notifications:
            self._send_notification(notification)


class PushNotificationService:
    """Handle push notifications using Firebase or similar service"""
    
    def __init__(self):
        self.fcm_key = getattr(settings, 'FCM_SERVER_KEY', None)
    
    def send_push_notification(self, token: str, title: str, body: str, data: Dict = None) -> bool:
        """Send push notification via FCM"""
        
        if not self.fcm_key:
            logger.warning("FCM server key not configured")
            return False
        
        url = "https://fcm.googleapis.com/fcm/send"
        
        headers = {
            "Authorization": f"key={self.fcm_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "to": token,
            "notification": {
                "title": title,
                "body": body
            },
            "data": data or {}
        }
        
        try:
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            
            result = response.json()
            if result.get('success', 0) > 0:
                logger.info(f"Push notification sent successfully: {result}")
                return True
            else:
                logger.error(f"Push notification failed: {result}")
                return False
                
        except requests.RequestException as e:
            logger.error(f"Failed to send push notification: {e}")
            return False


# Convenience functions for common notifications

def send_grade_notification(student, grade_data):
    """Send grade-related notification to parents"""
    service = NotificationService()
    
    # Get parents
    parents = student.parent_users.all()  # Assuming this relationship exists
    
    for parent in parents:
        service.send_notification(
            recipient=parent,
            template_name='new_grade_posted',
            context={
                'student_name': student.full_name,
                'subject': grade_data.get('subject'),
                'grade': grade_data.get('grade'),
                'assignment': grade_data.get('assignment'),
                'teacher': grade_data.get('teacher'),
            },
            related_student=student,
            priority='normal'
        )


def send_attendance_alert(student, attendance_data):
    """Send attendance alert to parents"""
    service = NotificationService()
    
    parents = student.parent_users.all()
    
    for parent in parents:
        service.send_notification(
            recipient=parent,
            template_name='attendance_alert',
            context={
                'student_name': student.full_name,
                'date': attendance_data.get('date'),
                'status': attendance_data.get('status'),
                'period': attendance_data.get('period'),
            },
            related_student=student,
            priority='high'
        )


def send_emergency_notification(recipients, message, title="Emergency Alert"):
    """Send emergency notification to all recipients"""
    service = NotificationService()
    
    for recipient in recipients:
        service.send_notification(
            recipient=recipient,
            template_name='emergency_alert',
            context={
                'message': message,
                'title': title,
                'timestamp': timezone.now(),
            },
            delivery_methods=['email', 'sms', 'push'],  # Force all methods for emergencies
            priority='emergency'
        )


def send_conference_confirmation(conference):
    """Send conference booking confirmation"""
    service = NotificationService()
    
    # Send to parent
    service.send_notification(
        recipient=conference.parent,
        template_name='conference_confirmation',
        context={
            'teacher_name': conference.teacher.get_full_name(),
            'student_name': conference.student.full_name,
            'date': conference.date,
            'time': conference.start_time,
            'location': conference.location,
            'virtual_link': conference.virtual_meeting_link,
        },
        related_student=conference.student,
        priority='normal'
    )
    
    # Send to teacher
    service.send_notification(
        recipient=conference.teacher,
        template_name='conference_confirmation_teacher',
        context={
            'parent_name': conference.parent.get_full_name(),
            'student_name': conference.student.full_name,
            'date': conference.date,
            'time': conference.start_time,
            'location': conference.location,
        },
        related_student=conference.student,
        priority='normal'
    )


def send_conference_reschedule_notification(old_conference, new_conference):
    """Send notification about conference rescheduling"""
    service = NotificationService()
    
    # Send to parent
    service.send_notification(
        recipient=new_conference.parent,
        template_name='conference_rescheduled',
        context={
            'teacher_name': new_conference.teacher.get_full_name(),
            'student_name': new_conference.student.full_name,
            'old_date': old_conference.date,
            'old_time': old_conference.start_time,
            'new_date': new_conference.date,
            'new_time': new_conference.start_time,
            'location': new_conference.location,
        },
        related_student=new_conference.student,
        priority='high'
    )
