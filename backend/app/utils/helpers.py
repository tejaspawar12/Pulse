"""
Helper utilities for common operations.
"""


def to_bool(value: any) -> bool:
    """
    Robust boolean normalizer.
    Converts various types to proper Python bool.
    
    Args:
        value: Any value to convert to bool
        
    Returns:
        bool: Proper boolean value
        
    Examples:
        >>> to_bool(True)
        True
        >>> to_bool("true")
        True
        >>> to_bool("1")
        True
        >>> to_bool(0)
        False
        >>> to_bool(None)
        False
    """
    if isinstance(value, bool):
        return value
    
    if isinstance(value, str):
        return value.lower() in ('true', '1', 'yes', 'on')
    
    if isinstance(value, (int, float)):
        return bool(value)
    
    return bool(value)
