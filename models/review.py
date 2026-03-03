"""Review model for LibBuddy."""

from datetime import datetime


# This model keeps rating/comment validation close to the data itself.
# Delete it and review safety depends entirely on callers behaving perfectly. Bold assumption.
class Review:
    """Represents a book review."""

    def __init__(self, review_id: int, user_id: int, book_id: int, rating: int, comment: str = ""):
        """Initialize a Review.

        Args:
            review_id: The review's ID
            user_id: The ID of the reviewer
            book_id: The ID of the reviewed book
            rating: The rating (1-5)
            comment: Optional comment text
        """
        self.id = review_id
        self.user_id = user_id
        self.book_id = book_id

        # Start blank so the setter does the validation instead of trusting constructor input.
        # Delete this and invalid ratings can bypass the guard.
        self._rating = None

        # Route through setters on purpose. That is not decorative.
        # Delete these and you skip validation during object creation.
        self.rating = rating
        self.comment = comment

        # Timestamp helps sort or audit reviews later.
        # Delete it and review chronology disappears.
        self.created_at = datetime.now().isoformat()

    @property
    def rating(self) -> int:
        """Get the rating."""
        return self._rating

    @rating.setter
    def rating(self, value: int) -> None:
        """Set the rating."""
        if not isinstance(value, int):
            raise TypeError("Rating must be an integer.")
        if value < 1 or value > 5:
            raise ValueError("Rating must be between 1 and 5.")
        self._rating = value

    @property
    def comment(self) -> str:
        """Get the comment."""
        return self._comment

    @comment.setter
    def comment(self, value: str) -> None:
        """Set the comment."""
        # Limit comment size so one review cannot bloat storage or output.
        # Delete this and users can dump novels into a single record.
        if len(value) > 500:
            raise ValueError("Comment cannot exceed 500 characters.")
        self._comment = value.strip() if value else ""
