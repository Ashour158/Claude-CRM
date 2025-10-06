# workflow/services.py
# Workflow execution service and DSL evaluator for Phase 4+

import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from django.utils import timezone
from django.db import transaction
from workflow.models import (
    Workflow, WorkflowTrigger, WorkflowAction,
    WorkflowRun, WorkflowActionRun
)

logger = logging.getLogger(__name__)

class WorkflowConditionEvaluator:
    """Evaluates workflow trigger conditions using simple DSL"""
    
    OPERATORS = {
        'eq': lambda a, b: a == b,
        'ne': lambda a, b: a != b,
        'gt': lambda a, b: a > b,
        'gte': lambda a, b: a >= b,
        'lt': lambda a, b: a < b,
        'lte': lambda a, b: a <= b,
        'in': lambda a, b: a in b,
        'contains': lambda a, b: b in a,
        'startswith': lambda a, b: str(a).startswith(str(b)),
        'endswith': lambda a, b: str(a).endswith(str(b)),
    }
    
    @classmethod
    def evaluate(cls, conditions: Dict[str, Any], context: Dict[str, Any]) -> bool:
        """
        Evaluate conditions against context data.
        
        Conditions format:
        {
            "field": "status",
            "operator": "eq",
            "value": "qualified"
        }
        OR
        {
            "and": [
                {"field": "amount", "operator": "gte", "value": 1000},
                {"field": "stage", "operator": "eq", "value": "proposal"}
            ]
        }
        OR
        {
            "or": [...]
        }
        """
        if not conditions:
            return True
        
        # Handle logical operators
        if 'and' in conditions:
            return all(cls.evaluate(cond, context) for cond in conditions['and'])
        
        if 'or' in conditions:
            return any(cls.evaluate(cond, context) for cond in conditions['or'])
        
        if 'not' in conditions:
            return not cls.evaluate(conditions['not'], context)
        
        # Handle simple condition
        field = conditions.get('field')
        operator = conditions.get('operator', 'eq')
        expected_value = conditions.get('value')
        
        if not field:
            logger.warning(f"Condition missing 'field': {conditions}")
            return False
        
        # Get actual value from context (support nested fields with dot notation)
        actual_value = cls._get_nested_value(context, field)
        
        # Apply operator
        op_func = cls.OPERATORS.get(operator)
        if not op_func:
            logger.warning(f"Unknown operator: {operator}")
            return False
        
        try:
            return op_func(actual_value, expected_value)
        except Exception as e:
            logger.error(f"Error evaluating condition: {e}")
            return False
    
    @staticmethod
    def _get_nested_value(data: Dict, field: str) -> Any:
        """Get nested field value using dot notation (e.g., 'lead.status')"""
        keys = field.split('.')
        value = data
        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
            else:
                return None
        return value

class WorkflowActionExecutor:
    """Executes workflow actions"""
    
    @classmethod
    def execute_action(
        cls,
        action: WorkflowAction,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute a workflow action.
        
        Returns:
            Dict with 'success', 'result', and optional 'error' keys
        """
        action_type = action.action_type
        payload = action.payload
        
        try:
            if action_type == 'send_email':
                return cls._send_email(payload, context)
            elif action_type == 'add_note':
                return cls._add_note(payload, context)
            elif action_type == 'update_field':
                return cls._update_field(payload, context)
            elif action_type == 'enqueue_export':
                return cls._enqueue_export(payload, context)
            elif action_type == 'create_task':
                return cls._create_task(payload, context)
            elif action_type == 'send_notification':
                return cls._send_notification(payload, context)
            elif action_type == 'call_webhook':
                return cls._call_webhook(payload, context)
            else:
                return {
                    'success': False,
                    'error': f'Unknown action type: {action_type}'
                }
        except Exception as e:
            logger.error(f"Error executing action {action_type}: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    def _send_email(payload: Dict, context: Dict) -> Dict:
        """Send email action (stub for now)"""
        logger.info(f"Send email action: {payload}")
        # TODO: Integrate with email service
        return {
            'success': True,
            'result': {
                'action': 'send_email',
                'recipient': payload.get('to'),
                'subject': payload.get('subject'),
                'status': 'queued'
            }
        }
    
    @staticmethod
    def _add_note(payload: Dict, context: Dict) -> Dict:
        """Add note action"""
        logger.info(f"Add note action: {payload}")
        # TODO: Create note in timeline/activity
        return {
            'success': True,
            'result': {
                'action': 'add_note',
                'note': payload.get('note'),
                'entity_type': payload.get('entity_type'),
                'entity_id': context.get('entity_id')
            }
        }
    
    @staticmethod
    def _update_field(payload: Dict, context: Dict) -> Dict:
        """Update field action"""
        logger.info(f"Update field action: {payload}")
        # TODO: Update the field on the target object
        return {
            'success': True,
            'result': {
                'action': 'update_field',
                'field': payload.get('field'),
                'value': payload.get('value'),
                'entity_type': payload.get('entity_type'),
                'entity_id': context.get('entity_id')
            }
        }
    
    @staticmethod
    def _enqueue_export(payload: Dict, context: Dict) -> Dict:
        """Enqueue export action"""
        logger.info(f"Enqueue export action: {payload}")
        # TODO: Queue export job
        return {
            'success': True,
            'result': {
                'action': 'enqueue_export',
                'export_type': payload.get('export_type'),
                'filters': payload.get('filters', {}),
                'status': 'queued'
            }
        }
    
    @staticmethod
    def _create_task(payload: Dict, context: Dict) -> Dict:
        """Create task action"""
        logger.info(f"Create task action: {payload}")
        # TODO: Create activity/task
        return {
            'success': True,
            'result': {
                'action': 'create_task',
                'title': payload.get('title'),
                'assignee': payload.get('assignee'),
                'due_date': payload.get('due_date')
            }
        }
    
    @staticmethod
    def _send_notification(payload: Dict, context: Dict) -> Dict:
        """Send notification action"""
        logger.info(f"Send notification action: {payload}")
        # TODO: Send in-app notification
        return {
            'success': True,
            'result': {
                'action': 'send_notification',
                'recipient': payload.get('recipient'),
                'message': payload.get('message')
            }
        }
    
    @staticmethod
    def _call_webhook(payload: Dict, context: Dict) -> Dict:
        """Call webhook action"""
        logger.info(f"Call webhook action: {payload}")
        # TODO: Make HTTP request to webhook URL
        return {
            'success': True,
            'result': {
                'action': 'call_webhook',
                'url': payload.get('url'),
                'method': payload.get('method', 'POST'),
                'status': 'sent'
            }
        }

class WorkflowExecutionService:
    """Main workflow execution service"""
    
    @classmethod
    def trigger_workflow(
        cls,
        event_type: str,
        event_data: Dict[str, Any],
        company,
        user=None
    ) -> List[WorkflowRun]:
        """
        Trigger workflows matching the event type.
        
        Args:
            event_type: Type of event (e.g., 'lead.created')
            event_data: Event data to pass to workflow
            company: Company context
            user: User who triggered the event (optional)
        
        Returns:
            List of WorkflowRun instances created
        """
        # Find matching triggers
        triggers = WorkflowTrigger.objects.filter(
            event_type=event_type,
            is_active=True,
            workflow__is_active=True,
            workflow__status='active',
            company=company
        ).select_related('workflow').order_by('-priority')
        
        runs = []
        for trigger in triggers:
            # Check if conditions are met
            if not WorkflowConditionEvaluator.evaluate(trigger.conditions, event_data):
                logger.debug(f"Trigger {trigger.id} conditions not met")
                continue
            
            # Create workflow run
            run = cls.execute_workflow(
                workflow=trigger.workflow,
                trigger=trigger,
                trigger_data=event_data,
                user=user
            )
            runs.append(run)
        
        return runs
    
    @classmethod
    def execute_workflow(
        cls,
        workflow: Workflow,
        trigger: WorkflowTrigger = None,
        trigger_data: Dict = None,
        user = None
    ) -> WorkflowRun:
        """
        Execute a workflow instance.
        
        Args:
            workflow: Workflow to execute
            trigger: Trigger that fired (optional)
            trigger_data: Data that triggered the workflow
            user: User who triggered execution
        
        Returns:
            WorkflowRun instance
        """
        start_time = timezone.now()
        
        # Create workflow run
        run = WorkflowRun.objects.create(
            workflow=workflow,
            trigger=trigger,
            company=workflow.company,
            triggered_by=user,
            trigger_data=trigger_data or {},
            status='running',
            started_at=start_time
        )
        
        try:
            # Execute actions in order
            actions = workflow.actions.filter(is_active=True).order_by('ordering')
            
            for action in actions:
                action_run = cls._execute_action(run, action, trigger_data or {})
                
                # If action failed and not allowed to fail, stop execution
                if not action_run.success and not action.allow_failure:
                    run.status = 'failed'
                    run.success = False
                    run.error_message = f"Action {action.action_type} failed: {action_run.error_message}"
                    break
            else:
                # All actions completed successfully
                run.status = 'completed'
                run.success = True
        
        except Exception as e:
            logger.error(f"Workflow execution error: {e}", exc_info=True)
            run.status = 'failed'
            run.success = False
            run.error_message = str(e)
            run.error_details = {'exception': str(type(e).__name__)}
        
        finally:
            # Update run timing
            end_time = timezone.now()
            run.completed_at = end_time
            run.duration_ms = int((end_time - start_time).total_seconds() * 1000)
            run.save()
            
            # Update workflow stats
            workflow.execution_count += 1
            workflow.last_executed = end_time
            workflow.save(update_fields=['execution_count', 'last_executed'])
        
        return run
    
    @classmethod
    def _execute_action(
        cls,
        run: WorkflowRun,
        action: WorkflowAction,
        context: Dict[str, Any]
    ) -> WorkflowActionRun:
        """Execute a single workflow action and create action run record"""
        start_time = timezone.now()
        
        action_run = WorkflowActionRun.objects.create(
            workflow_run=run,
            action=action,
            company=run.company,
            status='running',
            started_at=start_time
        )
        
        try:
            # Execute the action
            result = WorkflowActionExecutor.execute_action(action, context)
            
            action_run.success = result.get('success', False)
            action_run.result_data = result.get('result', {})
            action_run.error_message = result.get('error', '')
            action_run.status = 'completed' if action_run.success else 'failed'
        
        except Exception as e:
            logger.error(f"Action execution error: {e}", exc_info=True)
            action_run.success = False
            action_run.status = 'failed'
            action_run.error_message = str(e)
        
        finally:
            end_time = timezone.now()
            action_run.completed_at = end_time
            action_run.duration_ms = int((end_time - start_time).total_seconds() * 1000)
            action_run.save()
        
        return action_run
