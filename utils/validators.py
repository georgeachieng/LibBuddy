"""Validation utilities for LibBuddy."""

import re


def require_non_empty(value: str, field_name: str) -> str:
    """Validate that a string value is not empty.
    
    Args:
        value: The string to validate
        field_name: The name of the field (for error messages)
        
    Returns:
        The trimmed value if valid
        
    Raises:
        ValueError: If the value is empty or whitespace-only
    """
    if not value or not value.strip():
        raise ValueError(f"{field_name} cannot be empty.")
    return value.strip()


def is_valid_email(email: str) -> bool:
    """Validate email format.
    
    Args:
        email: The email address to validate
        
    Returns:
        True if the email is valid, False otherwise
    """
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def is_valid_isbn(isbn: str) -> bool:
    """Validate ISBN format (basic check).
    
    Args:
        isbn: The ISBN to validate
        
    Returns:
        True if the ISBN is valid, False otherwise
    """
    # Remove hyphens and spaces
    isbn_clean = isbn.replace("-", "").replace(" ", "")
    # Accept ISBN-10 or ISBN-13
    return len(isbn_clean) in (10, 13) and isbn_clean.isdigit()


def validate_rating(rating: int) -> bool:
    """Validate that rating is between 1 and 5.
    
    Args:
        rating: The rating value to validate
        
    Returns:
        True if the rating is valid, False otherwise
    """
    return isinstance(rating, int) and 1 <= rating <= 5