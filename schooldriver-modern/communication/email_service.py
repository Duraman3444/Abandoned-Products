"""
Enhanced email service for school communications
"""
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import List, Optional, Dict, Any
from django.conf import settings
from django.core.mail import send_mail, send_mass_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.contrib.auth.models import User

logger = logging.getLogger(__name__)


class SchoolEmailService:
    """Enhanced email service for school communications"""
    
    def __init__(self):
        self.smtp_host = getattr(settings, 'SMTP_HOST', 'localhost')
        self.smtp_port = getattr(settings, 'SMTP_PORT', 587)
        self.smtp_user = getattr(settings, 'SMTP_USER', '')
        self.smtp_password = getattr(settings, 'SMTP_PASSWORD', '')
        self.use_tls = getattr(settings, 'SMTP_USE_TLS', True)
        self.from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@school.edu')
        
    def send_announcement_email(
        self, 
        announcement, 
        recipients: List[User],
        template_name: str = 'communication/announcement_email.html'
    ) -> Dict[str, Any]:
        """
        Send an announcement via email to specified recipients
        """
        results = {
            'sent': 0,
            'failed': 0,
            'errors': []
        }
        
        try:
            # Prepare email content
            context = {
                'announcement': announcement,
                'school_name': getattr(settings, 'SCHOOL_NAME', 'School'),
                'school_url': getattr(settings, 'SCHOOL_URL', 'https://school.edu'),
            }
            
            html_content = render_to_string(template_name, context)
            text_content = strip_tags(html_content)
            
            # Prepare recipient emails
            recipient_emails = [user.email for user in recipients if user.email]
            
            if not recipient_emails:
                logger.warning(f"No valid email addresses found for announcement: {announcement.title}")
                return results
            
            # Send emails
            messages = []
            for email in recipient_emails:
                messages.append((
                    f"[{getattr(settings, 'SCHOOL_NAME', 'School')}] {announcement.title}",
                    text_content,
                    self.from_email,
                    [email]
                ))
            
            # Send mass email
            send_mass_mail(messages, fail_silently=False)
            results['sent'] = len(recipient_emails)
            
            logger.info(f"Sent announcement email '{announcement.title}' to {len(recipient_emails)} recipients")
            
        except Exception as e:
            logger.error(f"Failed to send announcement email: {str(e)}")
            results['errors'].append(str(e))
            results['failed'] = len(recipients)
            
        return results
    
    def send_progress_note_email(
        self, 
        progress_note, 
        parent_users: List[User],
        template_name: str = 'communication/progress_note_email.html'
    ) -> Dict[str, Any]:
        """
        Send a progress note via email to parents
        """
        results = {
            'sent': 0,
            'failed': 0,
            'errors': []
        }
        
        try:
            # Prepare email content
            context = {
                'progress_note': progress_note,
                'student': progress_note.student,
                'teacher': progress_note.teacher,
                'school_name': getattr(settings, 'SCHOOL_NAME', 'School'),
            }
            
            html_content = render_to_string(template_name, context)
            text_content = strip_tags(html_content)
            
            # Send to parent emails
            for parent in parent_users:
                if parent.email:
                    try:
                        send_mail(
                            subject=f"Progress Note: {progress_note.student.get_full_name()} - {progress_note.title}",
                            message=text_content,
                            from_email=self.from_email,
                            recipient_list=[parent.email],
                            html_message=html_content,
                            fail_silently=False
                        )
                        results['sent'] += 1
                    except Exception as e:
                        logger.error(f"Failed to send progress note email to {parent.email}: {str(e)}")
                        results['errors'].append(f"{parent.email}: {str(e)}")
                        results['failed'] += 1
                        
            logger.info(f"Sent progress note '{progress_note.title}' to {results['sent']} parents")
            
        except Exception as e:
            logger.error(f"Failed to send progress note emails: {str(e)}")
            results['errors'].append(str(e))
            results['failed'] = len(parent_users)
            
        return results
    
    def send_direct_message_email(
        self, 
        message, 
        template_name: str = 'communication/direct_message_email.html'
    ) -> bool:
        """
        Send a direct message via email
        """
        try:
            if not message.recipient.email:
                logger.warning(f"No email address for user: {message.recipient.username}")
                return False
                
            context = {
                'message': message,
                'sender': message.sender,
                'recipient': message.recipient,
                'school_name': getattr(settings, 'SCHOOL_NAME', 'School'),
            }
            
            html_content = render_to_string(template_name, context)
            text_content = strip_tags(html_content)
            
            send_mail(
                subject=f"Message from {message.sender.get_full_name()}: {message.subject}",
                message=text_content,
                from_email=self.from_email,
                recipient_list=[message.recipient.email],
                html_message=html_content,
                fail_silently=False
            )
            
            logger.info(f"Sent direct message email to {message.recipient.email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send direct message email: {str(e)}")
            return False
    
    def send_custom_email(
        self, 
        subject: str,
        content: str,
        recipients: List[str],
        template_name: Optional[str] = None,
        context: Optional[Dict] = None,
        attachments: Optional[List] = None
    ) -> Dict[str, Any]:
        """
        Send a custom email with optional template and attachments
        """
        results = {
            'sent': 0,
            'failed': 0,
            'errors': []
        }
        
        try:
            # Prepare content
            if template_name and context:
                html_content = render_to_string(template_name, context)
                text_content = strip_tags(html_content)
            else:
                html_content = content
                text_content = strip_tags(content)
            
            # Send to each recipient
            for recipient_email in recipients:
                try:
                    if attachments:
                        # Handle attachments with MIME
                        msg = MIMEMultipart()
                        msg['From'] = self.from_email
                        msg['To'] = recipient_email
                        msg['Subject'] = subject
                        
                        msg.attach(MIMEText(html_content, 'html'))
                        
                        for attachment in attachments:
                            with open(attachment['path'], 'rb') as f:
                                part = MIMEBase('application', 'octet-stream')
                                part.set_payload(f.read())
                                encoders.encode_base64(part)
                                part.add_header(
                                    'Content-Disposition',
                                    f'attachment; filename= {attachment["name"]}'
                                )
                                msg.attach(part)
                        
                        # Send via SMTP
                        server = smtplib.SMTP(self.smtp_host, self.smtp_port)
                        if self.use_tls:
                            server.starttls()
                        if self.smtp_user and self.smtp_password:
                            server.login(self.smtp_user, self.smtp_password)
                        server.send_message(msg)
                        server.quit()
                    else:
                        # Send without attachments
                        send_mail(
                            subject=subject,
                            message=text_content,
                            from_email=self.from_email,
                            recipient_list=[recipient_email],
                            html_message=html_content,
                            fail_silently=False
                        )
                    
                    results['sent'] += 1
                    
                except Exception as e:
                    logger.error(f"Failed to send email to {recipient_email}: {str(e)}")
                    results['errors'].append(f"{recipient_email}: {str(e)}")
                    results['failed'] += 1
                    
        except Exception as e:
            logger.error(f"Failed to send custom emails: {str(e)}")
            results['errors'].append(str(e))
            results['failed'] = len(recipients)
            
        return results


# Singleton instance
email_service = SchoolEmailService()
