"""Library service for LibBuddy.

Person 2 scope - Stub implementation for CLI testing.
"""

import os
from datetime import datetime
from typing import Any

# Ensure we can import from sibling packages
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from storage.json_store import JsonStore


class LibraryService:
    """Handles book management, borrowing, and returns."""

    BORROW_LIMIT = 3  # Maximum books a user can borrow at once

    def __init__(self) -> None:
        data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
        self.book_store = JsonStore(os.path.join(data_dir, "books.json"))
        self.borrow_store = JsonStore(os.path.join(data_dir, "borrow_records.json"))

    def list_books(self) -> list[dict[str, Any]]:
        """List all books."""
        return self.book_store.load()

    def search_books(self, query: str) -> list[dict[str, Any]]:
        """Search books by title or author."""
        books = self.book_store.load()
        query_lower = query.lower()
        return [
            b for b in books
            if query_lower in b.get("title", "").lower()
            or query_lower in b.get("author", "").lower()
        ]

    def get_book_by_id(self, book_id: int) -> dict[str, Any] | None:
        """Get a book by ID."""
        return self.book_store.find_by_id(book_id)

    def add_book(self, title: str, author: str, isbn: str, total_copies: int, available_copies: int | None = None) -> dict[str, Any] | None:
        """Add a new book to the library."""
        book = {
            "title": title,
            "author": author,
            "isbn": isbn,
            "total_copies": total_copies,
            "available_copies": available_copies if available_copies is not None else total_copies,
        }
        return self.book_store.add(book)

    def update_book_copies(self, book_id: int, total_copies: int) -> bool:
        """Update the total copies of a book."""
        book = self.book_store.find_by_id(book_id)
        if not book:
            return False

        # Adjust available copies proportionally
        borrowed = book.get("total_copies", 0) - book.get("available_copies", 0)
        new_available = max(0, total_copies - borrowed)

        return self.book_store.update(book_id, {
            "total_copies": total_copies,
            "available_copies": new_available,
        })

    def delete_book(self, book_id: int) -> bool:
        """Delete a book from the library."""
        return self.book_store.delete(book_id)

    def _get_active_borrows(self, user_id: int) -> list[dict[str, Any]]:
        """Get active (not returned) borrow records for a user."""
        records = self.borrow_store.load()
        return [r for r in records if r.get("user_id") == user_id and r.get("status") == "borrowed"]

    def borrow_book(self, user_id: int, book_id: int) -> bool:
        """Borrow a book."""
        # Check borrow limit
        active_borrows = self._get_active_borrows(user_id)
        if len(active_borrows) >= self.BORROW_LIMIT:
            return False

        # Check if already borrowing this book
        if any(r.get("book_id") == book_id for r in active_borrows):
            return False

        # Check book availability
        book = self.book_store.find_by_id(book_id)
        if not book or book.get("available_copies", 0) <= 0:
            return False

        # Create borrow record
        record = {
            "user_id": user_id,
            "book_id": book_id,
            "status": "borrowed",
            "borrowed_at": datetime.now().isoformat(),
            "returned_at": None,
        }
        self.borrow_store.add(record)

        # Decrement available copies
        self.book_store.update(book_id, {
            "available_copies": book["available_copies"] - 1,
        })

        return True

    def return_book(self, user_id: int, book_id: int) -> bool:
        """Return a borrowed book."""
        records = self.borrow_store.load()

        for record in records:
            if (record.get("user_id") == user_id
                    and record.get("book_id") == book_id
                    and record.get("status") == "borrowed"):
                # Update record
                self.borrow_store.update(record["id"], {
                    "status": "returned",
                    "returned_at": datetime.now().isoformat(),
                })

                # Increment available copies
                book = self.book_store.find_by_id(book_id)
                if book:
                    self.book_store.update(book_id, {
                        "available_copies": book["available_copies"] + 1,
                    })

                return True

        return False

    def my_borrow_history(self, user_id: int) -> list[dict[str, Any]]:
        """Get borrow history for a user."""
        return self.borrow_store.find_by(user_id=user_id)

    def view_all_borrow_records(self) -> list[dict[str, Any]]:
        """Get all borrow records (admin only)."""
        return self.borrow_store.load()

    def get_user_active_borrows(self, user_id: int) -> list[dict[str, Any]]:
        """Get currently borrowed books for a user."""
        return self._get_active_borrows(user_id)
