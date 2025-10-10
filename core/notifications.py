# core/notifications.py
# Email notification system for Phase 9

from django.core.mail import EmailMultiAlternatives, send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.utils.html import strip_tags
from celery import shared_task
import logging

logger = logging.getLogger(__name__)


class NotificationService:
    """Email notification service"""
    
    @staticmethod
    def send_email(to_emails, subject, template_name, context, from_email=None):
        """Send email with template"""
        if not from_email:
            from_email = settings.DEFAULT_FROM_EMAIL
        
        # Render HTML content
        html_content = render_to_string(template_name, context)
        text_content = strip_tags(html_content)
        
        # Create email
        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=from_email,
            to=to_emails if isinstance(to_emails, list) else [to_emails]
        )
        email.attach_alternative(html_content, "text/html")
        
        try:
            email.send()
            logger.info(f"Email sent to {to_emails}: {subject}")
            return True
        except Exception as e:
            logger.error(f"Failed to send email to {to_emails}: {str(e)}")
            return False
    
    @staticmethod
    def send_user_invitation(email, invitation_token, inviter_name, company_name):
        """Send user invitation email"""
        subject = f"Invitation to join {company_name} on CRM"
        context = {
            'email': email,
            'invitation_token': invitation_token,
            'inviter_name': inviter_name,
            'company_name': company_name,
            'invitation_url': f"{settings.FRONTEND_URL}/accept-invitation/{invitation_token}",
        }
        return NotificationService.send_email(
            to_emails=email,
            subject=subject,
            template_name='emails/user_invitation.html',
            context=context
        )
    
    @staticmethod
    def send_password_reset(email, reset_token, user_name):
        """Send password reset email"""
        subject = "Reset your password"
        context = {
            'user_name': user_name,
            'reset_token': reset_token,
            'reset_url': f"{settings.FRONTEND_URL}/reset-password/{reset_token}",
        }
        return NotificationService.send_email(
            to_emails=email,
            subject=subject,
            template_name='emails/password_reset.html',
            context=context
        )
    
    @staticmethod
    def send_account_activation(email, activation_token, user_name):
        """Send account activation email"""
        subject = "Activate your account"
        context = {
            'user_name': user_name,
            'activation_token': activation_token,
            'activation_url': f"{settings.FRONTEND_URL}/activate/{activation_token}",
        }
        return NotificationService.send_email(
            to_emails=email,
            subject=subject,
            template_name='emails/account_activation.html',
            context=context
        )
    
    @staticmethod
    def send_lead_assignment(email, lead, assigned_by):
        """Send lead assignment notification"""
        subject = f"New lead assigned: {lead.name}"
        context = {
            'lead': lead,
            'assigned_by': assigned_by,
            'lead_url': f"{settings.FRONTEND_URL}/leads/{lead.id}",
        }
        return NotificationService.send_email(
            to_emails=email,
            subject=subject,
            template_name='emails/lead_assignment.html',
            context=context
        )
    
    @staticmethod
    def send_deal_update(email, deal, update_type, updated_by):
        """Send deal update notification"""
        subject = f"Deal updated: {deal.name}"
        context = {
            'deal': deal,
            'update_type': update_type,
            'updated_by': updated_by,
            'deal_url': f"{settings.FRONTEND_URL}/deals/{deal.id}",
        }
        return NotificationService.send_email(
            to_emails=email,
            subject=subject,
            template_name='emails/deal_update.html',
            context=context
        )
    
    @staticmethod
    def send_task_reminder(email, task):
        """Send task reminder notification"""
        subject = f"Task reminder: {task.subject}"
        context = {
            'task': task,
            'task_url': f"{settings.FRONTEND_URL}/tasks/{task.id}",
        }
        return NotificationService.send_email(
            to_emails=email,
            subject=subject,
            template_name='emails/task_reminder.html',
            context=context
        )


# Celery tasks for async email sending
@shared_task
def send_invitation_email_async(email, invitation_token, inviter_name, company_name):
    """Send invitation email asynchronously"""
    return NotificationService.send_user_invitation(
        email, invitation_token, inviter_name, company_name
    )


@shared_task
def send_password_reset_email_async(email, reset_token, user_name):
    """Send password reset email asynchronously"""
    return NotificationService.send_password_reset(email, reset_token, user_name)


@shared_task
def send_lead_assignment_email_async(email, lead_id, assigned_by_id):
    """Send lead assignment email asynchronously"""
    from crm.models import Lead
    from django.contrib.auth import get_user_model
    
    User = get_user_model()
    try:
        lead = Lead.objects.get(id=lead_id)
        assigned_by = User.objects.get(id=assigned_by_id)
        return NotificationService.send_lead_assignment(email, lead, assigned_by)
    except (Lead.DoesNotExist, User.DoesNotExist) as e:
        logger.error(f"Failed to send lead assignment email: {str(e)}")
        return False


@shared_task
def send_deal_update_email_async(email, deal_id, update_type, updated_by_id):
    """Send deal update email asynchronously"""
    from deals.models import Deal
    from django.contrib.auth import get_user_model
    
    User = get_user_model()
    try:
        deal = Deal.objects.get(id=deal_id)
        updated_by = User.objects.get(id=updated_by_id)
        return NotificationService.send_deal_update(email, deal, update_type, updated_by)
    except (Deal.DoesNotExist, User.DoesNotExist) as e:
        logger.error(f"Failed to send deal update email: {str(e)}")
        return False
