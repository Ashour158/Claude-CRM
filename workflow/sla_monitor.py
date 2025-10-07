# workflow/sla_monitor.py
# SLA monitoring and alerting utilities

from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from datetime import timedelta
import logging
from .models import WorkflowSLA, SLABreach, WorkflowExecution
from .metrics import record_sla_breach, update_sla_metrics

logger = logging.getLogger(__name__)


class SLAMonitor:
    """Monitor workflow executions for SLA breaches"""
    
    def __init__(self):
        self.alert_enabled = getattr(settings, 'SLA_ALERTS_ENABLED', True)
    
    def check_execution(self, execution):
        """
        Check a workflow execution against all SLAs
        
        Args:
            execution: WorkflowExecution instance
        """
        if execution.status != 'completed':
            return
        
        # Calculate execution duration
        if not execution.completed_at or not execution.started_at:
            return
        
        duration = (execution.completed_at - execution.started_at).total_seconds()
        
        # Get all active SLAs for this workflow
        slas = WorkflowSLA.objects.filter(
            workflow=execution.workflow,
            is_active=True
        )
        
        for sla in slas:
            self._check_sla(sla, execution, duration)
    
    def _check_sla(self, sla, execution, duration_seconds):
        """
        Check if an execution breaches an SLA
        
        Args:
            sla: WorkflowSLA instance
            execution: WorkflowExecution instance
            duration_seconds: Execution duration in seconds
        """
        # Update SLA statistics
        sla.total_executions += 1
        
        # Check if SLA is breached
        breach_severity = None
        
        if duration_seconds > sla.critical_threshold_seconds:
            breach_severity = 'critical'
        elif duration_seconds > sla.warning_threshold_seconds:
            breach_severity = 'warning'
        
        if breach_severity:
            # Record breach
            sla.breached_executions += 1
            breach = self._create_breach(
                sla, execution, duration_seconds, breach_severity
            )
            
            # Send alert if enabled
            if self.alert_enabled:
                self._send_alert(breach)
            
            # Record Prometheus metric
            record_sla_breach(breach_severity, sla.workflow.name)
        
        # Update SLO percentage
        sla.current_slo_percentage = (
            (sla.total_executions - sla.breached_executions) / 
            sla.total_executions * 100
        ) if sla.total_executions > 0 else 100.0
        
        sla.save()
        
        # Update Prometheus metrics
        update_sla_metrics(
            sla.workflow.name,
            sla.name,
            sla.target_duration_seconds,
            sla.current_slo_percentage
        )
    
    def _create_breach(self, sla, execution, duration_seconds, severity):
        """
        Create an SLA breach record
        
        Args:
            sla: WorkflowSLA instance
            execution: WorkflowExecution instance
            duration_seconds: Actual duration in seconds
            severity: Breach severity ('warning' or 'critical')
        
        Returns:
            SLABreach instance
        """
        breach_margin = duration_seconds - sla.target_duration_seconds
        
        breach = SLABreach.objects.create(
            company=sla.company,
            sla=sla,
            workflow_execution=execution,
            severity=severity,
            actual_duration_seconds=int(duration_seconds),
            target_duration_seconds=sla.target_duration_seconds,
            breach_margin_seconds=int(breach_margin)
        )
        
        logger.warning(
            f"SLA breach detected: {sla.name} for workflow {sla.workflow.name}. "
            f"Duration: {duration_seconds}s, Target: {sla.target_duration_seconds}s, "
            f"Severity: {severity}"
        )
        
        return breach
    
    def _send_alert(self, breach):
        """
        Send alert for SLA breach
        
        Args:
            breach: SLABreach instance
        """
        try:
            # Get alert recipients
            recipients = self._get_alert_recipients(breach.sla)
            
            if not recipients:
                logger.warning(f"No recipients configured for SLA {breach.sla.name}")
                return
            
            # Prepare alert email
            subject = f"[{breach.severity.upper()}] SLA Breach: {breach.sla.name}"
            message = self._format_alert_message(breach)
            
            # Send email
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=recipients,
                fail_silently=False
            )
            
            # Update breach record
            breach.alert_sent = True
            breach.alert_sent_at = timezone.now()
            breach.alert_recipients = recipients
            breach.save()
            
            logger.info(f"SLA breach alert sent to {len(recipients)} recipients")
            
        except Exception as e:
            logger.error(f"Failed to send SLA breach alert: {str(e)}")
    
    def _get_alert_recipients(self, sla):
        """
        Get list of email addresses to alert for SLA breach
        
        Args:
            sla: WorkflowSLA instance
        
        Returns:
            List of email addresses
        """
        recipients = []
        
        # Add workflow owner
        if sla.workflow.owner and sla.workflow.owner.email:
            recipients.append(sla.workflow.owner.email)
        
        # Add company admins (if configured)
        company_admins = sla.company.users.filter(
            usercompanyaccess__role__in=['admin', 'owner']
        )
        for admin in company_admins:
            if admin.email:
                recipients.append(admin.email)
        
        # Get custom recipients from settings
        custom_recipients = getattr(settings, 'SLA_ALERT_RECIPIENTS', [])
        recipients.extend(custom_recipients)
        
        # Remove duplicates
        return list(set(recipients))
    
    def _format_alert_message(self, breach):
        """
        Format alert message for SLA breach
        
        Args:
            breach: SLABreach instance
        
        Returns:
            Formatted message string
        """
        message = f"""
SLA Breach Alert

Severity: {breach.severity.upper()}
SLA: {breach.sla.name}
Workflow: {breach.sla.workflow.name}

Details:
- Target Duration: {breach.target_duration_seconds} seconds
- Actual Duration: {breach.actual_duration_seconds} seconds
- Breach Margin: {breach.breach_margin_seconds} seconds ({self._format_percentage(breach.breach_margin_seconds, breach.target_duration_seconds)})

Execution ID: {breach.workflow_execution.id}
Detected At: {breach.detected_at.strftime('%Y-%m-%d %H:%M:%S UTC')}

Current SLA Performance:
- Total Executions: {breach.sla.total_executions}
- Breached Executions: {breach.sla.breached_executions}
- Current SLO: {breach.sla.current_slo_percentage:.2f}%
- Target SLO: {breach.sla.slo_target_percentage}%

Please investigate and acknowledge this breach in the system.
        """
        return message.strip()
    
    def _format_percentage(self, value, total):
        """Calculate and format percentage"""
        if total == 0:
            return "N/A"
        percentage = (value / total) * 100
        return f"{percentage:.1f}%"
    
    def calculate_slo_metrics(self, sla, window_hours=None):
        """
        Calculate SLO metrics for a given window
        
        Args:
            sla: WorkflowSLA instance
            window_hours: Hours to look back (defaults to SLA's slo_window_hours)
        
        Returns:
            Dictionary with SLO metrics
        """
        if window_hours is None:
            window_hours = sla.slo_window_hours
        
        window_start = timezone.now() - timedelta(hours=window_hours)
        
        # Get breaches in window
        breaches = SLABreach.objects.filter(
            sla=sla,
            detected_at__gte=window_start
        )
        
        # Get executions in window
        executions = WorkflowExecution.objects.filter(
            workflow=sla.workflow,
            completed_at__gte=window_start,
            status='completed'
        )
        
        total_executions = executions.count()
        breached_count = breaches.count()
        
        slo_percentage = (
            ((total_executions - breached_count) / total_executions * 100)
            if total_executions > 0 else 100.0
        )
        
        return {
            'window_hours': window_hours,
            'window_start': window_start,
            'total_executions': total_executions,
            'breached_executions': breached_count,
            'slo_percentage': slo_percentage,
            'target_percentage': sla.slo_target_percentage,
            'meets_target': slo_percentage >= sla.slo_target_percentage,
            'critical_breaches': breaches.filter(severity='critical').count(),
            'warning_breaches': breaches.filter(severity='warning').count(),
        }


def check_workflow_execution(execution_id):
    """
    Convenience function to check a workflow execution for SLA breaches
    
    Args:
        execution_id: WorkflowExecution ID
    """
    try:
        execution = WorkflowExecution.objects.get(id=execution_id)
        monitor = SLAMonitor()
        monitor.check_execution(execution)
    except WorkflowExecution.DoesNotExist:
        logger.error(f"Workflow execution {execution_id} not found")
    except Exception as e:
        logger.error(f"Error checking workflow execution {execution_id}: {str(e)}")
