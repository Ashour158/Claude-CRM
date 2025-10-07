# analytics/metrics_catalog.py
# Metrics catalog and introspection system

from django.db import models
from core.models import CompanyIsolatedModel, User
import json
from typing import Dict, List, Any


class MetricDefinition(CompanyIsolatedModel):
    """
    Catalog of metric definitions with lineage tracking
    """
    # Basic Information
    name = models.CharField(max_length=255, unique=True)
    display_name = models.CharField(max_length=255)
    description = models.TextField()
    category = models.CharField(
        max_length=50,
        choices=[
            ('revenue', 'Revenue'),
            ('leads', 'Leads'),
            ('conversion', 'Conversion'),
            ('activity', 'Activity'),
            ('custom', 'Custom'),
        ]
    )
    
    # Metric Configuration
    metric_type = models.CharField(
        max_length=20,
        choices=[
            ('base', 'Base Metric'),
            ('derived', 'Derived Metric'),
            ('aggregate', 'Aggregate Metric'),
        ]
    )
    
    # Computation Details
    data_source = models.CharField(
        max_length=100,
        help_text="Source table/model for base metrics"
    )
    calculation_formula = models.TextField(
        help_text="SQL or Python expression for calculation"
    )
    aggregation_method = models.CharField(
        max_length=20,
        choices=[
            ('sum', 'Sum'),
            ('avg', 'Average'),
            ('count', 'Count'),
            ('min', 'Minimum'),
            ('max', 'Maximum'),
            ('custom', 'Custom'),
        ],
        null=True,
        blank=True
    )
    
    # Metadata
    unit = models.CharField(max_length=50, default='')
    format_pattern = models.CharField(
        max_length=50,
        default='',
        help_text="Display format (e.g., '${:,.2f}', '{:.2%}')"
    )
    
    # Dependencies (for derived metrics)
    dependencies = models.JSONField(
        default=list,
        help_text="List of metric names this metric depends on"
    )
    
    # Lineage tracking
    version = models.IntegerField(default=1)
    parent_metric = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='versions'
    )
    
    # Access control
    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='owned_metrics'
    )
    is_public = models.BooleanField(default=False)
    
    # Cache configuration
    cache_duration = models.IntegerField(
        default=3600,
        help_text="Cache duration in seconds"
    )
    
    class Meta:
        db_table = 'metric_definition'
        ordering = ['category', 'name']
        indexes = [
            models.Index(fields=['category', 'metric_type']),
            models.Index(fields=['name']),
        ]
    
    def __str__(self):
        return f"{self.display_name} (v{self.version})"
    
    def get_lineage(self) -> List[Dict[str, Any]]:
        """
        Get lineage chain for this metric
        """
        lineage = []
        current = self
        
        while current:
            lineage.append({
                'id': current.id,
                'name': current.name,
                'version': current.version,
                'metric_type': current.metric_type,
                'dependencies': current.dependencies,
            })
            current = current.parent_metric
        
        return lineage
    
    def get_dependency_graph(self) -> Dict[str, List[str]]:
        """
        Build dependency graph for this metric
        """
        graph = {self.name: self.dependencies}
        
        for dep_name in self.dependencies:
            try:
                dep_metric = MetricDefinition.objects.get(
                    name=dep_name,
                    company=self.company
                )
                sub_graph = dep_metric.get_dependency_graph()
                graph.update(sub_graph)
            except MetricDefinition.DoesNotExist:
                pass
        
        return graph


class MetricLineage(CompanyIsolatedModel):
    """
    Track lineage relationships between metrics
    """
    metric = models.ForeignKey(
        MetricDefinition,
        on_delete=models.CASCADE,
        related_name='lineage_records'
    )
    upstream_metric = models.ForeignKey(
        MetricDefinition,
        on_delete=models.CASCADE,
        related_name='downstream_metrics'
    )
    relationship_type = models.CharField(
        max_length=20,
        choices=[
            ('direct', 'Direct Dependency'),
            ('indirect', 'Indirect Dependency'),
            ('derived', 'Derived From'),
        ]
    )
    
    class Meta:
        db_table = 'metric_lineage'
        unique_together = ('metric', 'upstream_metric')
    
    def __str__(self):
        return f"{self.metric.name} <- {self.upstream_metric.name}"


class MetricComputationDAG(CompanyIsolatedModel):
    """
    Directed Acyclic Graph for metric computation ordering
    """
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    
    # DAG Definition
    dag_definition = models.JSONField(
        help_text="DAG structure with nodes and edges"
    )
    
    # Execution order (topologically sorted)
    execution_order = models.JSONField(
        help_text="List of metric names in execution order"
    )
    
    # Versioning
    version = models.IntegerField(default=1)
    parent_dag = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='versions'
    )
    
    # Status
    is_active = models.BooleanField(default=True)
    last_computed = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'metric_computation_dag'
        ordering = ['-version']
    
    def __str__(self):
        return f"{self.name} (v{self.version})"
    
    def validate_dag(self) -> tuple[bool, str]:
        """
        Validate that the DAG is acyclic
        """
        def has_cycle(graph, node, visited, rec_stack):
            visited.add(node)
            rec_stack.add(node)
            
            for neighbor in graph.get(node, []):
                if neighbor not in visited:
                    if has_cycle(graph, neighbor, visited, rec_stack):
                        return True
                elif neighbor in rec_stack:
                    return True
            
            rec_stack.remove(node)
            return False
        
        graph = self.dag_definition.get('edges', {})
        visited = set()
        rec_stack = set()
        
        for node in graph:
            if node not in visited:
                if has_cycle(graph, node, visited, rec_stack):
                    return False, f"Cycle detected involving node: {node}"
        
        return True, "DAG is valid"
    
    def topological_sort(self) -> List[str]:
        """
        Perform topological sort on the DAG
        """
        from collections import deque, defaultdict
        
        graph = self.dag_definition.get('edges', {})
        in_degree = defaultdict(int)
        
        # Calculate in-degrees
        for node in graph:
            if node not in in_degree:
                in_degree[node] = 0
            for neighbor in graph[node]:
                in_degree[neighbor] += 1
        
        # Find all nodes with in-degree 0
        queue = deque([node for node in in_degree if in_degree[node] == 0])
        result = []
        
        while queue:
            node = queue.popleft()
            result.append(node)
            
            for neighbor in graph.get(node, []):
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)
        
        return result
