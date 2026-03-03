from datetime import datetime
import json
from typing import Optional, Dict, Any, List
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from storage.json_store import JSONStore


# This service owns catalog state plus borrow/return side effects.
# Delete it and LibBuddy becomes a list of books with zero actual library behavior.
class LibraryService:
    # Borrow limit mirrors the project proposal and the CLI copy.
    # Delete it and users can hoard books forever, which is not the policy we said we built.
    BORROW_LIMIT = 3

    def __init__(self):
        # Separate stores keep book data and borrow data from stepping on each other.
        # Delete either one and you lose either catalog state or borrowing history.
        self.books_store = JSONStore("books.json")
        self.records_store = JSONStore("borrow_records.json")

    # Active borrows are the real source of truth for limits and "currently borrowed" views.
    # Delete it and those checks go back to copy-paste loops.
    def get_user_active_borrows(self, user_id: int = None, **kwargs) -> List[Dict[str, Any]]:
        if user_id is None:
            user_id = kwargs.get("user_id")

        records = self.records_store.all()
        return [
            r for r in records
            if r.get("user_id") == user_id and r.get("status") == "borrowed"
        ]

    # These aliases keep the CLI compatibility layer from pretending this feature does not exist.
    # Delete them and "current borrows" breaks again over naming nonsense.
    def active_borrows(self, user_id: int = None, **kwargs) -> List[Dict[str, Any]]:
        return self.get_user_active_borrows(user_id, **kwargs)

    def current_borrows(self, user_id: int = None, **kwargs) -> List[Dict[str, Any]]:
        return self.get_user_active_borrows(user_id, **kwargs)

    # Book creation validates catalog input before writing to storage.
    # Delete it and admins cannot grow the library.
    def add_book(self, title: str, author: str, isbn: str, total_copies: int, **kwargs) -> Dict[str, Any]:
        # These checks stop empty catalog records from landing in the JSON file.
        # Remove them and the app starts storing garbage books.
        if not title or not title.strip():
            raise ValueError("Title cannot be empty.")
        if not author or not author.strip():
            raise ValueError("Author cannot be empty.")
        if not isbn or not isbn.strip():
            raise ValueError("ISBN cannot be empty.")
        if total_copies < 1:
            raise ValueError("Total copies must be at least 1.")

        # ISBN uniqueness is the only thing stopping duplicate book entries here.
        # Delete it and admins can clone the same book accidentally all day.
        existing = self.books_store.find_by_field("isbn", isbn)
        if existing:
            raise ValueError(f"Book with ISBN {isbn} already exists.")

        # Stored shape stays explicit so the CLI and tests can trust the fields.
        # Delete any field and downstream display/borrow logic gets weird.
        book = {
            "title": title.strip(),
            "author": author.strip(),
            "isbn": isbn.strip(),
            "total_copies": total_copies,
            "available_copies": total_copies,
        }

        return self.books_store.save(book)

    # This is the raw catalog read path.
    # Delete it and list views have nothing to show.
    def list_books(self) -> List[Dict[str, Any]]:
        return self.books_store.all()

    # Single-book lookup keeps other methods from hand-rolling scans.
    # Delete it and callers start duplicating lookup logic.
    def get_book(self, book_id: int) -> Optional[Dict[str, Any]]:
        return self.books_store.find_by_id(book_id)

    # Search is intentionally loose so title/author lookups feel usable in a CLI.
    # Delete it and "search" becomes "scroll and pray."
    def search_books(self, query: str, title_or_author: str = None) -> List[Dict[str, Any]]:
        # This compatibility fallback keeps older call styles alive.
        # Remove it and some CLI code paths break for no good reason.
        search_term = (title_or_author or query or "").lower().strip()
        if not search_term:
            return []

        # Read once, filter in memory, keep it simple.
        # Delete this and there is nothing to search through.
        books = self.books_store.all()
        results = []
        for book in books:
            title = (book.get("title", "") or "").lower()
            author = (book.get("author", "") or "").lower()

            # Matching both fields keeps search practical instead of annoyingly literal.
            # Delete one side and users miss obvious results.
            if search_term in title or search_term in author:
                results.append(book)

        return results

    # Inventory updates keep total and available counts from drifting too far apart.
    # Delete it and admins have to edit JSON files by hand. Gross.
    def update_book_copies(self, book_id: int, total_copies: int = None, **kwargs) -> bool:
        # Some callers pass a differently named kwarg, so normalize it here.
        # Delete this and those callers silently stop working.
        if total_copies is None:
            total_copies = kwargs.get("new_total_copies", kwargs.get("total_copies"))

        if total_copies is None or total_copies < 0:
            raise ValueError("Total copies must be a non-negative number.")

        # If the book is missing, fail cleanly instead of exploding.
        # Delete this and missing ids cause nonsense later in the method.
        book = self.books_store.find_by_id(book_id)
        if not book:
            return False

        # Available copies should never exceed the new total.
        # Remove this cap and you can end up with impossible stock counts.
        available = book.get("available_copies", 0)
        new_available = min(available, total_copies)

        updates = {
            "total_copies": total_copies,
            "available_copies": new_available,
        }

        return self.books_store.update(book_id, updates)

    # Delete path for bad or retired books.
    # Remove it and catalog cleanup becomes impossible from the service layer.
    def delete_book(self, book_id: int, **kwargs) -> bool:
        return self.books_store.delete(book_id)

    # Borrowing updates inventory and writes a record. Two side effects, one action.
    # Delete it and the app stops being a library.
    def borrow_book(self, user_id: int = None, book_id: int = None, **kwargs) -> bool:
        # These fallbacks keep older calling styles from breaking.
        # Remove them and compatibility drops for zero benefit.
        if user_id is None:
            user_id = kwargs.get("user_id")
        if book_id is None:
            book_id = kwargs.get("book_id")

        # Missing ids mean the service cannot safely tie the action to a user or book.
        # Delete this and you can write half-broken borrow records.
        if user_id is None or book_id is None:
            raise ValueError("Both user_id and book_id are required.")

        # Missing book should fail loudly and early.
        # Delete this and later logic crashes or writes bad records.
        book = self.books_store.find_by_id(book_id)
        if not book:
            raise ValueError(f"Book ID {book_id} not found.")

        # Borrow limits are part of the project rules, not a nice-to-have.
        # Delete this and the app stops matching the actual library policy we documented.
        active_borrows = self.get_user_active_borrows(user_id=user_id)
        if len(active_borrows) >= self.BORROW_LIMIT:
            raise ValueError(f"Borrow limit reached. You can only borrow {self.BORROW_LIMIT} books at a time.")

        # Duplicate active borrows for the same book make the history weird and the inventory fake.
        # Delete this and one user can stack the same checkout record over and over.
        if any(record.get("book_id") == book_id for record in active_borrows):
            raise ValueError("You already have this book borrowed.")

        # This blocks borrowing ghost copies that do not exist.
        # Remove it and inventory can go negative.
        if book.get("available_copies", 0) <= 0:
            raise ValueError("No copies available for this book.")

        # Inventory update happens before the record write so availability stays honest.
        # Delete this and a successful borrow never changes stock.
        new_available = book.get("available_copies", 1) - 1
        if not self.books_store.update(book_id, {"available_copies": new_available}):
            return False

        # Borrow record is the audit trail. No record means no history.
        # Delete this block and returns/history have nothing real to work with.
        record = {
            "user_id": user_id,
            "book_id": book_id,
            "borrowed_at": datetime.now().isoformat(),
            "returned_at": None,
            "status": "borrowed",
        }

        self.records_store.save(record)
        return True

    # Return flow flips the borrow record and puts inventory back.
    # Delete it and books leave the system forever.
    def return_book(self, user_id: int = None, book_id: int = None, **kwargs) -> bool:
        if user_id is None:
            user_id = kwargs.get("user_id")
        if book_id is None:
            book_id = kwargs.get("book_id")

        # Find the active borrow record, not just any old record.
        # Delete the status filter and users can "return" already-returned books again.
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

        # Returning means both timestamp and status need to change together.
        # Delete one and your history becomes half-true.
        updates = {
            "returned_at": datetime.now().isoformat(),
            "status": "returned",
        }

        if not self.records_store.update(record["id"], updates):
            return False

        # Inventory goes back up, but never past the configured total.
        # Remove the cap and repeated returns can inflate stock counts.
        book = self.books_store.find_by_id(book_id)
        if book:
            new_available = min(book.get("available_copies", 0) + 1, book.get("total_copies", 1))
            self.books_store.update(book_id, {"available_copies": new_available})

        return True

    # These aliases exist because the CLI and older branches used different names.
    # Delete them and compatibility gets needlessly brittle again.
    def return_borrowed_book(self, book_id: int = None, user_id: int = None, **kwargs) -> bool:
        return self.return_book(book_id, user_id, **kwargs)

    def mark_returned(self, book_id: int = None, user_id: int = None, **kwargs) -> bool:
        return self.return_book(book_id, user_id, **kwargs)

    # User history is just a filtered view over all records.
    # Delete it and user-facing borrow history disappears.
    def my_borrow_history(self, user_id: int = None, **kwargs) -> List[Dict[str, Any]]:
        if user_id is None:
            user_id = kwargs.get("user_id")

        records = self.records_store.all()
        return [r for r in records if r.get("user_id") == user_id]

    # More compatibility aliases. Not glamorous, still useful.
    # Delete them and callers from other branches start failing on name mismatches.
    def get_user_history(self, user_id: int = None, **kwargs) -> List[Dict[str, Any]]:
        return self.my_borrow_history(user_id, **kwargs)

    def user_borrow_records(self, user_id: int = None, **kwargs) -> List[Dict[str, Any]]:
        return self.my_borrow_history(user_id, **kwargs)

    # Admin view for every borrow record in the system.
    # Delete it and there is no service-layer path for global record inspection.
    def view_all_borrow_records(self, **kwargs) -> List[Dict[str, Any]]:
        return self.records_store.all()

    def all_borrow_records(self, **kwargs) -> List[Dict[str, Any]]:
        return self.view_all_borrow_records(**kwargs)

    def list_borrow_records(self, **kwargs) -> List[Dict[str, Any]]:
        return self.view_all_borrow_records(**kwargs)

    # Status lookup is just a semantic wrapper around get_book.
    # Delete it and callers lose a clearer API name.
    def get_book_status(self, book_id: int) -> Optional[Dict[str, Any]]:
        return self.get_book(book_id)

    # This quick boolean check keeps callers from hand-parsing inventory every time.
    # Delete it and availability logic gets duplicated around the app.
    def is_book_available(self, book_id: int) -> bool:
        book = self.get_book(book_id)
        return book is not None and book.get("available_copies", 0) > 0

    # This lets admins pull real book candidates instead of typing every title by hand.
    # Delete it and the "import books" flow becomes fake UI with no outside data.
    def fetch_books_from_open_library(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        query = (query or "").strip()
        if not query:
            raise ValueError("Search query cannot be empty.")

        if limit < 1:
            raise ValueError("Limit must be at least 1.")

        # Query params keep the payload small and focused on fields the CLI actually prints.
        # Delete that filter and you pull extra junk for no benefit.
        params = urlencode(
            {
                "q": query,
                "limit": min(limit, 20),
                "fields": "title,author_name,isbn,first_publish_year",
            }
        )
        request = Request(
            f"https://openlibrary.org/search.json?{params}",
            headers={"User-Agent": "LibBuddy (george.achieng@student.moringaschool.com)"},
        )

        try:
            # The context manager closes the response cleanly after parsing.
            # Delete it and network handles can leak while the CLI keeps running.
            with urlopen(request, timeout=10) as response:
                payload = json.load(response)
        except HTTPError as exc:
            raise ValueError(f"Book search failed: Open Library returned {exc.code}.") from exc
        except URLError as exc:
            raise ValueError("Book search failed: could not reach Open Library.") from exc

        books = []
        for index, doc in enumerate(payload.get("docs", []), start=1):
            isbn_candidates = [isbn for isbn in doc.get("isbn", []) if isbn]
            author_candidates = [author for author in doc.get("author_name", []) if author]

            # This shape is the contract the CLI table expects.
            # Delete a field and the import screen starts printing gaps or crashes.
            books.append(
                {
                    "result_id": index,
                    "title": (doc.get("title") or "").strip() or "Untitled",
                    "author": author_candidates[0].strip() if author_candidates else "Unknown",
                    "isbn": str(isbn_candidates[0]).strip() if isbn_candidates else "",
                    "first_publish_year": doc.get("first_publish_year"),
                }
            )

        return books

    # Importing in bulk turns API results into actual catalog rows.
    # Delete it and search results stay pretty but useless.
    def import_books(self, books: List[Dict[str, Any]], total_copies: int = 2) -> Dict[str, Any]:
        if total_copies < 1:
            raise ValueError("Total copies must be at least 1.")

        imported = []
        skipped = []
        existing_books = self.books_store.all()
        seen_isbns = {
            (book.get("isbn") or "").strip()
            for book in existing_books
            if (book.get("isbn") or "").strip()
        }
        seen_titles = {
            ((book.get("title") or "").strip().lower(), (book.get("author") or "").strip().lower())
            for book in existing_books
        }

        for book in books:
            title = (book.get("title") or "").strip()
            author = (book.get("author") or "").strip() or "Unknown"
            isbn = (book.get("isbn") or "").strip()
            key = (title.lower(), author.lower())

            if not title:
                skipped.append({"book": book, "reason": "missing title"})
                continue

            # Duplicate guards stop the API import from spamming the same catalog rows.
            # Delete them and one search can bloat the JSON file fast.
            if isbn and isbn in seen_isbns:
                skipped.append({"book": book, "reason": "duplicate isbn"})
                continue

            if key in seen_titles:
                skipped.append({"book": book, "reason": "duplicate title"})
                continue

            saved = self.add_book(
                title=title,
                author=author,
                isbn=isbn or f"OPENLIB-{title[:12].upper().replace(' ', '-')}-{len(imported) + len(skipped) + 1}",
                total_copies=total_copies,
            )
            imported.append(saved)
            seen_titles.add(key)
            if isbn:
                seen_isbns.add(isbn)

        return {
            "imported": imported,
            "skipped": skipped,
        }
