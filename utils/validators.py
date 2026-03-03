import re


def require_non_empty(value: str, field_name: str) -> str:
    if not value or not value.strip():
        raise ValueError(f"{field_name} cannot be empty.")
    return value.strip()


def is_valid_email(email: str) -> bool:
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def is_valid_isbn(isbn: str) -> bool:
    isbn_clean = isbn.replace("-", "").replace(" ", "")
    return len(isbn_clean) in (10, 13) and isbn_clean.isdigit()


def validate_rating(rating: int) -> bool:
    return isinstance(rating, int) and 1 <= rating <= 5