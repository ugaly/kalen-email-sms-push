import logging
import requests
from django.core.mail import send_mail
from django.conf import settings
from django.template import Template, Context
from typing import Dict, Any, Optional
from requests.auth import HTTPBasicAuth
from django.core.mail import EmailMultiAlternatives
from .template_engine import EmailTemplateEngine

from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.utils import timezone
from datetime import datetime

logger = logging.getLogger(__name__)

# class EmailService:
#     """Service for sending email notifications"""
    
#     def send_email(self, to_email: str, subject: str, message: str, 
#                    metadata: Dict[str, Any] = None) -> bool:
#         """
#         Send email notification
        
#         Args:
#             to_email: Recipient email address
#             subject: Email subject
#             message: Email message content
#             metadata: Additional metadata for the email
            
#         Returns:
#             bool: True if email was sent successfully, False otherwise
#         """
#         try:
#             # Process template variables if present
#             if metadata and 'template_vars' in metadata:
#                 template = Template(message)
#                 context = Context(metadata['template_vars'])
#                 message = template.render(context)
                
#                 if subject:
#                     subject_template = Template(subject)
#                     subject = subject_template.render(context)
            
#             # Send email
#             send_mail(
#                 subject=subject,
#                 message=message,
#                 from_email=settings.DEFAULT_FROM_EMAIL,
#                 recipient_list=[to_email],
#                 fail_silently=False,
#             )
            
#             logger.info(f"Email sent successfully to {to_email}")
#             return True
            
#         except Exception as e:
#             logger.error(f"Failed to send email to {to_email}: {str(e)}")
#             return False



class EmailService:
    """Service for sending email notifications"""
    
    def send_email(self, to_email: str, subject: str, message: str, use_html: str, first_name: Optional[str] = None, last_name: Optional[str] = None, templete_content: Optional[str] = None, primary_color: Optional[str] = None,
                   metadata: Dict[str, Any] = None) -> bool:
        
        """
        Send email notification
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            message: Email message content
            metadata: Additional metadata for the email
            
        Returns:
            bool: True if email was sent successfully, False otherwise
        """
        try:
            metadata = metadata or {}
            # use_html = metadata.get('use_html', True)
            logger.info(f"Sending email to {to_email} with subject: {subject}")
            logger.info(f"Email metadata: {metadata}")
            # html_template = metadata.get('html_template', 'base_email_template.html')
            html_template = f"{use_html}.html" if use_html else 'base_email_template.html'
            
            template_vars = metadata.get('template_vars', {})

            print("Template Variables------------------:", template_vars)
            
            template_vars.update({
                'subject': subject,
                'message': message,
                'current_year': datetime.now().year,
                'company_name': metadata.get('company_name', settings.COMPANY_NAME),
                'logo_url': metadata.get('logo_url', settings.COMPANY_LOGO),
                'support_email': metadata.get('support_email', settings.SUPPORT_EMAIL),
                'social_facebook': metadata.get('social_facebook', settings.SOCIAL_FACEBOOK),
                'social_twitter': metadata.get('social_twitter', settings.SOCIAL_TWITTER),
                'first_name': first_name,
                'last_name': last_name,
                'templete_content': templete_content,
                'primary_color': primary_color
            })
            
            if use_html:
                logger.info("Using HTML template for email", html_template)
                html_content = render_to_string(
                    # f"notifications/templates/{html_template}", 
                    f"notifications/{html_template}",
                    template_vars
                )
                
                plain_text = strip_tags(html_content)
                
                email = EmailMultiAlternatives(
                    subject=subject,
                    body=plain_text,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    to=[to_email]
                )
                email.attach_alternative(html_content, "text/html")
                email.send()
            else:
                if template_vars:
                    template = Template(message)
                    context = Context(template_vars)
                    message = template.render(context)
                    
                    if subject:
                        subject_template = Template(subject)
                        subject = subject_template.render(context)
                
                send_mail(
                    subject=subject,
                    message=message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[to_email],
                    fail_silently=False,
                )
            
            logger.info(f"Email sent successfully to {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {str(e)}")
            return False



class SMSService:
    """Service for sending SMS notifications using Beam"""
    
    def __init__(self):
        self.username = settings.BEEM_USERNAME
        self.password = settings.BEEM_PASSWORD
        self.api_url = settings.BEEM_API_URL or "https://apisms.beem.africa/v1/send"
        self.source_addr = settings.BEEM_SOURCE_NAME or "SILENTOCEAN"
        
    
    def send_sms(self, to_phone: str, message: str,
                 metadata: Dict[str, Any] = None) -> bool:
        """
        Send SMS notification using Beem API

        Args:
            to_phone: Recipient phone number
            message: SMS message content
            metadata: Optional template vars, reference, callback_url

        Returns:
            bool: True if SMS was sent successfully, False otherwise
        """
        try:
            if not self.username or not self.password:
                logger.error("Beem credentials not configured")
                return False

            if not to_phone:
                logger.error("No phone number provided for SMS")
                return False

            if not to_phone.startswith("+255"):
                to_phone = "+255" + to_phone.lstrip("0")

            if metadata and 'template_vars' in metadata:
                template = Template(message)
                context = Context(metadata['template_vars'])
                message = template.render(context)

            payload = {
                "source_addr": self.source_addr,
                "encoding": 0,
                "message": message,
                "recipients": [
                    {
                        "recipient_id": 1,
                        "dest_addr": to_phone
                    }
                ]
            }

            response = requests.post(
                self.api_url,
                json=payload,
                auth=HTTPBasicAuth(self.username, self.password),
                timeout=30
            )

            if response.status_code == 200:
                logger.info(f"SMS sent successfully to {to_phone}")
                return True
            else:
                logger.error(f"Failed to send SMS to {to_phone}: {response.status_code} - {response.text}")
                return False

        except requests.exceptions.RequestException as e:
            logger.error(f"Network error sending SMS to {to_phone}: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error sending SMS to {to_phone}: {str(e)}")
            return False
        


class PushNotificationService:
    """Service for sending push notifications"""
    
    def send_push(self, user, title: str, message: str, 
                  metadata: Dict[str, Any] = None) -> bool:
        """
        Send push notification
        
        Args:
            user: User object
            title: Notification title
            message: Notification message
            metadata: Additional metadata for the notification
            
        Returns:
            bool: True if push notification was sent successfully, False otherwise
        """
        try:
            # This is a placeholder implementation
            # In a real application, you would integrate with services like:
            # - Firebase Cloud Messaging (FCM)
            # - Apple Push Notification Service (APNs)
            # - OneSignal
            # - Pusher
            
            logger.info(f"Push notification sent to user {user.id}: {title}")
            
            # For now, we'll just log the notification
            # You would replace this with actual push notification logic
            return True
            
        except Exception as e:
            logger.error(f"Failed to send push notification to user {user.id}: {str(e)}")
            return False

class NotificationService:
    """Main service for handling notifications"""
    
    def __init__(self):
        self.email_service = EmailService()
        self.sms_service = SMSService()
        self.push_service = PushNotificationService()
    
    def send_notification(self, notification):
        print(
            f"Sending notification {notification.id} of type {notification.notification_type}"
        )
        """
        Send notification based on its type
        
        Args:
            notification: Notification model instance
            
        Returns:
            bool: True if notification was sent successfully, False otherwise
        """
        try:
            if notification.notification_type == 'email':
                return self.email_service.send_email(
                    to_email=notification.recipient_email or notification.user.email,
                    subject=notification.subject,
                    message=notification.message,
                    metadata=notification.metadata
                )
            elif notification.notification_type == 'sms':
                return self.sms_service.send_sms(
                    to_phone=notification.recipient_phone or notification.user.phone_number,
                    message=notification.message,
                    metadata=notification.metadata
                )
            elif notification.notification_type == 'push':
                return self.push_service.send_push(
                    user=notification.user,
                    title=notification.subject,
                    message=notification.message,
                    metadata=notification.metadata
                )
            else:
                logger.error(f"Unknown notification type: {notification.notification_type}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to send notification {notification.id}: {str(e)}")
            return False
    
    def create_and_send_notification(self, user, category, notification_type, 
                                   subject, message, metadata=None, 
                                   scheduled_at=None, template=None):
        """
        Create and send a notification
        
        Args:
            user: User object
            category: NotificationCategory object
            notification_type: Type of notification ('email', 'sms', 'push')
            subject: Notification subject
            message: Notification message
            metadata: Additional metadata
            scheduled_at: When to send the notification
            template: NotificationTemplate object
            
        Returns:
            Notification: Created notification object
        """
        from .models import Notification
        from django.utils import timezone
        
        notification = Notification.objects.create(
            user=user,
            category=category,
            template=template,
            notification_type=notification_type,
            subject=subject,
            message=message,
            metadata=metadata or {},
            scheduled_at=scheduled_at or timezone.now(),
            recipient_email=user.email if notification_type == 'email' else None,
            recipient_phone=user.phone_number if notification_type == 'sms' else None,
        )
        
        if not scheduled_at or scheduled_at <= timezone.now():
            from .tasks import (
                send_email_notification, 
                send_sms_notification, 
                send_push_notification
            )
            
            if notification_type == 'email':
                print("Sending email notification")
                print("Recipient Email------------------:", notification.recipient_email)
                send_email_notification.delay(str(notification.id))
            elif notification_type == 'sms':
                print("Sending SMS notification")
                print("Recipient Phone------------------:", notification.recipient_phone)
                send_sms_notification.delay(str(notification.id))
            elif notification_type == 'push':
                print("Sending push notification")
                print("Recipient User ID------------------:", notification.user.id)
                send_push_notification.delay(str(notification.id))
        
        return notification
