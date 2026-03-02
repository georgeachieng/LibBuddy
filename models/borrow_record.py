<<<<<<< HEAD
#write code here
=======
# models/borrow_record.py

from datetime import datetime

class BorrowRecord:
    def __init__(self, record_id: int, user_id: int, book_id: int):
        self.id = record_id
        self.user_id = user_id
        self.book_id = book_id
        self.borrowed_at = datetime.now().isoformat()
        self.returned_at = None
        self._status = "borrowed"

    @property
    def status(self) -> str:
        return self._status

    @status.setter
    def status(self, value: str):
        if value not in ["borrowed", "returned"]:
            raise ValueError("Status must be 'borrowed' or 'returned'.")
        self._status = value

    def mark_returned(self):
        self._status = "returned"
        self.returned_at = datetime.now().isoformat()
>>>>>>> 7d9e6de (Person/User inheritance,Book + BorrowRecord,properties/setters validation)
