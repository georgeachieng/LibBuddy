from datetime import datetime
from typing import Optional, Dict, Any, List

from storage.json_store import JSONStore
from utils.validators import validate_rating


# This service owns review CRUD plus rating aggregation.
# Delete it and the whole review feature collapses into dead UI.
class ReviewService:
    def __init__(self):
        # Reviews live in their own file so ratings do not get mixed with book records.
        # Delete this and persistence for reviews is gone.
        self.reviews_store = JSONStore("reviews.json")

    # Add review either creates a new record or updates the user's existing one for that book.
    # Delete it and reviews become read-only fantasy.
    def add_review(self, user_id: int, book_id: int, rating: int, comment: str = "") -> Dict[str, Any]:
        # Type check matters because "5" and 5 should not be treated as the same thing here.
        # Remove it and bad input leaks into rating math.
        if not isinstance(rating, int):
            raise TypeError("Rating must be an integer.")

        # Centralized rating validation keeps bounds consistent app-wide.
        # Delete it and out-of-range ratings start polluting review data.
        if not validate_rating(rating):
            raise ValueError("Rating must be between 1 and 5.")

        # Comment cap stops the JSON file from turning into a text dump.
        # Delete it and users can write giant blobs into review records.
        if comment and len(comment) > 500:
            raise ValueError("Comment cannot exceed 500 characters.")

        # One user gets one review per book. Updates beat duplicates here.
        # Delete this and averages get skewed by duplicate reviews from the same user.
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

    # Direct id lookup keeps update/delete code simple.
    # Delete it and those methods start duplicating search logic.
    def get_review(self, review_id: int) -> Optional[Dict[str, Any]]:
        return self.reviews_store.find_by_id(review_id)

    # This finds the unique review for one user/book pair.
    # Delete it and duplicate prevention stops existing.
    def find_review(self, user_id: int, book_id: int) -> Optional[Dict[str, Any]]:
        reviews = self.reviews_store.all()
        return next(
            (
                r for r in reviews
                if r.get("user_id") == user_id and r.get("book_id") == book_id
            ),
            None
        )

    # Update only mutates fields that were explicitly passed in.
    # Delete it and edit-review behavior is gone.
    def update_review(self, review_id: int, rating: int = None, comment: str = None) -> Dict[str, Any]:
        review = self.get_review(review_id)
        if not review:
            raise ValueError(f"Review ID {review_id} not found.")

        # Build updates incrementally so partial edits do not stomp untouched fields.
        # Remove this and every edit needs to resend the entire record shape.
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

        # Only write if something actually changed.
        # Delete this guard and you do pointless writes for empty edits.
        if updates:
            self.reviews_store.update(review_id, updates)
            review.update(updates)

        return review

    # Delete review removes the record from storage entirely.
    # Delete this method and bad reviews become permanent residents.
    def delete_review(self, review_id: int) -> bool:
        return self.reviews_store.delete(review_id)

    # Per-book review list powers the "view reviews" screen and average calculation.
    # Delete it and review browsing dies.
    def get_book_reviews(self, book_id: int) -> List[Dict[str, Any]]:
        reviews = self.reviews_store.all()
        return [r for r in reviews if r.get("book_id") == book_id]

    # User review history is mostly useful for tests and future profile views.
    # Delete it and that lookup becomes manual every time.
    def get_user_reviews(self, user_id: int) -> List[Dict[str, Any]]:
        reviews = self.reviews_store.all()
        return [r for r in reviews if r.get("user_id") == user_id]

    # Average rating is the summary number users actually care about first.
    # Delete it and every caller has to recalculate the same thing.
    def get_book_rating(self, book_id: int) -> Optional[float]:
        reviews = self.get_book_reviews(book_id)
        if not reviews:
            return None

        # Sum-and-divide is simple, correct, and enough for this project.
        # Delete this and the average display has nothing to show.
        total_rating = sum(r.get("rating", 0) for r in reviews)
        return total_rating / len(reviews)

    # Full review dump mainly helps admin/debug flows.
    # Delete it and global review inspection disappears.
    def list_all_reviews(self) -> List[Dict[str, Any]]:
        return self.reviews_store.all()
