import re


# These helpers keep validation rules in one place.
# Delete them and every service starts inventing its own version of "valid."
def require_non_empty(value: str, field_name: str) -> str:
    # strip-aware emptiness check blocks blank strings and all-whitespace junk.
    # Remove it and the app stores fake values that only look present.
    if not value or not value.strip():
        raise ValueError(f"{field_name} cannot be empty.")
    return value.strip()


# Email validation is basic, but enough for this project.
# Delete it and anything vaguely email-shaped starts getting trusted.
def is_valid_email(email: str) -> bool:
    # Regex keeps the check short and reusable.
    # Remove it and you are back to bad string guessing.
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


# ISBN validation is intentionally lightweight, not bookstore-level strict.
# Delete it and malformed identifiers slide into the catalog.
def is_valid_isbn(isbn: str) -> bool:
    # Normalize separators first because humans love typing them differently.
    # Remove this and valid ISBNs with spaces/hyphens fail for dumb reasons.
    isbn_clean = isbn.replace("-", "").replace(" ", "")
    return len(isbn_clean) in (10, 13) and isbn_clean.isdigit()


# Ratings only make sense on a 1-5 scale in this app.
# Delete it and review math starts accepting nonsense.
def validate_rating(rating: int) -> bool:
    return isinstance(rating, int) and 1 <= rating <= 5
