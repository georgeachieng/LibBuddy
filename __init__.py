"""LibBuddy - A Library Management System.

A CLI-based library management system with user authentication, book management,
borrowing/returning functionality, and book reviews.
"""

from services.auth_service import AuthService
from services.library_service import LibraryService
from services.review_service import ReviewService

__version__ = "1.0.0"
__all__ = ["AuthService", "LibraryService", "ReviewService"]