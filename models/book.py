class Book: 
    def __init__(self, book_id: int, title: str, author: str, isbn: str, total_copies: int):
        self.id = book_id
        self.title = title
        self.author = author
        self.isbn = isbn
        self.total_copies = total_copies
        self._available_copies = total_copies

    @property
    def available_copies(self) -> int:
        return self._available_copies

    @available_copies.setter
    def available_copies(self, value: int) -> None:
        if value < 0 or value > self.total_copies:
            raise ValueError("Available copies must be between 0 and total copies.")
        self._available_copies = value

    def borrow_copy(self) -> None:
        if self._available_copies <= 0:
            raise ValueError("No copies available to borrow.")
        self._available_copies -= 1

    def return_copy(self) -> None:
        if self._available_copies >= self.total_copies:
            raise ValueError("All copies are already returned.")
        self._available_copies += 1