from __future__ import annotations

import builtins
import sys
from datetime import datetime
from dataclasses import asdict, is_dataclass
from importlib import import_module
from textwrap import shorten
from typing import Any

from utils.decorators import login_required, role_required

try:
    from tabulate import tabulate
except ImportError:  # pragma: no cover
    tabulate = None


PRINT_INDENT = "    "
_PRINT_AT_LINE_START = True


def print(*args: Any, sep: str = " ", end: str = "\n", file=None, flush: bool = False) -> None:
    global _PRINT_AT_LINE_START

    if file is not None:
        builtins.print(*args, sep=sep, end=end, file=file, flush=flush)
        return

    text = sep.join(str(arg) for arg in args)
    if text:
        if _PRINT_AT_LINE_START:
            text = f"{PRINT_INDENT}{text}"
        text = text.replace("\n", f"\n{PRINT_INDENT}")

    builtins.print(text, end=end, flush=flush)
    _PRINT_AT_LINE_START = end.endswith("\n")


class ServiceNotReadyError(RuntimeError):
    """Raised when expected teammate service methods are missing."""


class LibBuddyCLI:
    INDENT = "    "

    def __init__(self) -> None:
        self.auth_service = self._load_service("services.auth_service", "AuthService")
        self.library_service = self._load_service("services.library_service", "LibraryService")
        self.review_service = self._load_service("services.review_service", "ReviewService")

        self.current_user: Any = None

    def _load_service(self, module_path: str, class_name: str) -> Any:
        try:
            module = import_module(module_path)
        except ImportError as exc:
            raise ServiceNotReadyError(
                f"Missing module '{module_path}'. Pull teammate code before running CLI."
            ) from exc

        service_cls = getattr(module, class_name, None)
        if service_cls is not None:
            try:
                return service_cls()
            except TypeError:
                pass

        return module

    def _call(self, service: Any, names: list[str], *args: Any, **kwargs: Any) -> Any:
        for name in names:
            fn = getattr(service, name, None)
            if callable(fn):
                return fn(*args, **kwargs)

        joined = ", ".join(names)
        raise ServiceNotReadyError(f"Service method not found. Expected one of: {joined}")

    @staticmethod
    def _to_dict(item: Any) -> dict[str, Any]:
        if isinstance(item, dict):
            return item

        if is_dataclass(item):
            return asdict(item)

        if hasattr(item, "__dict__"):
            return dict(vars(item))

        return {"value": item}

    def _line(self, text: str = "") -> None:
        print(text)

    def _get_input(self, prompt: str) -> str:
        return input(prompt).strip()

    def _get_password_input(self, prompt: str) -> str:
        if not sys.stdin.isatty() or not sys.stdout.isatty():
            return self._get_input(prompt)

        if sys.platform == "win32":
            import msvcrt

            print(prompt, end="", flush=True)
            chars: list[str] = []
            while True:
                key = msvcrt.getwch()
                if key in ("\r", "\n"):
                    print()
                    return "".join(chars).strip()
                if key == "\003":
                    raise KeyboardInterrupt
                if key == "\b":
                    if chars:
                        chars.pop()
                        print("\b \b", end="", flush=True)
                    continue
                if key in ("\x00", "\xe0"):
                    msvcrt.getwch()
                    continue
                chars.append(key)
                print("*", end="", flush=True)

        import termios
        import tty

        print(prompt, end="", flush=True)
        chars: list[str] = []
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            while True:
                key = sys.stdin.read(1)
                if key in ("\r", "\n"):
                    print()
                    return "".join(chars).strip()
                if key == "\x03":
                    raise KeyboardInterrupt
                if key in ("\x7f", "\b"):
                    if chars:
                        chars.pop()
                        print("\b \b", end="", flush=True)
                    continue
                chars.append(key)
                print("*", end="", flush=True)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

    def _prompt_int(self, prompt: str, min_value: int | None = None, allow_cancel: bool = False) -> int | None:
        while True:
            raw = self._get_input(prompt)
            if allow_cancel and raw.lower() in {"b", "back", "cancel"}:
                return None
            try:
                value = int(raw)

                if min_value is not None and value < min_value:
                    print(f"Value must be >= {min_value}.")
                    continue

                return value
            except ValueError:
                print("Enter a valid number.")

    @staticmethod
    def _get_field(item: dict[str, Any], *keys: str, default: Any = "-") -> Any:
        for key in keys:
            if key in item and item[key] is not None:
                return item[key]

        return default

    def _get_current_user_id(self) -> Any:
        user_dict = self._to_dict(self.current_user)
        return self._get_field(user_dict, "id", "user_id")

    def _get_current_user_role(self) -> str:
        user_dict = self._to_dict(self.current_user)
        role = str(self._get_field(user_dict, "role", default="user")).lower()
        return role

    @staticmethod
    def _format_timestamp(value: Any) -> str:
        if not value or value == "-":
            return "-"
        try:
            return datetime.fromisoformat(str(value)).strftime("%Y-%m-%d %H:%M")
        except ValueError:
            return str(value)

    def _get_book_label(self, book_id: Any) -> str:
        try:
            book = self._call(self.library_service, ["get_book", "get_book_status"], int(book_id))
        except (ServiceNotReadyError, TypeError, ValueError):
            book = None

        if book:
            book_dict = self._to_dict(book)
            title = self._get_field(book_dict, "title")
            return shorten(str(title), width=32, placeholder="...")

        return f"Book {book_id}"

    def _get_user_label(self, user_id: Any, fallback_name: Any = None) -> str:
        if fallback_name not in (None, ""):
            return str(fallback_name)

        try:
            user = self._call(self.auth_service, ["get_user_by_id"], int(user_id))
        except (ServiceNotReadyError, TypeError, ValueError):
            user = None

        if user:
            user_dict = self._to_dict(user)
            username = self._get_field(user_dict, "username", default="")
            if username and username != "-":
                return str(username)
            return str(self._get_field(user_dict, "name"))

        return f"user-{user_id}"

    def _get_reviewable_book_ids(self, user_id: Any) -> list[int]:
        try:
            records = self._call(
                self.library_service,
                ["my_borrow_history", "get_user_history", "user_borrow_records"],
                user_id,
            )
        except TypeError:
            records = self._call(
                self.library_service,
                ["my_borrow_history", "get_user_history", "user_borrow_records"],
                user_id=user_id,
            )

        seen: set[int] = set()
        reviewable: list[int] = []
        for record in list(records):
            record_dict = self._to_dict(record)
            book_id = self._get_field(record_dict, "book_id", default=None)
            if isinstance(book_id, int) and book_id not in seen:
                seen.add(book_id)
                reviewable.append(book_id)

        return reviewable

    def _show_menu(self, title: str, options: list[str]) -> str:
        self._line()
        self._line("=" * 72)
        self._line(title.center(72))
        self._line("=" * 72)
        print()
        for index, option in enumerate(options, start=1):
            self._line(f"{index}. {option}")
        print()
        return self._get_input("Select an option: ")

    def _print_table(self, headers: list[str], rows: list[list[Any]]) -> None:
        if not rows:
            return

        if tabulate is not None:
            for line in tabulate(rows, headers=headers, tablefmt="fancy_grid").splitlines():
                self._line(line)
            return

        normalized = [[str(cell) for cell in row] for row in rows]
        widths = [
            max(len(str(header)), *(len(row[index]) for row in normalized))
            for index, header in enumerate(headers)
        ]

        def render(row: list[str]) -> str:
            return " | ".join(cell.ljust(widths[index]) for index, cell in enumerate(row))

        self._line(render(headers))
        self._line("-+-".join("-" * width for width in widths))
        for row in normalized:
            self._line(render(row))

    def _show_welcome_panel(self) -> None:
        try:
            book_count = len(self._call(self.library_service, ["list_books", "get_books", "all_books"]))
        except ServiceNotReadyError:
            book_count = 0

        try:
            user_count = len(self._call(self.auth_service, ["list_users", "all_users", "get_all_users"]))
        except ServiceNotReadyError:
            user_count = 0

        try:
            review_count = len(self._call(self.review_service, ["list_all_reviews", "all_reviews"]))
        except ServiceNotReadyError:
            review_count = 0

        self._line()
        self._line("=" * 72)
        self._line("LIBBUDDY 📚".center(72))
        self._line("CLI Library Desk".center(72))
        self._line("=" * 72)
        self._line(f"Catalog: {book_count} books | Members: {user_count} users | Reviews: {review_count} ⭐")
        self._line("-" * 72)

    def _print_books(self, books: list[Any]) -> None:
        if not books:
            print("No books found.")
            return

        print("\nBooks:")
        rows = []
        for book in books:
            b = self._to_dict(book)
            rows.append(
                [
                    self._get_field(b, "id", "book_id"),
                    shorten(str(self._get_field(b, "title")), width=30, placeholder="..."),
                    shorten(str(self._get_field(b, "author")), width=20, placeholder="..."),
                    self._get_field(b, "isbn"),
                    f"{self._get_field(b, 'available_copies')}/{self._get_field(b, 'total_copies', default=self._get_field(b, 'available_copies'))}",
                ]
            )
        self._print_table(["ID", "Title", "Author", "ISBN", "Stock"], rows)

    def _print_records(self, records: list[Any]) -> None:
        if not records:
            print("No borrow records found.")
            return

        print("\nBorrow Records:")
        rows = []
        for record in records:
            r = self._to_dict(record)
            rows.append(
                [
                    self._get_field(r, "id", "record_id"),
                    self._get_user_label(
                        self._get_field(r, "user_id"),
                        self._get_field(r, "borrower_name", default=None),
                    ),
                    self._get_book_label(self._get_field(r, "book_id")),
                    self._get_field(r, "status"),
                    self._format_timestamp(self._get_field(r, "borrowed_at")),
                    self._format_timestamp(self._get_field(r, "returned_at", default="-")),
                ]
            )
        self._print_table(["ID", "User", "Book", "Status", "Borrowed", "Returned"], rows)

    def register(self) -> None:
        print("\n=== Register ===")
        name = self._get_input("Name: ")
        username = self._get_input("Username: ")
        email = self._get_input("Email: ")
        password = self._get_password_input("Password: ")

        if not (name and username and email and password):
            print("Please fill in every field.")
            return

        try:
            created = self._call(
                self.auth_service,
                ["register", "create_user", "signup"],
                name=name,
                email=email,
                password=password,
                role="user",
                username=username,
            )
        except TypeError:
            created = self._call(
                self.auth_service,
                ["register", "create_user", "signup"],
                name,
                email,
                password,
            )
        except (PermissionError, ValueError) as exc:
            print(exc)
            return

        if created:
            print("Account created. You can log in now. ✅")
        else:
            print("Could not create the account.")

    def login(self) -> None:
        print("\n=== Login ===")
        email = self._get_input("Email or username: ")
        password = self._get_password_input("Password: ")

        if not (email and password):
            print("Enter both your email or username and your password.")
            return

        try:
            user = self._call(
                self.auth_service,
                ["login", "authenticate", "signin"],
                email=email,
                password=password,
            )
        except TypeError:
            user = self._call(
                self.auth_service,
                ["login", "authenticate", "signin"],
                email,
                password,
            )
        except ValueError as exc:
            print(exc)
            return

        if not user:
            print("Login failed. Check your details and try again.")
            return

        self.current_user = user
        print(f"Login successful. Welcome, {self._get_field(self._to_dict(user), 'username', 'name')}. 👋")

    def logout(self) -> None:
        try:
            self._call(self.auth_service, ["logout", "signout"])
        except ServiceNotReadyError:
            pass

        self.current_user = None
        print("You have been logged out.")

    def list_books(self) -> None:
        books = self._call(self.library_service, ["list_books", "get_books", "all_books"])
        self._print_books(list(books))

    def list_available_books(self) -> None:
        books = self._call(self.library_service, ["list_books", "get_books", "all_books"])
        available_books = [
            book for book in list(books)
            if self._get_field(self._to_dict(book), "available_copies", default=0) > 0
        ]

        if not available_books:
            print("No books are available right now.")
            return

        print("\nAvailable Books:")
        self._print_books(available_books)

    def view_book_details(self) -> None:
        book_id = self._prompt_int("Book ID to inspect: ", min_value=1)

        try:
            book = self._call(self.library_service, ["get_book", "get_book_status"], book_id)
        except TypeError:
            book = self._call(self.library_service, ["get_book", "get_book_status"], book_id=book_id)

        if not book:
            print("No book found with that ID.")
            return

        book_dict = self._to_dict(book)
        try:
            average = self._call(self.review_service, ["get_book_average_rating", "average_rating"], book_id)
        except (ServiceNotReadyError, TypeError):
            average = None

        try:
            reviews = self._call(self.review_service, ["get_book_reviews", "book_reviews"], book_id)
        except TypeError:
            reviews = self._call(self.review_service, ["get_book_reviews", "book_reviews"], book_id=book_id)

        reviews = list(reviews)
        print("\n=== Book Details ===")
        print(f"ID: {self._get_field(book_dict, 'id', 'book_id')}")
        print(f"Title: {self._get_field(book_dict, 'title')}")
        print(f"Author: {self._get_field(book_dict, 'author')}")
        print(f"ISBN: {self._get_field(book_dict, 'isbn')}")
        print(
            f"Stock: {self._get_field(book_dict, 'available_copies')}/"
            f"{self._get_field(book_dict, 'total_copies', default=self._get_field(book_dict, 'available_copies'))}"
        )
        print(f"Reviews: {len(reviews)}")
        print(f"Average rating: {average:.1f}/5" if average else "Average rating: No ratings yet")

    def search_books(self) -> None:
        query = self._get_input("Search by title/author: ")
        if not query:
            print("Enter something to search for.")
            return

        try:
            results = self._call(
                self.library_service,
                ["search_books", "find_books"],
                query,
            )
        except TypeError:
            results = self._call(
                self.library_service,
                ["search_books", "find_books"],
                title_or_author=query,
            )

        self._print_books(list(results))

    @login_required
    def borrow_book(self) -> None:
        user_id = self._get_current_user_id()
        book_id = self._prompt_int("Book ID to borrow (or 'back'): ", min_value=1, allow_cancel=True)
        if book_id is None:
            print("Borrow cancelled.")
            return

        try:
            ok = self._call(
                self.library_service,
                ["borrow_book", "borrow"],
                user_id,
                book_id,
            )
        except TypeError:
            ok = self._call(
                self.library_service,
                ["borrow_book", "borrow"],
                book_id,
                user_id=user_id,
            )

        if ok:
            print("Book borrowed. ✅")
        else:
            print("Could not borrow that book.")

    @login_required
    def return_book(self) -> None:
        user_id = self._get_current_user_id()
        book_id = self._prompt_int("Book ID to return (or 'back'): ", min_value=1, allow_cancel=True)
        if book_id is None:
            print("Return cancelled.")
            return

        try:
            ok = self._call(
                self.library_service,
                ["return_book", "return_borrowed_book", "mark_returned"],
                user_id,
                book_id,
            )
        except TypeError:
            ok = self._call(
                self.library_service,
                ["return_book", "return_borrowed_book", "mark_returned"],
                book_id,
                user_id=user_id,
            )

        if ok:
            print("Book returned. ✅")
        else:
            print("Could not return that book.")

    @login_required
    def my_history(self) -> None:
        user_id = self._get_current_user_id()

        try:
            records = self._call(
                self.library_service,
                ["my_borrow_history", "get_user_history", "user_borrow_records"],
                user_id,
            )
        except TypeError:
            records = self._call(
                self.library_service,
                ["my_borrow_history", "get_user_history", "user_borrow_records"],
                user_id=user_id,
            )

        self._print_records(list(records))

    @role_required("admin")
    def add_book(self) -> None:
        print("\n=== Add Book ===")
        title = self._get_input("Title: ")
        author = self._get_input("Author: ")
        isbn = self._get_input("ISBN: ")
        total_copies = self._prompt_int("Total copies: ", min_value=1)

        if not (title and author and isbn):
            print("Title, author, and ISBN are required.")
            return

        payload = {
            "title": title,
            "author": author,
            "isbn": isbn,
            "total_copies": total_copies,
            "available_copies": total_copies,
        }

        try:
            ok = self._call(
                self.library_service,
                ["add_book", "create_book"],
                **payload,
            )
        except TypeError:
            ok = self._call(
                self.library_service,
                ["add_book", "create_book"],
                payload,
            )

        if ok:
            print("Book added to the catalog.")
        else:
            print("Could not add the book.")

    @role_required("admin")
    def update_book_copies(self) -> None:
        book_id = self._prompt_int("Book ID to update: ", min_value=1)
        total_copies = self._prompt_int("New total copies: ", min_value=0)

        try:
            ok = self._call(
                self.library_service,
                ["update_book_copies", "update_copies", "update_book"],
                book_id,
                total_copies,
            )
        except TypeError:
            ok = self._call(
                self.library_service,
                ["update_book_copies", "update_copies", "update_book"],
                book_id=book_id,
                total_copies=total_copies,
            )

        if ok:
            print("Book copies updated.")
        else:
            print("Could not update the copy count.")

    @role_required("admin")
    def delete_book(self) -> None:
        book_id = self._prompt_int("Book ID to delete: ", min_value=1)

        try:
            ok = self._call(self.library_service, ["delete_book", "remove_book"], book_id)
        except TypeError:
            ok = self._call(
                self.library_service,
                ["delete_book", "remove_book"],
                book_id=book_id,
            )

        if ok:
            print("Book removed from the catalog.")
        else:
            print("Could not delete that book.")

    @role_required("admin")
    def view_all_records(self) -> None:
        records = self._call(
            self.library_service,
            ["view_all_borrow_records", "all_borrow_records", "list_borrow_records"],
        )
        self._print_records(list(records))

    @role_required("admin")
    def list_users(self) -> None:
        users = self._call(self.auth_service, ["list_users", "all_users", "get_all_users"])

        users = [self._to_dict(user) for user in list(users)]

        if not users:
            print("No users found.")
            return

        print("\nUsers:")
        rows = []
        for user in users:
            rows.append(
                [
                    self._get_field(user, "id", "user_id"),
                    self._get_field(user, "username"),
                    self._get_field(user, "name"),
                    self._get_field(user, "email"),
                    self._get_field(user, "role"),
                ]
            )
        self._print_table(["ID", "Username", "Name", "Email", "Role"], rows)

    @role_required("admin")
    def import_books_from_api(self) -> None:
        print("\n=== Import Books From Open Library ===")
        print("Try title, author, topic, or ISBN.")
        print("Examples: clean code | robert martin | python | 9780132350884")
        query = self._get_input("Search query: ")
        if not query:
            print("Enter something to search for.")
            return
        if len(query) < 2:
            print("Use at least 2 characters. Try title, author, topic, or ISBN.")
            return

        limit_raw = self._get_input("How many results? [default: 5]: ")
        limit = 5
        if limit_raw:
            try:
                limit = max(1, min(10, int(limit_raw)))
            except ValueError:
                print("Enter a valid number.")
                return

        results = self._call(self.library_service, ["fetch_books_from_open_library"], query, limit)
        if not results:
            print("No books came back from Open Library.")
            return

        rows = [
            [
                item.get("result_id"),
                shorten(item.get("title", "Untitled"), width=32, placeholder="..."),
                shorten(item.get("author", "Unknown"), width=20, placeholder="..."),
                item.get("first_publish_year") or "-",
                item.get("isbn") or "-",
            ]
            for item in results
        ]
        print("\nOpen Library Results:")
        self._print_table(["No", "Title", "Author", "Year", "ISBN"], rows)

        selection = self._get_input("Import which results? Use comma list, 'all', or blank to cancel: ")
        if not selection:
            print("Import cancelled.")
            return

        if selection.lower() == "all":
            selected = results
        else:
            try:
                wanted = {int(piece.strip()) for piece in selection.split(",") if piece.strip()}
            except ValueError:
                print("Use numbers separated by commas.")
                return
            selected = [item for item in results if item.get("result_id") in wanted]

        if not selected:
            print("No valid API results selected.")
            return

        copies_raw = self._get_input("Copies per imported book [default: 2]: ")
        copies = 2
        if copies_raw:
            try:
                copies = max(1, int(copies_raw))
            except ValueError:
                print("Enter a valid number.")
                return

        summary = self._call(self.library_service, ["import_books"], selected, copies)
        print(f"Imported {len(summary.get('imported', []))} book(s).")
        if summary.get("skipped"):
            print(f"Skipped {len(summary['skipped'])} duplicate or invalid result(s).")

    @role_required("admin")
    def create_admin(self) -> None:
        print("\n=== Create Admin ===")
        name = self._get_input("Name: ")
        username = self._get_input("Username: ")
        email = self._get_input("Email: ")
        password = self._get_password_input("Password: ")

        if not (name and username and email and password):
            print("Please fill in every field.")
            return

        try:
            created = self._call(
                self.auth_service,
                ["register", "create_user", "signup"],
                name=name,
                email=email,
                password=password,
                role="admin",
                username=username,
            )
        except TypeError:
            created = self._call(
                self.auth_service,
                ["register", "create_user", "signup"],
                name,
                email,
                password,
                "admin",
                username,
            )
        except (PermissionError, ValueError) as exc:
            print(exc)
            return

        if created:
            print(f"Admin account created for {self._get_field(self._to_dict(created), 'username', 'name')}.")
        else:
            print("Could not create the admin account.")

    @login_required
    def add_review(self) -> None:
        print("\n=== Add Review ===")
        user_id = self._get_current_user_id()
        reviewable_book_ids = self._get_reviewable_book_ids(user_id)

        if not reviewable_book_ids:
            print("You can only review books you have borrowed.")
            return

        print("Your reviewable books:")
        for book_id in reviewable_book_ids:
            print(f"- [{book_id}] {self._get_book_label(book_id)}")

        book_id = self._prompt_int("Book ID to review: ", min_value=1)
        if book_id not in reviewable_book_ids:
            print("Choose a book from your borrowing history.")
            return

        rating = self._prompt_int("Rating (1-5): ", min_value=1)

        if rating > 5:
            print("Rating must be between 1 and 5.")
            return

        comment = self._get_input("Comment (optional): ")

        try:
            review = self._call(
                self.review_service,
                ["add_review", "create_review"],
                user_id,
                book_id,
                rating,
                comment,
            )
        except TypeError:
            review = self._call(
                self.review_service,
                ["add_review", "create_review"],
                user_id=user_id,
                book_id=book_id,
                rating=rating,
                comment=comment,
            )
        except (PermissionError, ValueError) as exc:
            print(exc)
            return

        if review:
            print("Review saved. ⭐")
        else:
            print("Could not save the review.")

    def view_review_details(self) -> None:
        review_id = self._prompt_int("Review ID to inspect: ", min_value=1)

        try:
            review = self._call(self.review_service, ["get_review"], review_id)
        except TypeError:
            review = self._call(self.review_service, ["get_review"], review_id=review_id)

        if not review:
            print("No review found with that ID.")
            return

        review_dict = self._to_dict(review)
        print("\n=== Review Details ===")
        print(f"Review ID: {self._get_field(review_dict, 'id')}")
        print(f"Book: {self._get_book_label(self._get_field(review_dict, 'book_id'))}")
        print(
            f"User: {self._get_user_label(self._get_field(review_dict, 'user_id'), self._get_field(review_dict, 'reviewer_name', default=None))}"
        )
        print(f"Rating: {self._get_field(review_dict, 'rating')}/5")
        print(f"Created: {self._format_timestamp(self._get_field(review_dict, 'created_at', default='-'))}")
        comment = self._get_field(review_dict, "comment", default="")
        print(f"Comment: {comment if comment and comment != '-' else 'No comment'}")

    def view_book_reviews(self) -> None:
        book_id = self._prompt_int("Book ID to view reviews: ", min_value=1)

        try:
            reviews = self._call(
                self.review_service,
                ["get_book_reviews", "book_reviews"],
                book_id,
            )
        except TypeError:
            reviews = self._call(
                self.review_service,
                ["get_book_reviews", "book_reviews"],
                book_id=book_id,
            )

        reviews = list(reviews)
        if not reviews:
            print("No reviews yet for that book.")
            return

        try:
            avg_rating = self._call(
                self.review_service,
                ["get_book_average_rating", "average_rating"],
                book_id,
            )
        except (ServiceNotReadyError, TypeError):
            avg_rating = None

        print(f"\nReviews for {self._get_book_label(book_id)}:")
        if avg_rating:
            print(f"Average Rating: {avg_rating:.1f}/5")
        print("-" * 40)

        reviews.sort(key=lambda review: self._get_field(self._to_dict(review), "created_at", default=""), reverse=True)
        for review in reviews:
            r = self._to_dict(review)

            stars = "*" * self._get_field(r, "rating", default=0)
            print(
                f"  #{self._get_field(r, 'id')} | {self._get_user_label(self._get_field(r, 'user_id'), self._get_field(r, 'reviewer_name', default=None))} | "
                f"{stars} ({self._get_field(r, 'rating')}/5) | "
                f"{self._format_timestamp(self._get_field(r, 'created_at', default='-'))}"
            )

            comment = self._get_field(r, "comment", default="")
            if comment and comment != "-":
                print(f"    \"{comment}\"")

    @login_required
    def my_current_borrows(self) -> None:
        user_id = self._get_current_user_id()

        try:
            records = self._call(
                self.library_service,
                ["get_user_active_borrows", "active_borrows", "current_borrows"],
                user_id,
            )
        except TypeError:
            records = self._call(
                self.library_service,
                ["get_user_active_borrows", "active_borrows", "current_borrows"],
                user_id=user_id,
            )

        records = list(records)
        if not records:
            print("You do not have any active borrows.")
            return

        print(f"\nCurrently Borrowed Books ({len(records)}/3 limit):")
        for record in records:
            r = self._to_dict(record)
            print(
                f"- {self._get_book_label(self._get_field(r, 'book_id'))} | "
                f"Borrowed: {self._format_timestamp(self._get_field(r, 'borrowed_at'))}"
            )

    def reviews_menu(self) -> None:
        while self.current_user is not None:
            choice = self._show_menu("Reviews ⭐", ["Write or update review", "View book reviews", "View review details", "Back"])

            if choice == "1":
                self.add_review()
            elif choice == "2":
                self.view_book_reviews()
            elif choice == "3":
                self.view_review_details()
            elif choice == "4":
                return
            else:
                print("Invalid option. Try again.")

    def my_books_menu(self) -> None:
        while self.current_user is not None:
            choice = self._show_menu("My Books 📚", ["Current borrows", "Borrow history", "Back"])

            if choice == "1":
                self.my_current_borrows()
            elif choice == "2":
                self.my_history()
            elif choice == "3":
                return
            else:
                print("Invalid option. Try again.")

    def catalog_menu(self) -> None:
        while self.current_user is not None:
            choice = self._show_menu(
                "Catalog",
                ["Browse books 📚", "View book details 🔎", "Add book ➕", "Import from Open Library 🌐", "Update copies ✏️", "Remove book 🗑️", "Back"],
            )

            if choice == "1":
                self.list_books()
            elif choice == "2":
                self.view_book_details()
            elif choice == "3":
                self.add_book()
            elif choice == "4":
                self.import_books_from_api()
            elif choice == "5":
                self.update_book_copies()
            elif choice == "6":
                self.delete_book()
            elif choice == "7":
                return
            else:
                print("Invalid option. Try again.")

    def users_menu(self) -> None:
        while self.current_user is not None:
            choice = self._show_menu("Users 👥", ["List users", "Create admin", "Back"])

            if choice == "1":
                self.list_users()
            elif choice == "2":
                self.create_admin()
            elif choice == "3":
                return
            else:
                print("Invalid option. Try again.")

    @role_required("admin")
    def view_recent_reviews(self) -> None:
        try:
            reviews = self._call(self.review_service, ["list_recent_reviews"], 10)
        except ServiceNotReadyError:
            reviews = self._call(self.review_service, ["list_all_reviews", "all_reviews"])
            reviews = sorted(
                list(reviews),
                key=lambda review: self._get_field(self._to_dict(review), "created_at", default=""),
                reverse=True,
            )[:10]

        if not reviews:
            print("No reviews found.")
            return

        print("\nRecent Reviews:")
        rows = []
        for review in reviews[:10]:
            r = self._to_dict(review)
            rows.append(
                [
                    self._get_field(r, "id"),
                    self._get_book_label(self._get_field(r, "book_id")),
                    self._get_user_label(
                        self._get_field(r, "user_id"),
                        self._get_field(r, "reviewer_name", default=None),
                    ),
                    f"{self._get_field(r, 'rating')}/5",
                    self._format_timestamp(self._get_field(r, "created_at", default="-")),
                    shorten(str(self._get_field(r, "comment", default="")), width=36, placeholder="..."),
                ]
            )
        self._print_table(["ID", "Book", "User", "Rating", "Created", "Comment"], rows)

    def user_menu(self) -> None:
        while self.current_user is not None:
            choice = self._show_menu(
                "Member Menu",
                ["Available books ✅", "Browse books 📚", "Search books 🔎", "Borrow ➡️", "Return ↩️", "My books", "Reviews ⭐", "Logout 👋"],
            )

            try:
                if choice == "1":
                    self.list_available_books()
                elif choice == "2":
                    self.list_books()
                elif choice == "3":
                    self.search_books()
                elif choice == "4":
                    self.borrow_book()
                elif choice == "5":
                    self.return_book()
                elif choice == "6":
                    self.my_books_menu()
                elif choice == "7":
                    self.reviews_menu()
                elif choice == "8":
                    self.logout()
                    return
                else:
                    print("Invalid option. Try again.")
            except (ServiceNotReadyError, ValueError) as exc:
                print(f"Could not complete that action: {exc}")

    def admin_menu(self) -> None:
        while self.current_user is not None:
            choice = self._show_menu("Admin Menu", ["Catalog 📚", "Users 👥", "Borrow records 🧾", "Reviews ⭐", "Logout 👋"])

            try:
                if choice == "1":
                    self.catalog_menu()
                elif choice == "2":
                    self.users_menu()
                elif choice == "3":
                    self.view_all_records()
                elif choice == "4":
                    self.view_recent_reviews()
                elif choice == "5":
                    self.logout()
                    return
                else:
                    print("Invalid option. Try again.")
            except (ServiceNotReadyError, ValueError) as exc:
                print(f"Could not complete that action: {exc}")

    def run(self) -> None:
        while True:
            self._show_welcome_panel()
            choice = self._show_menu("Welcome to LibBuddy", ["Register ✍️", "Login 🔐", "Exit 🚪"])

            try:
                if choice == "1":
                    self.register()
                elif choice == "2":
                    self.login()

                    if self.current_user is None:
                        continue

                    role = self._get_current_user_role()
                    if role == "admin":
                        self.admin_menu()
                    else:
                        self.user_menu()
                elif choice == "3":
                    print("Goodbye. 👋")
                    break
                else:
                    print("Invalid option. Try again.")
            except ServiceNotReadyError as exc:
                print(f"Setup issue: {exc}")
            except Exception as exc:
                print(f"Something unexpected happened: {exc}")


def main() -> None:
    try:
        app = LibBuddyCLI()
    except ServiceNotReadyError as exc:
        print(f"Setup issue: {exc}")
        return

    app.run()


if __name__ == "__main__":
    main()
