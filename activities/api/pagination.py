# activities/api/pagination.py
"""DRF pagination classes for activity-related endpoints."""

from rest_framework.pagination import PageNumberPagination


class TimelinePagination(PageNumberPagination):
    """
    Pagination class for timeline endpoint.
    
    Accepts ?page= parameter for pagination.
    Default page size: 50
    Maximum page size: 100
    """
    page_size = 50
    page_size_query_param = 'page_size'
    max_page_size = 100
