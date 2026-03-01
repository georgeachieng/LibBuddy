"""Review service for LibBuddy.

Person 2 scope - Stub implementation for CLI testing.
"""

import os
from datetime import datetime
from typing import Any

# Ensure we can import from sibling packages
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from storage.json_store import JsonStore


class ReviewService:
    """Handles book reviews and ratings."""

    def __init__(self) -> None:
        data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
        self.review_store = JsonStore(os.path.join(data_dir, "reviews.json"))

    def add_review(self, user_id: int, book_id: int, rating: int, comment: str = "") -> dict[str, Any] | None:
        """Add a review for a book."""
        # Validate rating
        if not 1 <= rating <= 5:
            return None

        # Check if user already reviewed this book
        existing = self.review_store.find_by(user_id=user_id, book_id=book_id)
        if existing:
            # Update existing review
            self.review_store.update(existing[0]["id"], {
                "rating": rating,
                "comment": comment,
                "updated_at": datetime.now().isoformat(),
            })
            return self.review_store.find_by_id(existing[0]["id"])

        review = {
            "user_id": user_id,
            "book_id": book_id,
            "rating": rating,
            "comment": comment,
            "created_at": datetime.now().isoformat(),
        }
        return self.review_store.add(review)

    def get_book_reviews(self, book_id: int) -> list[dict[str, Any]]:
        """Get all reviews for a book."""
        return self.review_store.find_by(book_id=book_id)

    def get_book_average_rating(self, book_id: int) -> float | None:
        """Get the average rating for a book."""
        reviews = self.get_book_reviews(book_id)
        if not reviews:
            return None
        return sum(r.get("rating", 0) for r in reviews) / len(reviews)

    def get_user_reviews(self, user_id: int) -> list[dict[str, Any]]:
        """Get all reviews by a user."""
        return self.review_store.find_by(user_id=user_id)

    def delete_review(self, review_id: int) -> bool:
        """Delete a review."""
        return self.review_store.delete(review_id)
