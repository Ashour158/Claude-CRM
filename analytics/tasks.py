# analytics/tasks.py
# Celery tasks for analytics and performance features

import logging
from celery import shared_task
from django.utils import timezone

logger = logging.getLogger(__name__)


@shared_task(name='analytics.precompute_facets')
def precompute_facets_task():
    """
    Precompute search facets for all entity types.
    Run every 5 minutes via Celery Beat.
    """
    from analytics.search_optimization import FacetPrecomputer, FacetConfig
    from django.apps import apps
    
    logger.info("Starting facet precomputation")
    
    # Entity type to model mapping
    entity_models = {
        'lead': 'leads.Lead',
        'deal': 'deals.Deal',
        'account': 'accounts.Account',
        'contact': 'contacts.Contact',
    }
    
    results = []
    
    for entity_type, model_path in entity_models.items():
        try:
            # Get model class
            app_label, model_name = model_path.split('.')
            model_class = apps.get_model(app_label, model_name)
            
            # Get facet configs
            common_facets = FacetConfig.COMMON_FACETS
            entity_facets = FacetConfig.ENTITY_FACETS.get(entity_type, {})
            all_facets = {**common_facets, **entity_facets}
            
            # Precompute each facet
            for facet_name, facet_config in all_facets.items():
                try:
                    result = FacetPrecomputer.precompute_facet(
                        entity_type, facet_name, facet_config, model_class
                    )
                    
                    # Cache the result
                    FacetPrecomputer.cache_facet(entity_type, facet_name, result)
                    
                    results.append({
                        'entity': entity_type,
                        'facet': facet_name,
                        'status': 'success'
                    })
                except Exception as e:
                    logger.error(f"Error precomputing facet {entity_type}.{facet_name}: {e}")
                    results.append({
                        'entity': entity_type,
                        'facet': facet_name,
                        'status': 'error',
                        'error': str(e)
                    })
        
        except Exception as e:
            logger.error(f"Error processing entity {entity_type}: {e}")
    
    logger.info(f"Facet precomputation complete: {len(results)} facets processed")
    return results


@shared_task(name='analytics.precompute_aggregates')
def precompute_aggregates_task():
    """
    Precompute report aggregates for all entity types.
    Run every 10 minutes via Celery Beat.
    """
    from analytics.reporting_optimization import ReportingOptimizer, ReportingPresets
    from django.apps import apps
    
    logger.info("Starting aggregate precomputation")
    
    # Entity type to model mapping
    entity_models = {
        'lead': 'leads.Lead',
        'deal': 'deals.Deal',
        'account': 'accounts.Account',
    }
    
    results = []
    
    for entity_type, model_path in entity_models.items():
        try:
            # Get model class
            app_label, model_name = model_path.split('.')
            model_class = apps.get_model(app_label, model_name)
            
            # Precompute common reports
            ReportingOptimizer.precompute_common_reports(entity_type, model_class)
            
            results.append({
                'entity': entity_type,
                'status': 'success'
            })
        
        except Exception as e:
            logger.error(f"Error precomputing aggregates for {entity_type}: {e}")
            results.append({
                'entity': entity_type,
                'status': 'error',
                'error': str(e)
            })
    
    logger.info(f"Aggregate precomputation complete: {len(results)} entities processed")
    return results


@shared_task(name='system_config.audit_maintenance')
def audit_maintenance_task():
    """
    Run audit log maintenance.
    Run daily at 2 AM via Celery Beat.
    """
    from system_config.audit_partitioning import AuditMaintenanceScheduler
    
    logger.info("Starting audit log maintenance")
    
    try:
        results = AuditMaintenanceScheduler.run_maintenance()
        
        logger.info(
            f"Audit maintenance complete: "
            f"{len(results.get('partitions_created', []))} partitions created, "
            f"{len(results.get('partitions_archived', []))} partitions archived"
        )
        
        return results
    
    except Exception as e:
        logger.error(f"Error in audit maintenance: {e}")
        return {'success': False, 'error': str(e)}


@shared_task(name='workflow.execute_step')
def execute_workflow_step_task(workflow_id, step_config, context):
    """
    Execute a single workflow step.
    Routed to appropriate queue based on step type.
    """
    from workflow.partitioning import WorkflowExecutor, WorkflowMetrics
    from core.prometheus_metrics import record_workflow_execution
    import time
    
    logger.info(f"Executing workflow step: {step_config.get('name')}")
    
    start_time = time.time()
    
    try:
        result = WorkflowExecutor.execute_step(step_config, context)
        
        duration = time.time() - start_time
        
        # Record metrics
        WorkflowMetrics.record_step_execution(
            step_config.get('name'),
            step_config.get('_queue'),
            int(duration * 1000),
            True
        )
        
        record_workflow_execution(
            step_config.get('type', 'unknown'),
            'completed',
            duration
        )
        
        logger.info(f"Step completed: {step_config.get('name')} in {duration:.2f}s")
        
        return result
    
    except Exception as e:
        duration = time.time() - start_time
        
        logger.error(f"Step failed: {step_config.get('name')}: {e}")
        
        record_workflow_execution(
            step_config.get('type', 'unknown'),
            'failed',
            duration
        )
        
        raise


@shared_task(name='master_data.background_export')
def background_export_task(export_id, queryset_params, format, fields, user_id):
    """
    Execute background export operation.
    Used for large exports that would timeout in HTTP request.
    """
    from master_data.streaming_export import ExportManager, ExportProgress
    from django.apps import apps
    import time
    
    logger.info(f"Starting background export: {export_id}")
    
    # Track progress
    ExportProgress.track_export(export_id, None, format, user_id)
    
    start_time = time.time()
    
    try:
        # Reconstruct queryset
        model_class = apps.get_model(queryset_params['app'], queryset_params['model'])
        queryset = model_class.objects.filter(**queryset_params.get('filters', {}))
        
        # Create exporter
        exporter = ExportManager.create_exporter(format, queryset, fields)
        
        # TODO: Save export to file storage (S3, local, etc.)
        # For now, just count records
        record_count = 0
        for record in exporter.iter_records():
            record_count += 1
            
            if record_count % 1000 == 0:
                ExportProgress.update_progress(export_id, record_count)
        
        duration = time.time() - start_time
        
        # Complete export
        file_url = f"/exports/{export_id}.{format}.gz"  # TODO: actual file URL
        ExportProgress.complete_export(export_id, file_url)
        
        logger.info(
            f"Export complete: {export_id} - "
            f"{record_count} records in {duration:.2f}s"
        )
        
        return {
            'export_id': export_id,
            'status': 'completed',
            'record_count': record_count,
            'duration': duration,
            'file_url': file_url
        }
    
    except Exception as e:
        logger.error(f"Export failed: {export_id}: {e}")
        ExportProgress.fail_export(export_id, str(e))
        raise


@shared_task(name='analytics.index_vectors')
def index_vectors_task(documents):
    """
    Bulk index vectors for similarity search.
    """
    from analytics.vector_search import vector_search_manager
    
    logger.info(f"Indexing {len(documents)} vectors")
    
    try:
        success = vector_search_manager.bulk_index(documents)
        
        if success:
            logger.info(f"Successfully indexed {len(documents)} vectors")
        else:
            logger.warning(f"Vector indexing completed with warnings")
        
        return {
            'status': 'success' if success else 'partial',
            'document_count': len(documents)
        }
    
    except Exception as e:
        logger.error(f"Vector indexing failed: {e}")
        raise


@shared_task(name='analytics.warm_caches')
def warm_caches_task():
    """
    Warm various caches during off-peak hours.
    Run daily at 3 AM via Celery Beat.
    """
    from core.cache_strategies import CacheWarming
    from sharing.cache import SharingRuleCache
    
    logger.info("Starting cache warming")
    
    results = []
    
    # Warm sharing rule cache
    # TODO: Get list of active companies
    # for company_id in active_companies:
    #     for object_type in ['lead', 'deal', 'account', 'contact']:
    #         SharingRuleCache warm for company/object_type
    
    # Warm facet cache
    # Already done by precompute_facets_task
    
    # Warm aggregate cache
    # Already done by precompute_aggregates_task
    
    logger.info("Cache warming complete")
    
    return results
