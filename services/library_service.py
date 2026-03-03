from datetime import datetime
from typing import Optional, Dict, Any, List

from storage.json_store import JSONStore


class LibraryService:
    BORROW_LIMIT = 3

    def __init__(self):
        self.books_store = JSONStore("books.json")
        self.records_store = JSONStore("borrow_records.json")

    def get_user_active_borrows(self, user_id: int = None, **kwargs) -> List[Dict[str, Any]]:
        if user_id is None:
            user_id = kwargs.get("user_id")

        records = self.records_store.all()
        return [
            r for r in records
            if r.get("user_id") == user_id and r.get("status") == "borrowed"
        ]

    def active_borrows(self, user_id: int = None, **kwargs) -> List[Dict[str, Any]]:
        return self.get_user_active_borrows(user_id, **kwargs)

    def current_borrows(self, user_id: int = None, **kwargs) -> List[Dict[str, Any]]:
        return self.get_user_active_borrows(user_id, **kwargs)

    def add_book(self, title: str, author: str, isbn: str, total_copies: int, **kwargs) -> Dict[str, Any]:
        if not title or not title.strip():
            raise ValueError("Title cannot be empty.")
        if not author or not author.strip():
            raise ValueError("Author cannot be empty.")
        if not isbn or not isbn.strip():
            raise ValueError("ISBN cannot be empty.")
        if total_copies < 1:
            raise ValueError("Total copies must be at least 1.")

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
        return self.books_store.all()

    def get_book(self, book_id: int) -> Optional[Dict[str, Any]]:
        return self.books_store.find_by_id(book_id)

    def search_books(self, query: str, title_or_author: str = None) -> List[Dict[str, Any]]:
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
        if total_copies is None:
            total_copies = kwargs.get("new_total_copies", kwargs.get("total_copies"))

        if total_copies is None or total_copies < 0:
            raise ValueError("Total copies must be a non-negative number.")

        book = self.books_store.find_by_id(book_id)
        if not book:
            return False

        available = book.get("available_copies", 0)
        new_available = min(available, total_copies)

        updates = {
            "total_copies": total_copies,
            "available_copies": new_available,
        }

        return self.books_store.update(book_id, updates)

    def delete_book(self, book_id: int, **kwargs) -> bool:
        return self.books_store.delete(book_id)

    def borrow_book(self, user_id: int = None, book_id: int = None, **kwargs) -> bool:
        if user_id is None:
            user_id = kwargs.get("user_id")
        if book_id is None:
            book_id = kwargs.get("book_id")

        if user_id is None or book_id is None:
            raise ValueError("Both user_id and book_id are required.")

        book = self.books_store.find_by_id(book_id)
        if not book:
            raise ValueError(f"Book ID {book_id} not found.")

        active_borrows = self.get_user_active_borrows(user_id=user_id)
        if len(active_borrows) >= self.BORROW_LIMIT:
            raise ValueError(f"Borrow limit reached. You can only borrow {self.BORROW_LIMIT} books at a time.")

        if any(record.get("book_id") == book_id for record in active_borrows):
            raise ValueError("You already have this book borrowed.")

        if book.get("available_copies", 0) <= 0:
            raise ValueError("No copies available for this book.")

        new_available = book.get("available_copies", 1) - 1
        if not self.books_store.update(book_id, {"available_copies": new_available}):
            return False

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
        if user_id is None:
            user_id = kwargs.get("user_id")
        if book_id is None:
            book_id = kwargs.get("book_id")

        records = self.records_store.all()
        record = next(
            (
                r for r in records
                if r.get("user_id") == user_id
                and r.get("book_id") == book_id
                and r.get("status") == "borrowed"
            ),
            None
        )

        if not record:
            raise ValueError("No active borrow record found for this book and user.")

        updates = {
            "returned_at": datetime.now().isoformat(),
            "status": "returned",
        }

        if not self.records_store.update(record["id"], updates):
            return False

        book = self.books_store.find_by_id(book_id)
        if book:
            new_available = min(book.get("available_copies", 0) + 1, book.get("total_copies", 1))
            self.books_store.update(book_id, {"available_copies": new_available})

        return True

    def return_borrowed_book(self, book_id: int = None, user_id: int = None, **kwargs) -> bool:
        return self.return_book(book_id, user_id, **kwargs)

    def mark_returned(self, book_id: int = None, user_id: int = None, **kwargs) -> bool:
        return self.return_book(book_id, user_id, **kwargs)

    def my_borrow_history(self, user_id: int = None, **kwargs) -> List[Dict[str, Any]]:
        if user_id is None:
            user_id = kwargs.get("user_id")

        records = self.records_store.all()
        return [r for r in records if r.get("user_id") == user_id]

    def get_user_history(self, user_id: int = None, **kwargs) -> List[Dict[str, Any]]:
        return self.my_borrow_history(user_id, **kwargs)

    def user_borrow_records(self, user_id: int = None, **kwargs) -> List[Dict[str, Any]]:
        return self.my_borrow_history(user_id, **kwargs)

    def view_all_borrow_records(self, **kwargs) -> List[Dict[str, Any]]:
        return self.records_store.all()

    def all_borrow_records(self, **kwargs) -> List[Dict[str, Any]]:
        return self.view_all_borrow_records(**kwargs)

    def list_borrow_records(self, **kwargs) -> List[Dict[str, Any]]:
        return self.view_all_borrow_records(**kwargs)

    def get_book_status(self, book_id: int) -> Optional[Dict[str, Any]]:
        return self.get_book(book_id)

    def is_book_available(self, book_id: int) -> bool:
        book = self.get_book(book_id)
        return book is not None and book.get("available_copies", 0) > 0
