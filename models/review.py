<<<<<<< HEAD
#write code here
=======
# models/review.py

from datetime import datetime

class Review:
    def __init__(self, review_id: int, user_id: int, book_id: int, rating: int, comment: str = ""):
        self.id = review_id
        self.user_id = user_id
        self.book_id = book_id
        self._rating = None
        self.rating = rating  # use setter for validation
        self.comment = comment  # use setter for validation
        self.created_at = datetime.now().isoformat()

    @property
    def rating(self) -> int:
        return self._rating

    @rating.setter
    def rating(self, value: int):
        if not isinstance(value, int):
            raise TypeError("Rating must be an integer.")
        if value < 1 or value > 5:
            raise ValueError("Rating must be between 1 and 5.")
        self._rating = value

    @property
    def comment(self) -> str:
        return self._comment

    @comment.setter
    def comment(self, value: str):
        # Allow empty comments, but enforce max length
        if len(value) > 500:
            raise ValueError("Comment cannot exceed 500 characters.")
        self._comment = value.strip()
>>>>>>> 7d9e6de (Person/User inheritance,Book + BorrowRecord,properties/setters validation)
