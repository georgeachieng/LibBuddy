"""Review service for LibBuddy - manages book reviews and ratings."""

from datetime import datetime
from typing import Optional, Dict, Any, List

from storage.json_store import JSONStore
from utils.validators import validate_rating


class ReviewService:
    """Handles book reviews and ratings."""
    
    def __init__(self):
        """Initialize ReviewService with JSON store."""
        self.reviews_store = JSONStore("reviews.json")

    def add_review(self, user_id: int, book_id: int, rating: int, comment: str = "") -> Dict[str, Any]:
        """Add a review for a book.
        
        Args:
            user_id: The reviewer's user ID
            book_id: The book being reviewed ID
            rating: Rating from 1-5
            comment: Optional review comment
            
        Returns:
            Dictionary with the new review's data
            
        Raises:
            ValueError: If validation fails
            TypeError: If rating is not an integer
        """
        if not isinstance(rating, int):
            raise TypeError("Rating must be an integer.")
        
        if not validate_rating(rating):
            raise ValueError("Rating must be between 1 and 5.")
        
        if comment and len(comment) > 500:
            raise ValueError("Comment cannot exceed 500 characters.")
        
        # Check if user already reviewed this book
        existing = self.find_review(user_id, book_id)
        if existing:
            # Update existing review instead
            return self.update_review(existing["id"], rating, comment)
        
        review = {
            "user_id": user_id,
            "book_id": book_id,
            "rating": rating,
            "comment": comment.strip() if comment else "",
            "created_at": datetime.now().isoformat(),
        }
        
        return self.reviews_store.save(review)

    def get_review(self, review_id: int) -> Optional[Dict[str, Any]]:
        """Get a review by ID.
        
        Args:
            review_id: The review's ID
            
        Returns:
            Review dictionary or None if not found
        """
        return self.reviews_store.find_by_id(review_id)

    def find_review(self, user_id: int, book_id: int) -> Optional[Dict[str, Any]]:
        """Find a user's review for a specific book.
        
        Args:
            user_id: The user's ID
            book_id: The book's ID
            
        Returns:
            Review dictionary or None if not found
        """
        reviews = self.reviews_store.all()
        return next(
            (r for r in reviews
             if r.get("user_id") == user_id and r.get("book_id") == book_id),
            None
        )

    def update_review(self, review_id: int, rating: int = None, comment: str = None) -> Dict[str, Any]:
        """Update a review.
        
        Args:
            review_id: The review's ID
            rating: New rating (1-5)
            comment: New comment text
            
        Returns:
            Updated review dictionary
            
        Raises:
            ValueError: If review not found or validation fails
        """
        review = self.get_review(review_id)
        if not review:
            raise ValueError(f"Review ID {review_id} not found.")
        
        updates = {}
        
        if rating is not None:
            if not isinstance(rating, int):
                raise TypeError("Rating must be an integer.")
            if not validate_rating(rating):
                raise ValueError("Rating must be between 1 and 5.")
            updates["rating"] = rating
        
        if comment is not None:
            if len(comment) > 500:
                raise ValueError("Comment cannot exceed 500 characters.")
            updates["comment"] = comment.strip()
        
        if updates:
            self.reviews_store.update(review_id, updates)
            review.update(updates)
        
        return review

    def delete_review(self, review_id: int) -> bool:
        """Delete a review.
        
        Args:
            review_id: The review's ID
            
        Returns:
            True if successful, False otherwise
        """
        return self.reviews_store.delete(review_id)

    def get_book_reviews(self, book_id: int) -> List[Dict[str, Any]]:
        """Get all reviews for a book.
        
        Args:
            book_id: The book's ID
            
        Returns:
            List of reviews for the book
        """
        reviews = self.reviews_store.all()
        return [r for r in reviews if r.get("book_id") == book_id]

    def get_user_reviews(self, user_id: int) -> List[Dict[str, Any]]:
        """Get all reviews by a user.
        
        Args:
            user_id: The user's ID
            
        Returns:
            List of reviews by the user
        """
        reviews = self.reviews_store.all()
        return [r for r in reviews if r.get("user_id") == user_id]

    def get_book_rating(self, book_id: int) -> Optional[float]:
        """Get average rating for a book.
        
        Args:
            book_id: The book's ID
            
        Returns:
            Average rating as float or None if no reviews
        """
        reviews = self.get_book_reviews(book_id)
        if not reviews:
            return None
        
        total_rating = sum(r.get("rating", 0) for r in reviews)
        return total_rating / len(reviews)

    def list_all_reviews(self) -> List[Dict[str, Any]]:
        """Get all reviews in the system.
        
        Returns:
            List of all reviews
        """
        return self.reviews_store.all()