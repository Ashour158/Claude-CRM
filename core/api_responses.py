# core/api_responses.py
# Standardized API response utilities

from rest_framework.response import Response
from rest_framework import status
from django.utils.translation import gettext_lazy as _


class APIResponse:
    """Standardized API response builder"""
    
    @staticmethod
    def success(data=None, message=None, status_code=status.HTTP_200_OK, **kwargs):
        """Success response"""
        response_data = {
            'success': True,
            'status': status_code,
        }
        
        if message:
            response_data['message'] = message
        
        if data is not None:
            response_data['data'] = data
        
        response_data.update(kwargs)
        return Response(response_data, status=status_code)
    
    @staticmethod
    def error(message, errors=None, status_code=status.HTTP_400_BAD_REQUEST, **kwargs):
        """Error response"""
        response_data = {
            'success': False,
            'status': status_code,
            'message': message,
        }
        
        if errors:
            response_data['errors'] = errors
        
        response_data.update(kwargs)
        return Response(response_data, status=status_code)
    
    @staticmethod
    def created(data=None, message=_('Resource created successfully'), **kwargs):
        """Created response"""
        return APIResponse.success(
            data=data,
            message=message,
            status_code=status.HTTP_201_CREATED,
            **kwargs
        )
    
    @staticmethod
    def updated(data=None, message=_('Resource updated successfully'), **kwargs):
        """Updated response"""
        return APIResponse.success(
            data=data,
            message=message,
            status_code=status.HTTP_200_OK,
            **kwargs
        )
    
    @staticmethod
    def deleted(message=_('Resource deleted successfully'), **kwargs):
        """Deleted response"""
        return APIResponse.success(
            message=message,
            status_code=status.HTTP_204_NO_CONTENT,
            **kwargs
        )
    
    @staticmethod
    def not_found(message=_('Resource not found'), **kwargs):
        """Not found response"""
        return APIResponse.error(
            message=message,
            status_code=status.HTTP_404_NOT_FOUND,
            **kwargs
        )
    
    @staticmethod
    def unauthorized(message=_('Unauthorized access'), **kwargs):
        """Unauthorized response"""
        return APIResponse.error(
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED,
            **kwargs
        )
    
    @staticmethod
    def forbidden(message=_('Forbidden access'), **kwargs):
        """Forbidden response"""
        return APIResponse.error(
            message=message,
            status_code=status.HTTP_403_FORBIDDEN,
            **kwargs
        )
    
    @staticmethod
    def validation_error(errors, message=_('Validation failed'), **kwargs):
        """Validation error response"""
        return APIResponse.error(
            message=message,
            errors=errors,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            **kwargs
        )
    
    @staticmethod
    def server_error(message=_('Internal server error'), **kwargs):
        """Server error response"""
        return APIResponse.error(
            message=message,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            **kwargs
        )
    
    @staticmethod
    def paginated(data, page, page_size, total, message=None, **kwargs):
        """Paginated response"""
        response_data = {
            'success': True,
            'status': status.HTTP_200_OK,
            'data': data,
            'pagination': {
                'page': page,
                'page_size': page_size,
                'total': total,
                'pages': (total + page_size - 1) // page_size if page_size > 0 else 0,
            }
        }
        
        if message:
            response_data['message'] = message
        
        response_data.update(kwargs)
        return Response(response_data, status=status.HTTP_200_OK)
