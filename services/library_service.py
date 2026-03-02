"""Library service for LibBuddy - manages books and borrowing."""

from datetime import datetime
from typing import Optional, Dict, Any, List

from storage.json_store import JSONStore


class LibraryService:
    """Handles all library operations: books, borrowing, and returns."""
    
    def __init__(self):
        """Initialize LibraryService with JSON stores."""
        self.books_store = JSONStore("books.json")
        self.records_store = JSONStore("borrow_records.json")

    # ==================== Book Operations ====================
    
    def add_book(self, title: str, author: str, isbn: str, total_copies: int, **kwargs) -> Dict[str, Any]:
        """Add a new book to the library.
        
        Args:
            title: Book title
            author: Book author
            isbn: ISBN number
            total_copies: Number of copies available
            
        Returns:
            Dictionary with the new book's data
            
        Raises:
            ValueError: If validation fails
        """
        if not title or not title.strip():
            raise ValueError("Title cannot be empty.")
        if not author or not author.strip():
            raise ValueError("Author cannot be empty.")
        if not isbn or not isbn.strip():
            raise ValueError("ISBN cannot be empty.")
        if total_copies < 1:
            raise ValueError("Total copies must be at least 1.")

        # Check if ISBN already exists
        existing = self.books_store.find_by_field("isbn", isbn)
        if existing:
            raise ValueError(f"Book with ISBN {isbn} already exists.")

        book = {
            "title": title.strip(),
            "author": author.strip(),
            "isbn": isbn.strip(),
            "total_copies": total_copies,
            "available_copies": total_copies,
        }
        
        return self.books_store.save(book)

    def list_books(self) -> List[Dict[str, Any]]:
        """Get all books in the library.
        
        Returns:
            List of all book dictionaries
        """
        return self.books_store.all()

    def get_book(self, book_id: int) -> Optional[Dict[str, Any]]:
        """Get a book by ID.
        
        Args:
            book_id: The book's ID
            
        Returns:
            Book dictionary or None if not found
        """
        return self.books_store.find_by_id(book_id)

    def search_books(self, query: str, title_or_author: str = None) -> List[Dict[str, Any]]:
        """Search books by title or author.
        
        Args:
            query: Search query (optional, for compatibility)
            title_or_author: Alternative parameter for search query
            
        Returns:
            List of matching books
        """
        search_term = (title_or_author or query or "").lower().strip()
        if not search_term:
            return []
        
        books = self.books_store.all()
        results = []
        for book in books:
            title = (book.get("title", "") or "").lower()
            author = (book.get("author", "") or "").lower()
            if search_term in title or search_term in author:
                results.append(book)
        
        return results

    def update_book_copies(self, book_id: int, total_copies: int = None, **kwargs) -> bool:
        """Update the number of copies for a book.
        
        Args:
            book_id: The book's ID
            total_copies: New total number of copies
            
        Returns:
            True if successful, False otherwise
            
        Raises:
            ValueError: If new total is invalid
        """
        if total_copies is None:
            total_copies = kwargs.get("new_total_copies", kwargs.get("total_copies"))
        
        if total_copies is None or total_copies < 0:
            raise ValueError("Total copies must be a non-negative number.")
        
        book = self.books_store.find_by_id(book_id)
        if not book:
            return False
        
        # Adjust available copies proportionally if needed
        old_total = book.get("total_copies", 1)
        available = book.get("available_copies", 0)
        
        # Cap available at new total
        new_available = min(available, total_copies)
        
        updates = {
            "total_copies": total_copies,
            "available_copies": new_available,
        }
        
        return self.books_store.update(book_id, updates)

    def delete_book(self, book_id: int, **kwargs) -> bool:
        """Delete a book from the library.
        
        Args:
            book_id: The book's ID
            
        Returns:
            True if successful, False otherwise
        """
        return self.books_store.delete(book_id)

    # ==================== Borrowing Operations ====================
    
    def borrow_book(self, user_id: int = None, book_id: int = None, **kwargs) -> bool:
        """Borrow a book from the library.
        
        Args:
            user_id: The user's ID
            book_id: The book's ID
            
        Returns:
            True if successful, False otherwise
            
        Raises:
            ValueError: If book not found or no copies available
        """
        # Handle parameter flexibility
        if user_id is None:
            user_id = kwargs.get("user_id")
        if book_id is None:
            book_id = kwargs.get("book_id")
        
        book = self.books_store.find_by_id(book_id)
        if not book:
            raise ValueError(f"Book ID {book_id} not found.")
        
        if book.get("available_copies", 0) <= 0:
            raise ValueError("No copies available for this book.")
        
        # Decrease available copies
        new_available = book.get("available_copies", 1) - 1
        if not self.books_store.update(book_id, {"available_copies": new_available}):
            return False
        
        # Create borrow record
        record = {
            "user_id": user_id,
            "book_id": book_id,
            "borrowed_at": datetime.now().isoformat(),
            "returned_at": None,
            "status": "borrowed",
        }
        
        self.records_store.save(record)
        return True

    def return_book(self, user_id: int = None, book_id: int = None, **kwargs) -> bool:
        """Return a borrowed book.
        
        Args:
            user_id: The user's ID
            book_id: The book's ID
            
        Returns:
            True if successful, False otherwise
            
        Raises:
            ValueError: If book or active borrow record not found
        """
        # Handle parameter flexibility
        if user_id is None:
            user_id = kwargs.get("user_id")
        if book_id is None:
            book_id = kwargs.get("book_id")
        
        # Find active borrow record
        records = self.records_store.all()
        record = next(
            (r for r in records
             if r.get("user_id") == user_id
             and r.get("book_id") == book_id
             and r.get("status") == "borrowed"),
            None
        )
        
        if not record:
            raise ValueError("No active borrow record found for this book and user.")
        
        # Update borrow record
        updates = {
            "returned_at": datetime.now().isoformat(),
            "status": "returned",
        }
        
        if not self.records_store.update(record["id"], updates):
            return False
        
        # Increase available copies
        book = self.books_store.find_by_id(book_id)
        if book:
            new_available = min(book.get("available_copies", 0) + 1, book.get("total_copies", 1))
            self.books_store.update(book_id, {"available_copies": new_available})
        
        return True

    def return_borrowed_book(self, book_id: int = None, user_id: int = None, **kwargs) -> bool:
        """Alias for return_book for compatibility."""
        return self.return_book(book_id, user_id, **kwargs)

    def mark_returned(self, book_id: int = None, user_id: int = None, **kwargs) -> bool:
        """Alias for return_book for compatibility."""
        return self.return_book(book_id, user_id, **kwargs)

    # ==================== Borrow Record Operations ====================
    
    def my_borrow_history(self, user_id: int = None, **kwargs) -> List[Dict[str, Any]]:
        """Get borrow history for a user.
        
        Args:
            user_id: The user's ID
            
        Returns:
            List of this user's borrow records
        """
        if user_id is None:
            user_id = kwargs.get("user_id")
        
        records = self.records_store.all()
        return [r for r in records if r.get("user_id") == user_id]

    def get_user_history(self, user_id: int = None, **kwargs) -> List[Dict[str, Any]]:
        """Alias for my_borrow_history for compatibility."""
        return self.my_borrow_history(user_id, **kwargs)

    def user_borrow_records(self, user_id: int = None, **kwargs) -> List[Dict[str, Any]]:
        """Alias for my_borrow_history for compatibility."""
        return self.my_borrow_history(user_id, **kwargs)

    def view_all_borrow_records(self, **kwargs) -> List[Dict[str, Any]]:
        """Get all borrow records.
        
        Returns:
            List of all borrow records
        """
        return self.records_store.all()

    def all_borrow_records(self, **kwargs) -> List[Dict[str, Any]]:
        """Alias for view_all_borrow_records for compatibility."""
        return self.view_all_borrow_records(**kwargs)

    def list_borrow_records(self, **kwargs) -> List[Dict[str, Any]]:
        """Alias for view_all_borrow_records for compatibility."""
        return self.view_all_borrow_records(**kwargs)

    # ==================== Utility Methods ====================
    
    def get_book_status(self, book_id: int) -> Optional[Dict[str, Any]]:
        """Get detailed status of a book including available copies.
        
        Args:
            book_id: The book's ID
            
        Returns:
            Book status dictionary or None if not found
        """
        return self.get_book(book_id)

    def is_book_available(self, book_id: int) -> bool:
        """Check if a book has available copies.
        
        Args:
            book_id: The book's ID
            
        Returns:
            True if copies are available, False otherwise
        """
        book = self.get_book(book_id)
        return book is not None and book.get("available_copies", 0) > 0