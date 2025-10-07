# compliance/dsr_processor.py
# Data Subject Rights request processor

from typing import Dict, List
from django.db.models import Q
from django.utils import timezone
from django.apps import apps
import json


class DSRProcessor:
    """Processor for Data Subject Rights requests"""
    
    # Entities that may contain personal data
    PERSONAL_DATA_ENTITIES = [
        'Contact', 'Lead', 'Account', 'Activity', 'Deal'
    ]
    
    def process_request(self, dsr, user) -> Dict:
        """
        Process DSR request
        
        Args:
            dsr: DataSubjectRequest instance
            user: User processing the request
            
        Returns:
            Dictionary with processing results
        """
        result = {
            'success': True,
            'request_type': dsr.request_type,
            'entities_processed': [],
            'records_affected': 0,
            'audit_data': {},
            'errors': []
        }
        
        try:
            if dsr.request_type == 'erasure':
                result = self._process_erasure(dsr)
            elif dsr.request_type == 'access':
                result = self._process_access(dsr)
            elif dsr.request_type == 'portability':
                result = self._process_portability(dsr)
            elif dsr.request_type == 'rectification':
                result = self._process_rectification(dsr)
            else:
                result['success'] = False
                result['errors'].append(f"Unsupported request type: {dsr.request_type}")
        
        except Exception as e:
            result['success'] = False
            result['errors'].append(str(e))
        
        return result
    
    def rollback_request(self, dsr) -> Dict:
        """
        Rollback DSR processing
        
        Args:
            dsr: DataSubjectRequest instance
            
        Returns:
            Dictionary with rollback results
        """
        result = {
            'success': True,
            'message': 'DSR rollback initiated',
            'restored_records': 0
        }
        
        if not dsr.can_rollback:
            result['success'] = False
            result['message'] = 'Rollback not available'
            return result
        
        # Restore data from rollback_data
        rollback_data = dsr.rollback_data
        
        if not rollback_data:
            result['success'] = False
            result['message'] = 'No rollback data available'
            return result
        
        # Restore records
        for entity_type, records in rollback_data.items():
            try:
                model = apps.get_model('crm', entity_type)
                for record_data in records:
                    # Restore record
                    model.objects.create(**record_data)
                    result['restored_records'] += 1
            except Exception as e:
                result['success'] = False
                result['message'] = f"Error restoring {entity_type}: {str(e)}"
        
        return result
    
    def _process_erasure(self, dsr) -> Dict:
        """Process right to erasure (deletion)"""
        result = {
            'success': True,
            'entities_processed': [],
            'records_affected': 0,
            'audit_data': {},
            'errors': []
        }
        
        # Store data for potential rollback
        rollback_data = {}
        
        # Determine which entities to process
        entities = dsr.entities_affected or self.PERSONAL_DATA_ENTITIES
        
        for entity_type in entities:
            try:
                # Get model
                model = apps.get_model('crm', entity_type)
                
                # Find records matching the data subject
                records = self._find_subject_records(model, dsr.subject_email, dsr.company)
                
                if records.exists():
                    # Store for rollback
                    rollback_data[entity_type] = list(
                        records.values()
                    )
                    
                    # Delete records
                    count = records.count()
                    records.delete()
                    
                    result['entities_processed'].append(entity_type)
                    result['records_affected'] += count
                    result['audit_data'][entity_type] = {
                        'deleted_count': count,
                        'timestamp': timezone.now().isoformat()
                    }
            
            except Exception as e:
                result['errors'].append(f"Error processing {entity_type}: {str(e)}")
        
        # Store rollback data
        dsr.rollback_data = rollback_data
        dsr.save()
        
        return result
    
    def _process_access(self, dsr) -> Dict:
        """Process right to access (data export)"""
        result = {
            'success': True,
            'entities_processed': [],
            'records_affected': 0,
            'audit_data': {},
            'data': {},
            'errors': []
        }
        
        # Determine which entities to process
        entities = dsr.entities_affected or self.PERSONAL_DATA_ENTITIES
        
        for entity_type in entities:
            try:
                # Get model
                model = apps.get_model('crm', entity_type)
                
                # Find records matching the data subject
                records = self._find_subject_records(model, dsr.subject_email, dsr.company)
                
                if records.exists():
                    # Export data
                    data = list(records.values())
                    
                    result['entities_processed'].append(entity_type)
                    result['records_affected'] += len(data)
                    result['data'][entity_type] = data
                    result['audit_data'][entity_type] = {
                        'exported_count': len(data),
                        'timestamp': timezone.now().isoformat()
                    }
            
            except Exception as e:
                result['errors'].append(f"Error processing {entity_type}: {str(e)}")
        
        return result
    
    def _process_portability(self, dsr) -> Dict:
        """Process right to data portability"""
        # Similar to access but in a machine-readable format
        return self._process_access(dsr)
    
    def _process_rectification(self, dsr) -> Dict:
        """Process right to rectification"""
        result = {
            'success': True,
            'entities_processed': [],
            'records_affected': 0,
            'audit_data': {},
            'message': 'Manual rectification required',
            'errors': []
        }
        
        # Rectification typically requires manual review
        # This method identifies records that need correction
        
        entities = dsr.entities_affected or self.PERSONAL_DATA_ENTITIES
        
        for entity_type in entities:
            try:
                model = apps.get_model('crm', entity_type)
                records = self._find_subject_records(model, dsr.subject_email, dsr.company)
                
                if records.exists():
                    result['entities_processed'].append(entity_type)
                    result['records_affected'] += records.count()
                    result['audit_data'][entity_type] = {
                        'records_found': records.count(),
                        'record_ids': list(records.values_list('id', flat=True))
                    }
            
            except Exception as e:
                result['errors'].append(f"Error processing {entity_type}: {str(e)}")
        
        return result
    
    def _find_subject_records(self, model, email, company):
        """Find records for a data subject"""
        query = Q(company=company)
        
        # Look for email in various fields
        if hasattr(model, 'email'):
            query &= Q(email=email)
        elif hasattr(model, 'contact_email'):
            query &= Q(contact_email=email)
        
        return model.objects.filter(query)
