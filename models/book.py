# This model keeps inventory math close to the book data itself.
# Delete it and borrow/return logic has to manage stock manually everywhere.
class Book:
    def __init__(self, book_id: int, title: str, author: str, isbn: str, total_copies: int):
        # These fields are the minimum shape the rest of the app expects.
        # Delete any one and printing, searching, or inventory logic gets weird fast.
        self.id = book_id
        self.title = title
        self.author = author
        self.isbn = isbn
        self.total_copies = total_copies

        # Available starts at total so new books begin fully in stock.
        # Delete this and fresh books may appear unavailable immediately.
        self._available_copies = total_copies

    @property
    def available_copies(self) -> int:
        return self._available_copies

    @available_copies.setter
    def available_copies(self, value: int) -> None:
        # This guard blocks impossible inventory states.
        # Delete it and stock can go negative or exceed the total.
        if value < 0 or value > self.total_copies:
            raise ValueError("Available copies must be between 0 and total copies.")
        self._available_copies = value

    # Borrowing should reduce stock by exactly one.
    # Delete this and the model cannot enforce its own inventory rules.
    def borrow_copy(self) -> None:
        if self._available_copies <= 0:
            raise ValueError("No copies available to borrow.")
        self._available_copies -= 1

    # Returning should restore stock, but never beyond total.
    # Delete it and returned books never come back into circulation.
    def return_copy(self) -> None:
        if self._available_copies >= self.total_copies:
            raise ValueError("All copies are already returned.")
        self._available_copies += 1
