"""
Shared utility functions.
"""

from typing import Any, Dict, List


def clean_dict(data: Dict[str, Any], remove_none: bool = True) -> Dict[str, Any]:
    """
    Clean a dictionary by removing None values or empty strings.
    
    Args:
        data: Dictionary to clean
        remove_none: Whether to remove None values
        
    Returns:
        Cleaned dictionary
    """
    if remove_none:
        return {k: v for k, v in data.items() if v is not None}
    return data


def chunk_list(lst: List[Any], chunk_size: int) -> List[List[Any]]:
    """
    Split a list into chunks of specified size.
    
    Args:
        lst: List to chunk
        chunk_size: Size of each chunk
        
    Returns:
        List of chunks
    """
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]
