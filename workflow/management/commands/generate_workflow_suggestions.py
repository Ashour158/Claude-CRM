# workflow/management/commands/generate_workflow_suggestions.py
# Management command to generate workflow suggestions from historical data

from django.core.management.base import BaseCommand
from django.db.models import Count, Avg, Q
from django.utils import timezone
from datetime import timedelta
from workflow.models import (
    WorkflowExecution, WorkflowSuggestion, Workflow, 
    ApprovalRequest, BusinessRuleExecution
)
from workflow.metrics import record_workflow_suggestion
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Generate workflow suggestions based on historical execution data'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=30,
            help='Number of days to analyze (default: 30)'
        )
        parser.add_argument(
            '--min-occurrences',
            type=int,
            default=10,
            help='Minimum pattern occurrences to suggest (default: 10)'
        )
        parser.add_argument(
            '--confidence-threshold',
            type=float,
            default=0.7,
            help='Minimum confidence score to create suggestion (default: 0.7)'
        )
    
    def handle(self, *args, **options):
        days = options['days']
        min_occurrences = options['min_occurrences']
        confidence_threshold = options['confidence_threshold']
        
        self.stdout.write(f'Analyzing workflow data from last {days} days...')
        
        cutoff_date = timezone.now() - timedelta(days=days)
        
        suggestions_created = 0
        
        # Generate different types of suggestions
        suggestions_created += self._suggest_auto_approvals(
            cutoff_date, min_occurrences, confidence_threshold
        )
        suggestions_created += self._suggest_parallel_approvals(
            cutoff_date, min_occurrences, confidence_threshold
        )
        suggestions_created += self._suggest_workflow_optimizations(
            cutoff_date, min_occurrences, confidence_threshold
        )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully created {suggestions_created} workflow suggestions'
            )
        )
    
    def _suggest_auto_approvals(self, cutoff_date, min_occurrences, confidence_threshold):
        """Suggest auto-approvals for consistently approved patterns"""
        suggestions_created = 0
        
        # Find approval patterns that are always approved
        approvals = ApprovalRequest.objects.filter(
            requested_at__gte=cutoff_date,
            status='approved'
        ).values('approval_process_id', 'entity_type')
        
        approval_counts = approvals.annotate(
            total_count=Count('id')
        ).filter(total_count__gte=min_occurrences)
        
        for approval_pattern in approval_counts:
            process_id = approval_pattern['approval_process_id']
            entity_type = approval_pattern['entity_type']
            total_count = approval_pattern['total_count']
            
            # Check rejection rate
            rejections = ApprovalRequest.objects.filter(
                approval_process_id=process_id,
                entity_type=entity_type,
                requested_at__gte=cutoff_date,
                status='rejected'
            ).count()
            
            approval_rate = total_count / (total_count + rejections) if (total_count + rejections) > 0 else 0
            
            if approval_rate >= 0.95:  # 95% or higher approval rate
                confidence = min(approval_rate, 1.0)
                
                if confidence >= confidence_threshold:
                    # Check if suggestion already exists
                    existing = WorkflowSuggestion.objects.filter(
                        title__contains=f'Auto-approve {entity_type}',
                        status__in=['pending', 'accepted']
                    ).exists()
                    
                    if not existing:
                        try:
                            suggestion = WorkflowSuggestion.objects.create(
                                title=f'Auto-approve {entity_type} requests',
                                description=f'Based on {total_count} requests, {entity_type} approvals have a {approval_rate*100:.1f}% approval rate. Consider implementing auto-approval rules.',
                                source='historical',
                                workflow_template={
                                    'workflow_type': 'approval',
                                    'entity_type': entity_type,
                                    'auto_approve': True,
                                    'conditions': {}
                                },
                                confidence_score=confidence,
                                supporting_data={
                                    'total_requests': total_count,
                                    'approval_rate': approval_rate,
                                    'rejection_count': rejections
                                },
                                pattern_frequency=total_count
                            )
                            
                            # Record metric
                            record_workflow_suggestion('historical', 'pending', confidence)
                            
                            suggestions_created += 1
                            logger.info(f'Created auto-approval suggestion for {entity_type}')
                        except Exception as e:
                            logger.error(f'Failed to create suggestion: {str(e)}')
        
        return suggestions_created
    
    def _suggest_parallel_approvals(self, cutoff_date, min_occurrences, confidence_threshold):
        """Suggest parallel approvals when multiple approvers at same level"""
        suggestions_created = 0
        
        # Analyze workflows with sequential approvals that could be parallel
        executions = WorkflowExecution.objects.filter(
            started_at__gte=cutoff_date,
            status='completed'
        ).select_related('workflow')
        
        workflow_patterns = {}
        
        for execution in executions:
            workflow = execution.workflow
            if workflow.workflow_type != 'approval':
                continue
            
            # Analyze approval steps
            approval_steps = [
                step for step in workflow.steps 
                if step.get('action') == 'approval'
            ]
            
            if len(approval_steps) >= 2:
                workflow_id = workflow.id
                if workflow_id not in workflow_patterns:
                    workflow_patterns[workflow_id] = {
                        'workflow': workflow,
                        'count': 0,
                        'approval_steps': len(approval_steps)
                    }
                workflow_patterns[workflow_id]['count'] += 1
        
        # Create suggestions for workflows with multiple approvals
        for workflow_id, pattern in workflow_patterns.items():
            if pattern['count'] >= min_occurrences:
                workflow = pattern['workflow']
                
                # Check if suggestion exists
                existing = WorkflowSuggestion.objects.filter(
                    title__contains=f'Parallel approval for {workflow.name}',
                    status__in=['pending', 'accepted']
                ).exists()
                
                if not existing:
                    confidence = min(0.75, 1.0)  # Base confidence
                    
                    if confidence >= confidence_threshold:
                        try:
                            suggestion = WorkflowSuggestion.objects.create(
                                title=f'Parallel approval for {workflow.name}',
                                description=f'Workflow has {pattern["approval_steps"]} sequential approval steps. Running approvals in parallel could reduce completion time.',
                                source='pattern',
                                workflow_template={
                                    'workflow_id': workflow_id,
                                    'optimization': 'parallel_approval',
                                    'approval_type': 'parallel'
                                },
                                confidence_score=confidence,
                                supporting_data={
                                    'execution_count': pattern['count'],
                                    'approval_steps': pattern['approval_steps']
                                },
                                pattern_frequency=pattern['count']
                            )
                            
                            record_workflow_suggestion('pattern', 'pending', confidence)
                            suggestions_created += 1
                            logger.info(f'Created parallel approval suggestion for workflow {workflow.name}')
                        except Exception as e:
                            logger.error(f'Failed to create suggestion: {str(e)}')
        
        return suggestions_created
    
    def _suggest_workflow_optimizations(self, cutoff_date, min_occurrences, confidence_threshold):
        """Suggest workflow optimizations based on execution patterns"""
        suggestions_created = 0
        
        # Find workflows with long execution times
        workflows = Workflow.objects.filter(is_active=True)
        
        for workflow in workflows:
            executions = WorkflowExecution.objects.filter(
                workflow=workflow,
                started_at__gte=cutoff_date,
                status='completed',
                completed_at__isnull=False
            )
            
            if executions.count() < min_occurrences:
                continue
            
            durations = []
            for execution in executions:
                duration = (execution.completed_at - execution.started_at).total_seconds()
                durations.append(duration)
            
            if durations:
                avg_duration = sum(durations) / len(durations)
                
                # Suggest optimization if average duration > 5 minutes
                if avg_duration > 300:
                    existing = WorkflowSuggestion.objects.filter(
                        title__contains=f'Optimize {workflow.name}',
                        status__in=['pending', 'accepted']
                    ).exists()
                    
                    if not existing:
                        confidence = 0.7
                        
                        try:
                            suggestion = WorkflowSuggestion.objects.create(
                                title=f'Optimize {workflow.name} performance',
                                description=f'Average execution time is {avg_duration/60:.1f} minutes. Consider caching, reducing approval steps, or optimizing action execution.',
                                source='pattern',
                                workflow_template={
                                    'workflow_id': workflow.id,
                                    'optimization': 'performance',
                                    'current_avg_duration': avg_duration
                                },
                                confidence_score=confidence,
                                supporting_data={
                                    'avg_duration_seconds': avg_duration,
                                    'execution_count': len(durations)
                                },
                                pattern_frequency=len(durations)
                            )
                            
                            record_workflow_suggestion('pattern', 'pending', confidence)
                            suggestions_created += 1
                            logger.info(f'Created optimization suggestion for workflow {workflow.name}')
                        except Exception as e:
                            logger.error(f'Failed to create suggestion: {str(e)}')
        
        return suggestions_created
