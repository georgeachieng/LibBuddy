from datetime import datetime


# This model is the paper trail for borrows and returns.
# Delete it and the app has inventory changes with no history behind them.
class BorrowRecord:
    def __init__(self, record_id: int, user_id: int, book_id: int):
        # These ids tie one borrow event to one user and one book.
        # Delete them and the record stops being useful.
        self.id = record_id
        self.user_id = user_id
        self.book_id = book_id

        # Timestamp on creation proves when the borrow actually started.
        # Delete it and history becomes way less meaningful.
        self.borrowed_at = datetime.now().isoformat()

        # Starts empty because the book is still out.
        # Delete this and every new record looks already returned.
        self.returned_at = None

        # Default state matters because return logic filters on it.
        # Delete this and active-borrow detection breaks.
        self._status = "borrowed"

    @property
    def status(self) -> str:
        return self._status

    @status.setter
    def status(self, value: str) -> None:
        # Restricting states keeps borrow history predictable.
        # Delete this and typos can become official statuses.
        if value not in ["borrowed", "returned"]:
            raise ValueError("Status must be 'borrowed' or 'returned'.")
        self._status = value

    # This is the state flip that closes out a borrow.
    # Delete it and records stay permanently active.
    def mark_returned(self) -> None:
        self._status = "returned"
        self.returned_at = datetime.now().isoformat()
