"""Book model for LibBuddy."""


class Book:
    """Represents a Book in the library system."""
    
    def __init__(self, book_id: int, title: str, author: str, isbn: str, total_copies: int):
        """Initialize a Book.
        
        Args:
            book_id: The book's ID
            title: The book's title
            author: The book's author
            isbn: The book's ISBN
            total_copies: Total copies available
        """
        self.id = book_id
        self.title = title
        self.author = author
        self.isbn = isbn
        self.total_copies = total_copies
        self._available_copies = total_copies

    @property
    def available_copies(self) -> int:
        """Get the number of available copies."""
        return self._available_copies

    @available_copies.setter
    def available_copies(self, value: int) -> None:
        """Set the number of available copies."""
        if value < 0 or value > self.total_copies:
            raise ValueError("Available copies must be between 0 and total copies.")
        self._available_copies = value

    def borrow_copy(self) -> None:
        """Borrow a copy of the book."""
        if self._available_copies <= 0:
            raise ValueError("No copies available to borrow.")
        self._available_copies -= 1

    def return_copy(self) -> None:
        """Return a copy of the book."""
        if self._available_copies >= self.total_copies:
            raise ValueError("All copies are already returned.")
        self._available_copies += 1