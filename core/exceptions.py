# core/exceptions.py
# Custom exceptions for the CRM system

from rest_framework import status
from rest_framework.exceptions import APIException
from django.core.exceptions import ValidationError
from django.http import JsonResponse
import logging

logger = logging.getLogger(__name__)

class CRMException(APIException):
    """Base exception for CRM system"""
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    default_detail = 'An error occurred in the CRM system'
    default_code = 'crm_error'

class ValidationException(CRMException):
    """Custom validation exception"""
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = 'Validation error'
    default_code = 'validation_error'

class AuthenticationException(CRMException):
    """Authentication related exceptions"""
    status_code = status.HTTP_401_UNAUTHORIZED
    default_detail = 'Authentication failed'
    default_code = 'authentication_error'

class PermissionException(CRMException):
    """Permission related exceptions"""
    status_code = status.HTTP_403_FORBIDDEN
    default_detail = 'Permission denied'
    default_code = 'permission_error'

class CompanyAccessException(CRMException):
    """Company access related exceptions"""
    status_code = status.HTTP_403_FORBIDDEN
    default_detail = 'Access denied to this company'
    default_code = 'company_access_error'

class ResourceNotFoundException(CRMException):
    """Resource not found exceptions"""
    status_code = status.HTTP_404_NOT_FOUND
    default_detail = 'Resource not found'
    default_code = 'not_found_error'

class BusinessLogicException(CRMException):
    """Business logic related exceptions"""
    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    default_detail = 'Business logic error'
    default_code = 'business_logic_error'

class RateLimitException(CRMException):
    """Rate limiting exceptions"""
    status_code = status.HTTP_429_TOO_MANY_REQUESTS
    default_detail = 'Rate limit exceeded'
    default_code = 'rate_limit_error'

class DataIntegrityException(CRMException):
    """Data integrity related exceptions"""
    status_code = status.HTTP_409_CONFLICT
    default_detail = 'Data integrity error'
    default_code = 'data_integrity_error'

class ExternalServiceException(CRMException):
    """External service related exceptions"""
    status_code = status.HTTP_502_BAD_GATEWAY
    default_detail = 'External service error'
    default_code = 'external_service_error'

class WorkflowException(CRMException):
    """Workflow related exceptions"""
    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    default_detail = 'Workflow error'
    default_code = 'workflow_error'

class AuditException(CRMException):
    """Audit logging related exceptions"""
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    default_detail = 'Audit logging error'
    default_code = 'audit_error'

# Specific business exceptions
class LeadConversionException(BusinessLogicException):
    """Lead conversion related exceptions"""
    default_detail = 'Lead conversion failed'
    default_code = 'lead_conversion_error'

class DealStageException(BusinessLogicException):
    """Deal stage transition exceptions"""
    default_detail = 'Invalid deal stage transition'
    default_code = 'deal_stage_error'

class TerritoryAssignmentException(BusinessLogicException):
    """Territory assignment exceptions"""
    default_detail = 'Territory assignment failed'
    default_code = 'territory_assignment_error'

class WorkflowExecutionException(WorkflowException):
    """Workflow execution exceptions"""
    default_detail = 'Workflow execution failed'
    default_code = 'workflow_execution_error'

class DataQualityException(DataIntegrityException):
    """Data quality related exceptions"""
    default_detail = 'Data quality validation failed'
    default_code = 'data_quality_error'

class IntegrationException(ExternalServiceException):
    """Integration related exceptions"""
    default_detail = 'Integration error'
    default_code = 'integration_error'

class EmailServiceException(ExternalServiceException):
    """Email service related exceptions"""
    default_detail = 'Email service error'
    default_code = 'email_service_error'

class FileUploadException(CRMException):
    """File upload related exceptions"""
    status_code = status.HTTP_413_REQUEST_ENTITY_TOO_LARGE
    default_detail = 'File upload error'
    default_code = 'file_upload_error'

class CacheException(CRMException):
    """Cache related exceptions"""
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    default_detail = 'Cache service error'
    default_code = 'cache_error'

class DatabaseException(CRMException):
    """Database related exceptions"""
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    default_detail = 'Database service error'
    default_code = 'database_error'

# Exception handlers
def handle_validation_error(exc, context):
    """Handle validation errors"""
    logger.warning(f"Validation error: {exc}")
    return JsonResponse({
        'error': 'Validation failed',
        'details': exc.detail if hasattr(exc, 'detail') else str(exc),
        'code': 'validation_error'
    }, status=status.HTTP_400_BAD_REQUEST)

def handle_authentication_error(exc, context):
    """Handle authentication errors"""
    logger.warning(f"Authentication error: {exc}")
    return JsonResponse({
        'error': 'Authentication failed',
        'details': 'Invalid credentials or token',
        'code': 'authentication_error'
    }, status=status.HTTP_401_UNAUTHORIZED)

def handle_permission_error(exc, context):
    """Handle permission errors"""
    logger.warning(f"Permission error: {exc}")
    return JsonResponse({
        'error': 'Permission denied',
        'details': 'Insufficient permissions for this action',
        'code': 'permission_error'
    }, status=status.HTTP_403_FORBIDDEN)

def handle_not_found_error(exc, context):
    """Handle not found errors"""
    logger.warning(f"Not found error: {exc}")
    return JsonResponse({
        'error': 'Resource not found',
        'details': 'The requested resource does not exist',
        'code': 'not_found_error'
    }, status=status.HTTP_404_NOT_FOUND)

def handle_rate_limit_error(exc, context):
    """Handle rate limit errors"""
    logger.warning(f"Rate limit error: {exc}")
    return JsonResponse({
        'error': 'Rate limit exceeded',
        'details': 'Too many requests. Please try again later.',
        'code': 'rate_limit_error'
    }, status=status.HTTP_429_TOO_MANY_REQUESTS)

def handle_business_logic_error(exc, context):
    """Handle business logic errors"""
    logger.warning(f"Business logic error: {exc}")
    return JsonResponse({
        'error': 'Business logic error',
        'details': str(exc),
        'code': 'business_logic_error'
    }, status=status.HTTP_422_UNPROCESSABLE_ENTITY)

def handle_data_integrity_error(exc, context):
    """Handle data integrity errors"""
    logger.warning(f"Data integrity error: {exc}")
    return JsonResponse({
        'error': 'Data integrity error',
        'details': 'The operation conflicts with existing data',
        'code': 'data_integrity_error'
    }, status=status.HTTP_409_CONFLICT)

def handle_external_service_error(exc, context):
    """Handle external service errors"""
    logger.error(f"External service error: {exc}")
    return JsonResponse({
        'error': 'External service error',
        'details': 'An external service is currently unavailable',
        'code': 'external_service_error'
    }, status=status.HTTP_502_BAD_GATEWAY)

def handle_workflow_error(exc, context):
    """Handle workflow errors"""
    logger.warning(f"Workflow error: {exc}")
    return JsonResponse({
        'error': 'Workflow error',
        'details': str(exc),
        'code': 'workflow_error'
    }, status=status.HTTP_422_UNPROCESSABLE_ENTITY)

def handle_generic_error(exc, context):
    """Handle generic errors"""
    logger.error(f"Generic error: {exc}")
    return JsonResponse({
        'error': 'Internal server error',
        'details': 'An unexpected error occurred',
        'code': 'internal_error'
    }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# Exception handler mapping
EXCEPTION_HANDLERS = {
    ValidationError: handle_validation_error,
    AuthenticationException: handle_authentication_error,
    PermissionException: handle_permission_error,
    ResourceNotFoundException: handle_not_found_error,
    RateLimitException: handle_rate_limit_error,
    BusinessLogicException: handle_business_logic_error,
    DataIntegrityException: handle_data_integrity_error,
    ExternalServiceException: handle_external_service_error,
    WorkflowException: handle_workflow_error,
    Exception: handle_generic_error
}

# Utility functions for raising exceptions
def raise_validation_error(message, details=None):
    """Raise a validation error"""
    exc = ValidationException(message)
    if details:
        exc.detail = details
    raise exc

def raise_authentication_error(message="Authentication failed"):
    """Raise an authentication error"""
    raise AuthenticationException(message)

def raise_permission_error(message="Permission denied"):
    """Raise a permission error"""
    raise PermissionException(message)

def raise_company_access_error(message="Access denied to this company"):
    """Raise a company access error"""
    raise CompanyAccessException(message)

def raise_not_found_error(message="Resource not found"):
    """Raise a not found error"""
    raise ResourceNotFoundException(message)

def raise_business_logic_error(message, details=None):
    """Raise a business logic error"""
    exc = BusinessLogicException(message)
    if details:
        exc.detail = details
    raise exc

def raise_rate_limit_error(message="Rate limit exceeded"):
    """Raise a rate limit error"""
    raise RateLimitException(message)

def raise_data_integrity_error(message="Data integrity error"):
    """Raise a data integrity error"""
    raise DataIntegrityException(message)

def raise_external_service_error(message="External service error"):
    """Raise an external service error"""
    raise ExternalServiceException(message)

def raise_workflow_error(message="Workflow error"):
    """Raise a workflow error"""
    raise WorkflowException(message)

# Business logic specific exceptions
def raise_lead_conversion_error(message="Lead conversion failed"):
    """Raise a lead conversion error"""
    raise LeadConversionException(message)

def raise_deal_stage_error(message="Invalid deal stage transition"):
    """Raise a deal stage error"""
    raise DealStageException(message)

def raise_territory_assignment_error(message="Territory assignment failed"):
    """Raise a territory assignment error"""
    raise TerritoryAssignmentException(message)

def raise_workflow_execution_error(message="Workflow execution failed"):
    """Raise a workflow execution error"""
    raise WorkflowExecutionException(message)

def raise_data_quality_error(message="Data quality validation failed"):
    """Raise a data quality error"""
    raise DataQualityException(message)

def raise_integration_error(message="Integration error"):
    """Raise an integration error"""
    raise IntegrationException(message)

def raise_email_service_error(message="Email service error"):
    """Raise an email service error"""
    raise EmailServiceException(message)

def raise_file_upload_error(message="File upload error"):
    """Raise a file upload error"""
    raise FileUploadException(message)

def raise_cache_error(message="Cache service error"):
    """Raise a cache error"""
    raise CacheException(message)

def raise_database_error(message="Database service error"):
    """Raise a database error"""
    raise DatabaseException(message)
