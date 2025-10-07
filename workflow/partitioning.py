# workflow/partitioning.py
# Workflow async step partitioning for I/O vs CPU queues

import logging
from typing import Dict, Any, List, Optional
from enum import Enum
from celery import Task, group, chain, chord
from django.conf import settings

logger = logging.getLogger(__name__)


class StepType(Enum):
    """Workflow step types for queue partitioning."""
    IO_BOUND = 'io_bound'       # Network requests, database queries, file I/O
    CPU_BOUND = 'cpu_bound'     # Heavy computation, data processing
    MIXED = 'mixed'             # Both I/O and CPU operations


class QueueConfig:
    """Configuration for workflow execution queues."""
    
    # Queue names
    IO_QUEUE = getattr(settings, 'WORKFLOW_IO_QUEUE', 'workflow_io')
    CPU_QUEUE = getattr(settings, 'WORKFLOW_CPU_QUEUE', 'workflow_cpu')
    DEFAULT_QUEUE = getattr(settings, 'WORKFLOW_DEFAULT_QUEUE', 'workflow_default')
    
    # Queue priorities
    PRIORITY_HIGH = 9
    PRIORITY_NORMAL = 5
    PRIORITY_LOW = 1
    
    # Timeouts (seconds)
    IO_TIMEOUT = 300    # 5 minutes for I/O operations
    CPU_TIMEOUT = 600   # 10 minutes for CPU operations
    
    # Retry configuration
    IO_MAX_RETRIES = 3
    CPU_MAX_RETRIES = 2


class WorkflowStepClassifier:
    """
    Classifies workflow steps based on their characteristics
    to determine optimal queue assignment.
    """
    
    # Step patterns that indicate I/O-bound operations
    IO_PATTERNS = [
        'api', 'http', 'request', 'fetch', 'download', 'upload',
        'email', 'notification', 'webhook', 'database', 'query',
        'save', 'update', 'create', 'delete', 'read', 'write'
    ]
    
    # Step patterns that indicate CPU-bound operations
    CPU_PATTERNS = [
        'calculate', 'compute', 'process', 'transform', 'analyze',
        'aggregate', 'generate', 'encode', 'decode', 'compress',
        'encrypt', 'hash', 'sort', 'filter', 'map', 'reduce'
    ]
    
    @classmethod
    def classify_step(cls, step_config: Dict[str, Any]) -> StepType:
        """
        Classify a workflow step based on its configuration.
        
        Args:
            step_config: Step configuration dictionary with keys like
                        'type', 'action', 'name', 'settings'
        
        Returns:
            StepType enum indicating the step classification
        """
        step_type = step_config.get('type', '').lower()
        action = step_config.get('action', '').lower()
        name = step_config.get('name', '').lower()
        
        # Check for explicit type in config
        if 'queue_type' in step_config:
            queue_type = step_config['queue_type'].lower()
            if queue_type == 'io':
                return StepType.IO_BOUND
            elif queue_type == 'cpu':
                return StepType.CPU_BOUND
        
        # Classify based on patterns
        text_to_check = f"{step_type} {action} {name}"
        
        io_score = sum(1 for pattern in cls.IO_PATTERNS if pattern in text_to_check)
        cpu_score = sum(1 for pattern in cls.CPU_PATTERNS if pattern in text_to_check)
        
        if io_score > cpu_score:
            return StepType.IO_BOUND
        elif cpu_score > io_score:
            return StepType.CPU_BOUND
        else:
            return StepType.MIXED
    
    @classmethod
    def get_queue_name(cls, step_type: StepType) -> str:
        """Get queue name for step type."""
        if step_type == StepType.IO_BOUND:
            return QueueConfig.IO_QUEUE
        elif step_type == StepType.CPU_BOUND:
            return QueueConfig.CPU_QUEUE
        else:
            return QueueConfig.DEFAULT_QUEUE


class WorkflowPartitioner:
    """
    Partitions workflow execution across different queues
    based on step characteristics.
    """
    
    @classmethod
    def partition_steps(cls, steps: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Partition workflow steps into queue-specific groups.
        
        Args:
            steps: List of workflow step configurations
            
        Returns:
            Dictionary mapping queue names to lists of steps
        """
        partitions = {
            QueueConfig.IO_QUEUE: [],
            QueueConfig.CPU_QUEUE: [],
            QueueConfig.DEFAULT_QUEUE: []
        }
        
        for step in steps:
            step_type = WorkflowStepClassifier.classify_step(step)
            queue_name = WorkflowStepClassifier.get_queue_name(step_type)
            
            # Add queue info to step config
            step['_queue'] = queue_name
            step['_step_type'] = step_type.value
            
            partitions[queue_name].append(step)
        
        logger.info(
            f"Partitioned {len(steps)} steps: "
            f"{len(partitions[QueueConfig.IO_QUEUE])} I/O, "
            f"{len(partitions[QueueConfig.CPU_QUEUE])} CPU, "
            f"{len(partitions[QueueConfig.DEFAULT_QUEUE])} mixed"
        )
        
        return partitions
    
    @classmethod
    def create_execution_plan(cls, steps: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Create optimized execution plan with parallel and sequential steps.
        
        Args:
            steps: List of workflow step configurations
            
        Returns:
            Execution plan with parallelizable steps grouped
        """
        # Partition steps
        partitions = cls.partition_steps(steps)
        
        # Group steps that can run in parallel
        parallel_groups = []
        sequential_steps = []
        
        for i, step in enumerate(steps):
            # Check if step has dependencies on previous steps
            depends_on = step.get('depends_on', [])
            
            if not depends_on:
                # Can run in parallel with other independent steps
                parallel_groups.append({
                    'index': i,
                    'step': step,
                    'queue': step.get('_queue', QueueConfig.DEFAULT_QUEUE)
                })
            else:
                # Must run sequentially after dependencies
                sequential_steps.append({
                    'index': i,
                    'step': step,
                    'depends_on': depends_on,
                    'queue': step.get('_queue', QueueConfig.DEFAULT_QUEUE)
                })
        
        return {
            'parallel_groups': parallel_groups,
            'sequential_steps': sequential_steps,
            'partitions': partitions
        }


class WorkflowExecutor:
    """
    Executes workflow steps across partitioned queues using Celery.
    """
    
    @classmethod
    def execute_step(cls, step_config: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a single workflow step.
        
        Args:
            step_config: Step configuration
            context: Execution context with data from previous steps
            
        Returns:
            Step execution result
        """
        step_type = step_config.get('_step_type', StepType.MIXED.value)
        queue = step_config.get('_queue', QueueConfig.DEFAULT_QUEUE)
        
        logger.info(f"Executing step {step_config.get('name')} on queue {queue}")
        
        # Execute the step (implementation depends on step type)
        result = {
            'step_name': step_config.get('name'),
            'status': 'completed',
            'output': {},
            'queue': queue,
            'step_type': step_type
        }
        
        return result
    
    @classmethod
    def execute_workflow(cls, workflow_id: str, steps: List[Dict[str, Any]], 
                        context: Dict[str, Any]) -> str:
        """
        Execute workflow with step partitioning.
        
        Args:
            workflow_id: Workflow UUID
            steps: List of workflow steps
            context: Initial execution context
            
        Returns:
            Celery task ID for tracking
        """
        # Create execution plan
        plan = WorkflowPartitioner.create_execution_plan(steps)
        
        logger.info(
            f"Executing workflow {workflow_id} with "
            f"{len(plan['parallel_groups'])} parallel and "
            f"{len(plan['sequential_steps'])} sequential steps"
        )
        
        # Execute parallel steps first
        parallel_tasks = []
        for group_item in plan['parallel_groups']:
            step = group_item['step']
            queue = group_item['queue']
            
            # Create Celery task for this step
            # task = execute_workflow_step.apply_async(
            #     args=[workflow_id, step, context],
            #     queue=queue
            # )
            # parallel_tasks.append(task)
        
        # Execute sequential steps after parallel completion
        # This would use Celery chains and chords
        
        return f"workflow_execution_{workflow_id}"


class WorkflowMetrics:
    """
    Collect metrics for workflow execution across queues.
    """
    
    @classmethod
    def record_step_execution(cls, step_name: str, queue: str, 
                            duration_ms: int, success: bool) -> None:
        """
        Record metrics for a workflow step execution.
        
        Args:
            step_name: Name of the step
            queue: Queue where step was executed
            duration_ms: Execution duration in milliseconds
            success: Whether execution succeeded
        """
        # This would integrate with Prometheus or other metrics systems
        logger.info(
            f"Step metrics: {step_name} on {queue} - "
            f"{duration_ms}ms - {'success' if success else 'failure'}"
        )
    
    @classmethod
    def get_queue_stats(cls, queue_name: str) -> Dict[str, Any]:
        """
        Get statistics for a specific queue.
        
        Args:
            queue_name: Name of the queue
            
        Returns:
            Queue statistics dictionary
        """
        # This would query Celery or Redis for actual stats
        return {
            'queue': queue_name,
            'pending_tasks': 0,
            'active_tasks': 0,
            'completed_tasks': 0,
            'failed_tasks': 0,
            'avg_duration_ms': 0
        }


# Celery task definitions (would be in tasks.py in production)
class WorkflowStepTask(Task):
    """Base task for workflow steps with queue-specific configuration."""
    
    def apply_async(self, args=None, kwargs=None, **options):
        """Override to set queue-specific options."""
        step_config = args[1] if len(args) > 1 else {}
        
        # Set timeout based on step type
        step_type = step_config.get('_step_type', StepType.MIXED.value)
        if step_type == StepType.IO_BOUND.value:
            options.setdefault('time_limit', QueueConfig.IO_TIMEOUT)
            options.setdefault('max_retries', QueueConfig.IO_MAX_RETRIES)
        elif step_type == StepType.CPU_BOUND.value:
            options.setdefault('time_limit', QueueConfig.CPU_TIMEOUT)
            options.setdefault('max_retries', QueueConfig.CPU_MAX_RETRIES)
        
        return super().apply_async(args, kwargs, **options)
