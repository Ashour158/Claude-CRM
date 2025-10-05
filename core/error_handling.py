# core/error_handling.py
# Comprehensive error handling for CRM system

import logging
import traceback
from django.http import JsonResponse, HttpResponseServerError
from django.core.exceptions import ValidationError, PermissionDenied
from django.db import IntegrityError, DatabaseError
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler
from rest_framework.exceptions import APIException, ValidationError as DRFValidationError
from django.utils import timezone
from django.conf import settings
import json

logger = logging.getLogger(__name__)

class CRMException(APIException):
    """Base exception for CRM system"""
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = 'An error occurred in the CRM system'
    default_code = 'crm_error'

class ValidationException(CRMException):
    """Validation error exception"""
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = 'Validation error'
    default_code = 'validation_error'

class PermissionException(CRMException):
    """Permission denied exception"""
    status_code = status.HTTP_403_FORBIDDEN
    default_detail = 'Permission denied'
    default_code = 'permission_denied'

class NotFoundException(CRMException):
    """Resource not found exception"""
    status_code = status.HTTP_404_NOT_FOUND
    default_detail = 'Resource not found'
    default_code = 'not_found'

class ConflictException(CRMException):
    """Resource conflict exception"""
    status_code = status.HTTP_409_CONFLICT
    default_detail = 'Resource conflict'
    default_code = 'conflict'

class ServiceUnavailableException(CRMException):
    """Service unavailable exception"""
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    default_detail = 'Service temporarily unavailable'
    default_code = 'service_unavailable'

class MultiTenantError(CRMException):
    """Multi-tenant error exception"""
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = 'Multi-tenant error'
    default_code = 'multi_tenant_error'

class WorkflowError(CRMException):
    """Workflow error exception"""
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = 'Workflow error'
    default_code = 'workflow_error'

class IntegrationError(CRMException):
    """Integration error exception"""
    status_code = status.HTTP_502_BAD_GATEWAY
    default_detail = 'Integration error'
    default_code = 'integration_error'

class DataQualityError(CRMException):
    """Data quality error exception"""
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = 'Data quality error'
    default_code = 'data_quality_error'

def custom_exception_handler(exc, context):
    """Custom exception handler for DRF"""
    # Get the standard error response
    response = exception_handler(exc, context)
    
    if response is not None:
        # Log the error
        logger.error(f"API Error: {exc.__class__.__name__}: {str(exc)}")
        
        # Add custom error details
        custom_response_data = {
            'error': {
                'type': exc.__class__.__name__,
                'message': str(exc),
                'timestamp': timezone.now().isoformat(),
                'status_code': response.status_code
            }
        }
        
        # Add validation errors if available
        if hasattr(exc, 'detail'):
            if isinstance(exc.detail, dict):
                custom_response_data['error']['details'] = exc.detail
            elif isinstance(exc.detail, list):
                custom_response_data['error']['details'] = exc.detail
        
        # Add request context
        if 'request' in context:
            request = context['request']
            custom_response_data['error']['request_id'] = getattr(request, 'id', None)
            custom_response_data['error']['user_id'] = getattr(request.user, 'id', None) if hasattr(request, 'user') else None
        
        response.data = custom_response_data
    
    return response

def handle_django_exception(request, exception):
    """Handle Django exceptions"""
    logger.error(f"Django Error: {exception.__class__.__name__}: {str(exception)}")
    
    # Create error response
    error_data = {
        'error': {
            'type': exception.__class__.__name__,
            'message': str(exception),
            'timestamp': timezone.now().isoformat(),
            'status_code': 500
        }
    }
    
    # Handle specific exceptions
    if isinstance(exception, ValidationError):
        error_data['error']['type'] = 'ValidationError'
        error_data['error']['status_code'] = 400
        error_data['error']['details'] = exception.message_dict if hasattr(exception, 'message_dict') else str(exception)
    
    elif isinstance(exception, PermissionDenied):
        error_data['error']['type'] = 'PermissionDenied'
        error_data['error']['status_code'] = 403
    
    elif isinstance(exception, IntegrityError):
        error_data['error']['type'] = 'IntegrityError'
        error_data['error']['status_code'] = 400
        error_data['error']['message'] = 'Database integrity error'
    
    elif isinstance(exception, DatabaseError):
        error_data['error']['type'] = 'DatabaseError'
        error_data['error']['status_code'] = 500
        error_data['error']['message'] = 'Database error'
    
    return JsonResponse(error_data, status=error_data['error']['status_code'])

def handle_500_error(request):
    """Handle 500 errors"""
    logger.error("Internal Server Error", exc_info=True)
    
    error_data = {
        'error': {
            'type': 'InternalServerError',
            'message': 'Internal server error',
            'timestamp': timezone.now().isoformat(),
            'status_code': 500
        }
    }
    
    if settings.DEBUG:
        error_data['error']['traceback'] = traceback.format_exc()
    
    return JsonResponse(error_data, status=500)

class ErrorHandler:
    """Centralized error handling class"""
    
    @staticmethod
    def handle_validation_error(exception, context=None):
        """Handle validation errors"""
        logger.warning(f"Validation Error: {str(exception)}")
        
        error_data = {
            'error': {
                'type': 'ValidationError',
                'message': 'Validation failed',
                'timestamp': timezone.now().isoformat(),
                'status_code': 400,
                'details': exception.message_dict if hasattr(exception, 'message_dict') else str(exception)
            }
        }
        
        return JsonResponse(error_data, status=400)
    
    @staticmethod
    def handle_permission_error(exception, context=None):
        """Handle permission errors"""
        logger.warning(f"Permission Error: {str(exception)}")
        
        error_data = {
            'error': {
                'type': 'PermissionDenied',
                'message': 'Permission denied',
                'timestamp': timezone.now().isoformat(),
                'status_code': 403
            }
        }
        
        return JsonResponse(error_data, status=403)
    
    @staticmethod
    def handle_database_error(exception, context=None):
        """Handle database errors"""
        logger.error(f"Database Error: {str(exception)}")
        
        error_data = {
            'error': {
                'type': 'DatabaseError',
                'message': 'Database error occurred',
                'timestamp': timezone.now().isoformat(),
                'status_code': 500
            }
        }
        
        return JsonResponse(error_data, status=500)
    
    @staticmethod
    def handle_integration_error(exception, context=None):
        """Handle integration errors"""
        logger.error(f"Integration Error: {str(exception)}")
        
        error_data = {
            'error': {
                'type': 'IntegrationError',
                'message': 'External service error',
                'timestamp': timezone.now().isoformat(),
                'status_code': 502
            }
        }
        
        return JsonResponse(error_data, status=502)
    
    @staticmethod
    def handle_generic_error(exception, context=None):
        """Handle generic errors"""
        logger.error(f"Generic Error: {str(exception)}", exc_info=True)
        
        error_data = {
            'error': {
                'type': exception.__class__.__name__,
                'message': str(exception),
                'timestamp': timezone.now().isoformat(),
                'status_code': 500
            }
        }
        
        if settings.DEBUG:
            error_data['error']['traceback'] = traceback.format_exc()
        
        return JsonResponse(error_data, status=500)

# Error handling decorators
def handle_exceptions(func):
    """Decorator to handle exceptions in functions"""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ValidationError as e:
            return ErrorHandler.handle_validation_error(e)
        except PermissionDenied as e:
            return ErrorHandler.handle_permission_error(e)
        except (IntegrityError, DatabaseError) as e:
            return ErrorHandler.handle_database_error(e)
        except Exception as e:
            return ErrorHandler.handle_generic_error(e)
    
    return wrapper

def handle_api_exceptions(func):
    """Decorator to handle exceptions in API views"""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ValidationError as e:
            raise ValidationException(str(e))
        except PermissionDenied as e:
            raise PermissionException(str(e))
        except (IntegrityError, DatabaseError) as e:
            raise ServiceUnavailableException("Database error occurred")
        except Exception as e:
            logger.error(f"Unexpected error in {func.__name__}: {str(e)}", exc_info=True)
            raise CRMException("An unexpected error occurred")
    
    return wrapper

# Error response utilities
def create_error_response(error_type, message, status_code=400, details=None):
    """Create standardized error response"""
    error_data = {
        'error': {
            'type': error_type,
            'message': message,
            'timestamp': timezone.now().isoformat(),
            'status_code': status_code
        }
    }
    
    if details:
        error_data['error']['details'] = details
    
    return JsonResponse(error_data, status=status_code)

def create_validation_error_response(errors):
    """Create validation error response"""
    return create_error_response(
        'ValidationError',
        'Validation failed',
        400,
        errors
    )

def create_permission_error_response(message="Permission denied"):
    """Create permission error response"""
    return create_error_response(
        'PermissionDenied',
        message,
        403
    )

def create_not_found_error_response(message="Resource not found"):
    """Create not found error response"""
    return create_error_response(
        'NotFound',
        message,
        404
    )

def create_conflict_error_response(message="Resource conflict"):
    """Create conflict error response"""
    return create_error_response(
        'Conflict',
        message,
        409
    )

def create_service_unavailable_error_response(message="Service temporarily unavailable"):
    """Create service unavailable error response"""
    return create_error_response(
        'ServiceUnavailable',
        message,
        503
    )
