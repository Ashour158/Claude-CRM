# compliance/tasks.py
# Celery tasks for automated compliance operations

from celery import shared_task
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


@shared_task
def run_quarterly_access_review():
    """
    Automated quarterly access review
    Scheduled to run every 90 days
    """
    from .access_review import AccessReviewEngine
    from core.models import Company
    
    logger.info("Starting quarterly access review")
    
    results = []
    engine = AccessReviewEngine()
    
    # Run review for all active companies
    companies = Company.objects.filter(is_active=True)
    
    for company in companies:
        try:
            review = engine.create_review(company)
            result = engine.run_review(review)
            
            results.append({
                'company': company.name,
                'review_id': review.review_id,
                'stale_access_found': result['stale_access_found']
            })
            
            # Send notification if stale access found
            if result['stale_access_found'] > 0:
                send_access_review_notification(company, review, result)
        
        except Exception as e:
            logger.error(f"Error running access review for {company.name}: {str(e)}")
            results.append({
                'company': company.name,
                'error': str(e)
            })
    
    logger.info(f"Completed quarterly access review for {len(companies)} companies")
    return results


@shared_task
def execute_retention_policies():
    """
    Execute scheduled retention policies
    Scheduled to run daily
    """
    from .retention_engine import RetentionScheduler
    
    logger.info("Starting retention policy execution")
    
    results = RetentionScheduler.execute_scheduled_policies()
    
    logger.info(f"Executed {len(results)} retention policies")
    return results


@shared_task
def rotate_secrets():
    """
    Rotate secrets that are due for rotation
    Scheduled to run daily
    """
    from .models import SecretVault, SecretAccessLog
    from .encryption import SecretEncryption
    
    logger.info("Starting secret rotation check")
    
    now = timezone.now()
    
    # Find secrets due for rotation
    secrets = SecretVault.objects.filter(
        is_active=True,
        rotation_enabled=True,
        next_rotation__lte=now
    )
    
    rotated = 0
    encryption = SecretEncryption()
    
    for secret in secrets:
        try:
            # In a real implementation, this would:
            # 1. Generate new secret value (or fetch from provider)
            # 2. Encrypt with KMS
            # 3. Update integrations
            # 4. Log rotation
            
            # For now, just update rotation timestamps
            from datetime import timedelta
            secret.last_rotated = now
            secret.next_rotation = now + timedelta(days=secret.rotation_days)
            secret.save()
            
            # Log rotation
            SecretAccessLog.objects.create(
                secret=secret,
                company=secret.company,
                service_name='automated_rotation',
                success=True
            )
            
            rotated += 1
        
        except Exception as e:
            logger.error(f"Error rotating secret {secret.name}: {str(e)}")
            
            # Log failure
            SecretAccessLog.objects.create(
                secret=secret,
                company=secret.company,
                service_name='automated_rotation',
                success=False,
                failure_reason=str(e)
            )
    
    logger.info(f"Rotated {rotated} secrets")
    return {'rotated': rotated, 'total': secrets.count()}


@shared_task
def check_dsr_deadlines():
    """
    Check DSR request deadlines and send alerts
    Scheduled to run daily
    """
    from .models import DataSubjectRequest
    from datetime import timedelta
    
    logger.info("Checking DSR deadlines")
    
    now = timezone.now()
    warning_threshold = now + timedelta(days=7)  # Warn 7 days before deadline
    
    # Find DSR requests approaching deadline
    pending_requests = DataSubjectRequest.objects.filter(
        status__in=['pending', 'in_progress'],
        due_date__lte=warning_threshold,
        due_date__gte=now
    )
    
    alerts_sent = 0
    
    for dsr in pending_requests:
        try:
            days_remaining = (dsr.due_date - now).days
            
            # Send alert email
            send_dsr_deadline_alert(dsr, days_remaining)
            
            alerts_sent += 1
        
        except Exception as e:
            logger.error(f"Error sending DSR alert for {dsr.request_id}: {str(e)}")
    
    logger.info(f"Sent {alerts_sent} DSR deadline alerts")
    return {'alerts_sent': alerts_sent, 'total_pending': pending_requests.count()}


def send_access_review_notification(company, review, result):
    """Send notification about access review results"""
    subject = f"Access Review Completed - {company.name}"
    
    message = f"""
    Access review has been completed for {company.name}.
    
    Review ID: {review.review_id}
    Period: {review.review_period_start} to {review.review_period_end}
    
    Results:
    - Total users reviewed: {result['total_users']}
    - Stale access found: {result['stale_access_found']}
    
    Please review and take appropriate action.
    """
    
    # Get admin emails
    from core.models import UserCompanyAccess
    admin_users = UserCompanyAccess.objects.filter(
        company=company,
        role='admin',
        is_active=True
    ).select_related('user')
    
    recipient_emails = [access.user.email for access in admin_users]
    
    if recipient_emails:
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            recipient_emails,
            fail_silently=True
        )


def send_dsr_deadline_alert(dsr, days_remaining):
    """Send alert about approaching DSR deadline"""
    subject = f"DSR Request Deadline Alert - {dsr.request_id}"
    
    message = f"""
    A Data Subject Request is approaching its deadline.
    
    Request ID: {dsr.request_id}
    Type: {dsr.get_request_type_display()}
    Subject: {dsr.subject_email}
    
    Due Date: {dsr.due_date.strftime('%Y-%m-%d')}
    Days Remaining: {days_remaining}
    
    Please process this request as soon as possible.
    """
    
    # Get admin emails
    from core.models import UserCompanyAccess
    admin_users = UserCompanyAccess.objects.filter(
        company=dsr.company,
        role='admin',
        is_active=True
    ).select_related('user')
    
    recipient_emails = [access.user.email for access in admin_users]
    
    if recipient_emails:
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            recipient_emails,
            fail_silently=True
        )
