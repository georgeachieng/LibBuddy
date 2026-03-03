from datetime import datetime
from typing import Optional, Dict, Any, List

from storage.json_store import JSONStore
from utils.validators import validate_rating


class ReviewService:
    def __init__(self):
        self.reviews_store = JSONStore("reviews.json")

        self.records_store = JSONStore("borrow_records.json")

    def user_has_borrowed_book(self, user_id: int, book_id: int) -> bool:
        records = self.records_store.all()
        return any(
            record.get("user_id") == user_id and record.get("book_id") == book_id
            for record in records
        )

    def add_review(self, user_id: int, book_id: int, rating: int, comment: str = "") -> Dict[str, Any]:
        if not isinstance(rating, int):
            raise TypeError("Rating must be an integer.")

        if not self.user_has_borrowed_book(user_id, book_id):
            raise PermissionError("You can only review books you have borrowed.")

        if not validate_rating(rating):
            raise ValueError("Rating must be between 1 and 5.")

        if comment and len(comment) > 500:
            raise ValueError("Comment cannot exceed 500 characters.")

        existing = self.find_review(user_id, book_id)
        if existing:
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
        return self.reviews_store.find_by_id(review_id)

    def find_review(self, user_id: int, book_id: int) -> Optional[Dict[str, Any]]:
        reviews = self.reviews_store.all()
        return next(
            (
                r for r in reviews
                if r.get("user_id") == user_id and r.get("book_id") == book_id
            ),
            None
        )

    def update_review(self, review_id: int, rating: int = None, comment: str = None) -> Dict[str, Any]:
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
        return self.reviews_store.delete(review_id)

    def get_book_reviews(self, book_id: int) -> List[Dict[str, Any]]:
        reviews = self.reviews_store.all()
        return [r for r in reviews if r.get("book_id") == book_id]

    def get_user_reviews(self, user_id: int) -> List[Dict[str, Any]]:
        reviews = self.reviews_store.all()
        return [r for r in reviews if r.get("user_id") == user_id]

    def get_book_rating(self, book_id: int) -> Optional[float]:
        reviews = self.get_book_reviews(book_id)
        if not reviews:
            return None

        total_rating = sum(r.get("rating", 0) for r in reviews)
        return total_rating / len(reviews)

    def get_book_average_rating(self, book_id: int) -> Optional[float]:
        return self.get_book_rating(book_id)

    def average_rating(self, book_id: int) -> Optional[float]:
        return self.get_book_rating(book_id)

    def list_all_reviews(self) -> List[Dict[str, Any]]:
        return self.reviews_store.all()

    def list_recent_reviews(self, limit: int = 10) -> List[Dict[str, Any]]:
        reviews = self.reviews_store.all()
        reviews.sort(key=lambda review: review.get("created_at", ""), reverse=True)
        return reviews[:limit]
