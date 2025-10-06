# workflow/tasks.py
# Celery tasks for workflow operations

from celery import shared_task
from django.utils import timezone
from django.db.models import Q
import logging

logger = logging.getLogger(__name__)


@shared_task(name='workflow.escalate_expired_approvals')
def escalate_expired_approvals():
    """
    Celery task to escalate expired workflow approvals.
    
    This task:
    1. Finds all pending approvals that have expired
    2. Updates their status to 'escalated'
    3. Logs the escalation for audit purposes
    
    Returns:
        dict: Summary of escalations performed
    """
    from workflow.models import WorkflowApproval
    
    now = timezone.now()
    
    # Find expired pending approvals
    expired_approvals = WorkflowApproval.objects.filter(
        status='pending',
        expires_at__lte=now
    )
    
    escalated_count = 0
    escalation_details = []
    
    for approval in expired_approvals:
        try:
            # Update status to escalated
            approval.status = 'escalated'
            
            # Update metadata
            metadata = approval.metadata or {}
            metadata.update({
                'escalated_at': now.isoformat(),
                'escalation_reason': 'timeout',
                'original_approver_role': approval.approver_role,
                'escalated_to_role': approval.escalate_role or 'default_escalation_role',
            })
            approval.metadata = metadata
            approval.save()
            
            escalated_count += 1
            escalation_details.append({
                'approval_id': str(approval.id),
                'workflow_run_id': str(approval.workflow_run_id),
                'action_run_id': str(approval.action_run_id),
                'escalated_to': approval.escalate_role,
            })
            
            logger.info(
                f"Escalated approval {approval.id} from role '{approval.approver_role}' "
                f"to role '{approval.escalate_role}'"
            )
            
        except Exception as e:
            logger.error(
                f"Error escalating approval {approval.id}: {str(e)}",
                exc_info=True
            )
    
    result = {
        'task': 'escalate_expired_approvals',
        'executed_at': now.isoformat(),
        'escalated_count': escalated_count,
        'escalation_details': escalation_details,
    }
    
    logger.info(
        f"Escalation task completed: {escalated_count} approvals escalated"
    )
    
    return result


@shared_task(name='workflow.cleanup_old_approvals')
def cleanup_old_approvals(days=90):
    """
    Optional task to clean up old resolved approvals.
    
    Args:
        days (int): Number of days to keep resolved approvals
        
    Returns:
        dict: Summary of cleanup performed
    """
    from workflow.models import WorkflowApproval
    from datetime import timedelta
    
    cutoff_date = timezone.now() - timedelta(days=days)
    
    # Only delete resolved approvals (approved, denied, expired)
    old_approvals = WorkflowApproval.objects.filter(
        resolved_at__lt=cutoff_date,
        status__in=['approved', 'denied', 'expired']
    )
    
    count = old_approvals.count()
    old_approvals.delete()
    
    logger.info(f"Cleaned up {count} old approvals older than {days} days")
    
    return {
        'task': 'cleanup_old_approvals',
        'executed_at': timezone.now().isoformat(),
        'deleted_count': count,
        'cutoff_days': days,
    }
