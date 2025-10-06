# realtime/signals.py
# Django signals integration for automatic event publishing

import logging
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .event_bus import get_event_bus

logger = logging.getLogger(__name__)


def publish_model_event(instance, event_action, **kwargs):
    """
    Publish an event for a model instance
    
    Args:
        instance: Model instance
        event_action: Action type (created, updated, deleted)
        **kwargs: Additional event data
    """
    try:
        # Determine model type and event type
        model_name = instance._meta.model_name
        app_label = instance._meta.app_label
        event_type = f"{app_label}.{model_name}.{event_action}"
        
        # Build event data
        event_data = {
            'id': instance.pk,
            'model': model_name,
            'app': app_label,
            **kwargs
        }
        
        # Add company context if available
        if hasattr(instance, 'company_id'):
            event_data['company_id'] = instance.company_id
        
        # Add user context if available
        if hasattr(instance, 'owner_id'):
            event_data['owner_id'] = instance.owner_id
        
        # Get GDPR context
        gdpr_context = {
            'consent': True,  # Should be retrieved from user settings
            'retention_days': 365
        }
        
        # Publish event
        event_bus = get_event_bus()
        event_bus.publish_event(
            event_type=event_type,
            data=event_data,
            gdpr_context=gdpr_context
        )
        
        logger.debug(f"Published event: {event_type} for {model_name}#{instance.pk}")
        
    except Exception as e:
        logger.error(f"Error publishing event: {e}", exc_info=True)


# Example signal handlers for Deal model
# These can be enabled by importing this module in the app's __init__.py or ready() method

def connect_deal_signals():
    """Connect signals for Deal model"""
    from deals.models import Deal
    
    @receiver(post_save, sender=Deal)
    def on_deal_saved(sender, instance, created, **kwargs):
        """Handle Deal save events"""
        action = 'created' if created else 'updated'
        
        # Prepare event data
        event_data = {
            'deal_name': instance.name,
            'amount': str(instance.amount) if hasattr(instance, 'amount') else None,
            'stage': instance.stage if hasattr(instance, 'stage') else None,
        }
        
        publish_model_event(instance, action, **event_data)
    
    @receiver(post_delete, sender=Deal)
    def on_deal_deleted(sender, instance, **kwargs):
        """Handle Deal delete events"""
        publish_model_event(instance, 'deleted')


def connect_activity_signals():
    """Connect signals for Activity model"""
    from activities.models import Activity
    
    @receiver(post_save, sender=Activity)
    def on_activity_saved(sender, instance, created, **kwargs):
        """Handle Activity save events"""
        action = 'created' if created else 'updated'
        
        event_data = {
            'activity_type': instance.activity_type if hasattr(instance, 'activity_type') else None,
            'subject': instance.subject if hasattr(instance, 'subject') else None,
            'status': instance.status if hasattr(instance, 'status') else None,
        }
        
        publish_model_event(instance, action, **event_data)


def connect_timeline_signals():
    """Connect signals for timeline events"""
    # Timeline events can be triggered from various models
    # This is a placeholder for custom timeline event logic
    pass


# Auto-connect signals when module is imported
# Comment these out if you want manual control
# connect_deal_signals()
# connect_activity_signals()
# connect_timeline_signals()
