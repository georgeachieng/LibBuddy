"""BorrowRecord model for LibBuddy."""

from datetime import datetime


class BorrowRecord:
    """Represents a book borrowing record."""
    
    def __init__(self, record_id: int, user_id: int, book_id: int):
        """Initialize a BorrowRecord.
        
        Args:
            record_id: The record's ID
            user_id: The ID of the user who borrowed
            book_id: The ID of the borrowed book
        """
        self.id = record_id
        self.user_id = user_id
        self.book_id = book_id
        self.borrowed_at = datetime.now().isoformat()
        self.returned_at = None
        self._status = "borrowed"

    @property
    def status(self) -> str:
        """Get the borrow status."""
        return self._status

    @status.setter
    def status(self, value: str) -> None:
        """Set the borrow status."""
        if value not in ["borrowed", "returned"]:
            raise ValueError("Status must be 'borrowed' or 'returned'.")
        self._status = value

    def mark_returned(self) -> None:
        """Mark the book as returned."""
        self._status = "returned"
        self.returned_at = datetime.now().isoformat()