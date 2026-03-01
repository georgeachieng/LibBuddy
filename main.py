"""LibBuddy CLI entrypoint.

Person 4 scope:
- Menu-driven CLI flow
- Input validation
- Calls into auth/library services
"""

from __future__ import annotations

from dataclasses import asdict, is_dataclass
from importlib import import_module
from typing import Any


class ServiceNotReadyError(RuntimeError):
    """Raised when expected teammate service methods are missing."""


class LibBuddyCLI:
    def __init__(self) -> None:
        self.auth_service = self._load_service("services.auth_service", "AuthService")
        self.library_service = self._load_service("services.library_service", "LibraryService")
        self.review_service = self._load_service("services.review_service", "ReviewService")
        self.current_user: Any = None

    def _load_service(self, module_path: str, class_name: str) -> Any:
        """Load a service class if present, otherwise return the module as callable container."""
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
                # Constructor may require deps in other branches; fall back to module-level API.
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

    @staticmethod
    def _get_input(prompt: str) -> str:
        return input(prompt).strip()

    def _prompt_int(self, prompt: str, min_value: int | None = None) -> int:
        while True:
            raw = self._get_input(prompt)
            try:
                value = int(raw)
                if min_value is not None and value < min_value:
                    print(f"Value must be >= {min_value}.")
                    continue
                return value
            except ValueError:
                print("Please enter a valid number.")

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

    def _print_books(self, books: list[Any]) -> None:
        if not books:
            print("No books found.")
            return

        print("\nBooks:")
        for book in books:
            b = self._to_dict(book)
            print(
                f"- ID: {self._get_field(b, 'id', 'book_id')} | "
                f"{self._get_field(b, 'title')} by {self._get_field(b, 'author')} | "
                f"ISBN: {self._get_field(b, 'isbn')} | "
                f"Available: {self._get_field(b, 'available_copies')}"
            )

    def _print_records(self, records: list[Any]) -> None:
        if not records:
            print("No borrow records found.")
            return

        print("\nBorrow Records:")
        for record in records:
            r = self._to_dict(record)
            print(
                f"- Record ID: {self._get_field(r, 'id', 'record_id')} | "
                f"User: {self._get_field(r, 'user_id')} | "
                f"Book: {self._get_field(r, 'book_id')} | "
                f"Status: {self._get_field(r, 'status')} | "
                f"Borrowed: {self._get_field(r, 'borrowed_at')} | "
                f"Returned: {self._get_field(r, 'returned_at', default='-')}"
            )

    def register(self) -> None:
        print("\n=== Register ===")
        name = self._get_input("Name: ")
        email = self._get_input("Email: ")
        password = self._get_input("Password: ")

        if not (name and email and password):
            print("All fields are required.")
            return

        try:
            created = self._call(
                self.auth_service,
                ["register", "create_user", "signup"],
                name=name,
                email=email,
                password=password,
                role="user",
            )
        except TypeError:
            created = self._call(
                self.auth_service,
                ["register", "create_user", "signup"],
                name,
                email,
                password,
            )

        if created:
            print("Registration successful. You can now log in.")
        else:
            print("Registration failed.")

    def login(self) -> None:
        print("\n=== Login ===")
        email = self._get_input("Email: ")
        password = self._get_input("Password: ")

        if not (email and password):
            print("Email and password are required.")
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

        if not user:
            print("Invalid credentials.")
            return

        self.current_user = user
        print("Login successful.")

    def logout(self) -> None:
        try:
            self._call(self.auth_service, ["logout", "signout"])
        except ServiceNotReadyError:
            pass
        self.current_user = None
        print("Logged out.")

    def list_books(self) -> None:
        books = self._call(self.library_service, ["list_books", "get_books", "all_books"])
        self._print_books(list(books))

    def search_books(self) -> None:
        query = self._get_input("Search by title/author: ")
        if not query:
            print("Search query cannot be empty.")
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

    def borrow_book(self) -> None:
        user_id = self._get_current_user_id()
        book_id = self._prompt_int("Book ID to borrow: ", min_value=1)

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
            print("Book borrowed successfully.")
        else:
            print("Could not borrow book.")

    def return_book(self) -> None:
        user_id = self._get_current_user_id()
        book_id = self._prompt_int("Book ID to return: ", min_value=1)

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
            print("Book returned successfully.")
        else:
            print("Could not return book.")

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
            print("Book added.")
        else:
            print("Failed to add book.")

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
            print("Failed to update book copies.")

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
            print("Book deleted.")
        else:
            print("Failed to delete book.")

    def view_all_records(self) -> None:
        records = self._call(
            self.library_service,
            ["view_all_borrow_records", "all_borrow_records", "list_borrow_records"],
        )
        self._print_records(list(records))

    def list_users(self) -> None:
        users = self._call(self.auth_service, ["list_users", "all_users", "get_all_users"])
        users = [self._to_dict(user) for user in list(users)]

        if not users:
            print("No users found.")
            return

        print("\nUsers:")
        for user in users:
            print(
                f"- ID: {self._get_field(user, 'id', 'user_id')} | "
                f"Name: {self._get_field(user, 'name')} | "
                f"Email: {self._get_field(user, 'email')} | "
                f"Role: {self._get_field(user, 'role')}"
            )

    def add_review(self) -> None:
        print("\n=== Add Review ===")
        user_id = self._get_current_user_id()
        book_id = self._prompt_int("Book ID to review: ", min_value=1)
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

        if review:
            print("Review added successfully.")
        else:
            print("Failed to add review.")

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
            print("No reviews found for this book.")
            return

        # Get average rating
        try:
            avg_rating = self._call(
                self.review_service,
                ["get_book_average_rating", "average_rating"],
                book_id,
            )
        except (ServiceNotReadyError, TypeError):
            avg_rating = None

        print(f"\nReviews for Book ID {book_id}:")
        if avg_rating:
            print(f"Average Rating: {avg_rating:.1f}/5")
        print("-" * 40)

        for review in reviews:
            r = self._to_dict(review)
            stars = "*" * self._get_field(r, "rating", default=0)
            print(f"  User {self._get_field(r, 'user_id')}: {stars}")
            comment = self._get_field(r, "comment", default="")
            if comment and comment != "-":
                print(f"    \"{comment}\"")

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
            print("You have no books currently borrowed.")
            return

        print(f"\nCurrently Borrowed Books ({len(records)}/3 limit):")
        for record in records:
            r = self._to_dict(record)
            print(
                f"- Book ID: {self._get_field(r, 'book_id')} | "
                f"Borrowed: {self._get_field(r, 'borrowed_at')}"
            )

    def user_menu(self) -> None:
        while self.current_user is not None:
            print("\n=== User Menu ===")
            print("1. List books")
            print("2. Search books")
            print("3. Borrow book")
            print("4. Return book")
            print("5. My current borrows")
            print("6. My borrow history")
            print("7. Add review")
            print("8. View book reviews")
            print("9. Logout")

            choice = self._get_input("Choose an option: ")

            try:
                if choice == "1":
                    self.list_books()
                elif choice == "2":
                    self.search_books()
                elif choice == "3":
                    self.borrow_book()
                elif choice == "4":
                    self.return_book()
                elif choice == "5":
                    self.my_current_borrows()
                elif choice == "6":
                    self.my_history()
                elif choice == "7":
                    self.add_review()
                elif choice == "8":
                    self.view_book_reviews()
                elif choice == "9":
                    self.logout()
                    return
                else:
                    print("Invalid option. Try again.")
            except (ServiceNotReadyError, ValueError) as exc:
                print(f"Action failed: {exc}")

    def admin_menu(self) -> None:
        while self.current_user is not None:
            print("\n=== Admin Menu ===")
            print("1. List books")
            print("2. Add book")
            print("3. Update book copies")
            print("4. Delete book")
            print("5. View all borrow records")
            print("6. List all users")
            print("7. View book reviews")
            print("8. Logout")

            choice = self._get_input("Choose an option: ")

            try:
                if choice == "1":
                    self.list_books()
                elif choice == "2":
                    self.add_book()
                elif choice == "3":
                    self.update_book_copies()
                elif choice == "4":
                    self.delete_book()
                elif choice == "5":
                    self.view_all_records()
                elif choice == "6":
                    self.list_users()
                elif choice == "7":
                    self.view_book_reviews()
                elif choice == "8":
                    self.logout()
                    return
                else:
                    print("Invalid option. Try again.")
            except (ServiceNotReadyError, ValueError) as exc:
                print(f"Action failed: {exc}")

    def run(self) -> None:
        while True:
            print("\n=== Welcome to LibBuddy ===")
            print("1. Register")
            print("2. Login")
            print("3. Exit")

            choice = self._get_input("Choose an option: ")

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
                    print("Goodbye.")
                    break
                else:
                    print("Invalid option. Try again.")
            except ServiceNotReadyError as exc:
                print(f"Setup issue: {exc}")
            except Exception as exc:  # noqa: BLE001
                print(f"Unexpected error: {exc}")


def main() -> None:
    try:
        app = LibBuddyCLI()
    except ServiceNotReadyError as exc:
        print(f"Setup issue: {exc}")
        return
    app.run()


if __name__ == "__main__":
    main()
