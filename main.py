from __future__ import annotations

# These imports power the CLI's "work with whatever teammate code exists" trick.
# Kill them and the app either stops normalizing objects or straight-up fails to load services.
from dataclasses import asdict, is_dataclass
from importlib import import_module
from typing import Any

from utils.decorators import login_required, role_required


# This custom error keeps setup issues separate from actual user mistakes.
# Delete it and missing service code gets mixed in with random runtime junk.
class ServiceNotReadyError(RuntimeError):
    """Raised when expected teammate service methods are missing."""


# This class is the CLI traffic cop.
# Remove it and there is no menu flow, no auth handoff, basically no app.
class LibBuddyCLI:
    def __init__(self) -> None:
        # These lazy loads let the CLI survive teammates naming things slightly differently.
        # Delete any one and that feature path dies the second the app boots.
        self.auth_service = self._load_service("services.auth_service", "AuthService")
        self.library_service = self._load_service("services.library_service", "LibraryService")
        self.review_service = self._load_service("services.review_service", "ReviewService")

        # This tracks session state in memory for menus and permissions.
        # If this goes, login "works" for one print statement and then the app forgets you exist.
        self.current_user: Any = None

    # This loader keeps the CLI flexible when the service class exists, or at least the module does.
    # Delete it and startup becomes brittle enough to break over teammate merge differences.
    def _load_service(self, module_path: str, class_name: str) -> Any:
        try:
            # Dynamic import is doing the actual lookup here.
            # If removed, the CLI cannot discover service modules at runtime.
            module = import_module(module_path)
        except ImportError as exc:
            # This wraps a noisy import failure in something the app can explain cleanly.
            # Delete the wrapper and users get a traceback instead of a useful setup hint.
            raise ServiceNotReadyError(
                f"Missing module '{module_path}'. Pull teammate code before running CLI."
            ) from exc

        # This tries the clean path first: use the expected service class.
        # Delete it and you lose normal object-based service usage.
        service_cls = getattr(module, class_name, None)
        if service_cls is not None:
            try:
                # Instantiate the service if its constructor is simple enough.
                # If removed, even valid service classes never get created.
                return service_cls()
            except TypeError:
                # This fallback is here because cross-branch constructors got messy.
                # Delete it and the CLI crashes instead of degrading gracefully.
                pass

        # Returning the module is the "fine, we do it live" fallback.
        # Without this, partial teammate code means dead app.
        return module

    # This method tries multiple method names so the CLI can survive branch naming chaos.
    # Delete it and every service rename turns into a fresh bug.
    def _call(self, service: Any, names: list[str], *args: Any, **kwargs: Any) -> Any:
        for name in names:
            # getattr keeps this dynamic instead of hard-coded.
            # Kill it and the fallback chain stops existing.
            fn = getattr(service, name, None)
            if callable(fn):
                # First valid callable wins, which is exactly the point of the compatibility layer.
                # Remove the return and the CLI keeps searching like it forgot how functions work.
                return fn(*args, **kwargs)

        # This message tells you exactly which names were expected.
        # Delete it and debugging missing service methods gets way more annoying.
        joined = ", ".join(names)
        raise ServiceNotReadyError(f"Service method not found. Expected one of: {joined}")

    # This normalizes models, dataclasses, and dicts into one shape for printing.
    # Delete it and output code starts blowing up on anything that is not already a dict.
    @staticmethod
    def _to_dict(item: Any) -> dict[str, Any]:
        # Dicts are already fine, so do not overthink it.
        # Remove this and plain service responses get wrapped for no reason.
        if isinstance(item, dict):
            return item

        # Dataclasses need conversion before field lookup works.
        # Delete this and dataclass-backed responses become awkward or broken.
        if is_dataclass(item):
            return asdict(item)

        # Raw objects still get one last rescue path through __dict__.
        # Delete it and normal Python objects print like useless blobs.
        if hasattr(item, "__dict__"):
            return dict(vars(item))

        # This final wrapper stops weird scalar values from crashing the CLI.
        # Without it, one odd return shape nukes the whole display flow.
        return {"value": item}

    # Centralizing input trimming keeps every prompt from carrying whitespace garbage.
    # Delete it and validation gets way messier across the whole CLI.
    @staticmethod
    def _get_input(prompt: str) -> str:
        return input(prompt).strip()

    # This loop keeps numeric prompts from exploding on bad input.
    # Delete it and one typo turns into a crash or bad data sneaking through.
    def _prompt_int(self, prompt: str, min_value: int | None = None) -> int:
        while True:
            # Reuse the trimmed input helper so numbers do not come with junk spaces attached.
            # Skip this and the validation path becomes inconsistent.
            raw = self._get_input(prompt)
            try:
                # The int cast is the real gatekeeper here.
                # Remove it and IDs stay as strings, which breaks service lookups later.
                value = int(raw)

                # Minimum checks stop nonsense like book id 0 or negative copy counts.
                # Delete this and invalid values slide into business logic.
                if min_value is not None and value < min_value:
                    print(f"Value must be >= {min_value}.")
                    continue

                # Only return once the input is actually safe enough to use.
                # Remove this and the loop just traps users forever.
                return value
            except ValueError:
                # This keeps bad input recoverable instead of fatal.
                # Delete it and users get a traceback over typing "abc".
                print("Please enter a valid number.")

    # This helper lets the CLI read mixed response shapes without caring about key naming drama.
    # Delete it and every print block gets duplicated fallback logic.
    @staticmethod
    def _get_field(item: dict[str, Any], *keys: str, default: Any = "-") -> Any:
        for key in keys:
            # The None check matters because "present but empty" should still fall through.
            # Remove it and the CLI prints None all over the place.
            if key in item and item[key] is not None:
                return item[key]

        # This placeholder keeps output readable when a field is missing.
        # Without it, formatting lines get uglier or start failing.
        return default

    # This extracts the active user's id no matter which branch named it what.
    # Delete it and borrow/review flows lose the current user context.
    def _get_current_user_id(self) -> Any:
        user_dict = self._to_dict(self.current_user)
        return self._get_field(user_dict, "id", "user_id")

    # This normalizes role lookup for menu routing.
    # Remove it and admin users may get shoved into the wrong menu.
    def _get_current_user_role(self) -> str:
        user_dict = self._to_dict(self.current_user)
        role = str(self._get_field(user_dict, "role", default="user")).lower()
        return role

    # This handles all book list output in one place.
    # Delete it and every book-printing path grows its own messy formatting logic.
    def _print_books(self, books: list[Any]) -> None:
        # Empty-state messaging matters because silence looks like a bug.
        # Remove it and users just stare at a blank screen wondering if the app died.
        if not books:
            print("No books found.")
            return

        print("\nBooks:")
        for book in books:
            # Normalize each item before grabbing fields.
            # Delete this and object-based responses stop printing correctly.
            b = self._to_dict(book)
            print(
                f"- ID: {self._get_field(b, 'id', 'book_id')} | "
                f"{self._get_field(b, 'title')} by {self._get_field(b, 'author')} | "
                f"ISBN: {self._get_field(b, 'isbn')} | "
                f"Available: {self._get_field(b, 'available_copies')}"
            )

    # Same deal as books, but for borrow history and admin record views.
    # Remove it and record output turns into copy-paste soup.
    def _print_records(self, records: list[Any]) -> None:
        if not records:
            print("No borrow records found.")
            return

        print("\nBorrow Records:")
        for record in records:
            # Normalize the shape before field lookup so records from different branches still print.
            # Delete this and mixed return types become a runtime headache.
            r = self._to_dict(record)
            print(
                f"- Record ID: {self._get_field(r, 'id', 'record_id')} | "
                f"User: {self._get_field(r, 'user_id')} | "
                f"Book: {self._get_field(r, 'book_id')} | "
                f"Status: {self._get_field(r, 'status')} | "
                f"Borrowed: {self._get_field(r, 'borrowed_at')} | "
                f"Returned: {self._get_field(r, 'returned_at', default='-')}"
            )

    # Registration wires the CLI prompt layer to the auth service.
    # Delete this and new users are locked out before the app even starts being useful.
    def register(self) -> None:
        print("\n=== Register ===")
        name = self._get_input("Name: ")
        email = self._get_input("Email: ")
        password = self._get_input("Password: ")

        # Basic presence checks stop trash input before it reaches the service layer.
        # Remove this and you lean entirely on downstream exceptions for user-facing flow.
        if not (name and email and password):
            print("All fields are required.")
            return

        try:
            # Keyword args are the clean path for the current auth service.
            # Delete this attempt and newer service signatures may stop working.
            created = self._call(
                self.auth_service,
                ["register", "create_user", "signup"],
                name=name,
                email=email,
                password=password,
                role="user",
            )
        except TypeError:
            # Positional fallback keeps older service versions alive.
            # Remove it and branch compatibility gets wrecked again.
            created = self._call(
                self.auth_service,
                ["register", "create_user", "signup"],
                name,
                email,
                password,
            )

        # This success branch is the only user feedback proving account creation worked.
        # Delete it and the CLI feels broken even when it succeeds.
        if created:
            print("Registration successful. You can now log in.")
        else:
            print("Registration failed.")

    # Login is the gate to every user and admin action.
    # Delete it and the rest of the app is basically decorative.
    def login(self) -> None:
        print("\n=== Login ===")
        email = self._get_input("Email: ")
        password = self._get_input("Password: ")

        if not (email and password):
            print("Email and password are required.")
            return

        try:
            # Keyword args first, because that's the current service contract.
            # Remove this and the clean path for auth dies.
            user = self._call(
                self.auth_service,
                ["login", "authenticate", "signin"],
                email=email,
                password=password,
            )
        except TypeError:
            # Positional fallback keeps older versions from face-planting.
            # Delete it and compatibility gets fragile again.
            user = self._call(
                self.auth_service,
                ["login", "authenticate", "signin"],
                email,
                password,
            )

        # This protects the session from being set to garbage on failed auth.
        # Remove it and failed logins can still mutate app state.
        if not user:
            print("Invalid credentials.")
            return

        # This is the actual session handoff.
        # Delete it and every post-login feature thinks nobody is logged in.
        self.current_user = user
        print("Login successful.")

    # Logout clears both the service session and the CLI session.
    # Delete it and users can get stuck "logged in" until restart.
    def logout(self) -> None:
        try:
            # Tell the auth service too, if it supports logout.
            # Remove this and internal auth state can drift from CLI state.
            self._call(self.auth_service, ["logout", "signout"])
        except ServiceNotReadyError:
            # Some branches never implemented logout, so we fail soft here.
            # Delete the guard and logout becomes another crash point.
            pass

        # This local reset is the part menus actually care about.
        # Delete it and role-based loops keep running like nothing happened.
        self.current_user = None
        print("Logged out.")

    # Thin wrapper around book listing so menus stay readable.
    # Delete it and multiple menu options lose their book view.
    def list_books(self) -> None:
        books = self._call(self.library_service, ["list_books", "get_books", "all_books"])
        self._print_books(list(books))

    # Search asks for text, calls the service, then reuses the common printer.
    # Remove it and discoverability in the CLI drops hard.
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
            # Some older service code expected a named search parameter.
            # Delete this and that branch style breaks instantly.
            results = self._call(
                self.library_service,
                ["search_books", "find_books"],
                title_or_author=query,
            )

        self._print_books(list(results))

    # Borrow flow ties the current user to a book id and hands off to services.
    # Delete it and the core library feature is gone. Bit of a problem for LibBuddy.
    @login_required
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
            # Positional order changed across branches, so this fallback saves us from that drama.
            # Delete it and valid borrow calls can still fail on signature mismatch.
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

    # Return flow mirrors borrow flow and is just as central.
    # Delete it and inventory only goes down forever. Cute bug, terrible app.
    @login_required
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

    # History view gives users proof of their borrow activity.
    # Delete it and there is no audit trail in the CLI.
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

    # Admin-only book creation path.
    # Delete it and the catalog becomes read-only from the CLI.
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

        # Build once, pass around once. Less mess, fewer mismatched args.
        # Delete this dict and the same values get repeated across call paths.
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
            # Older service code sometimes wanted one payload object instead.
            # Delete this and that path breaks for no good reason.
            ok = self._call(
                self.library_service,
                ["add_book", "create_book"],
                payload,
            )

        if ok:
            print("Book added.")
        else:
            print("Failed to add book.")

    # Admin update for inventory counts.
    # Delete it and there is no way to fix stock numbers without editing data files by hand.
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
            print("Failed to update book copies.")

    # Admin delete path for books.
    # Delete it and bad catalog entries become immortal.
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
            print("Book deleted.")
        else:
            print("Failed to delete book.")

    # Admin borrow-record view for the whole system.
    # Delete it and admins lose visibility into who borrowed what.
    @role_required("admin")
    def view_all_records(self) -> None:
        records = self._call(
            self.library_service,
            ["view_all_borrow_records", "all_borrow_records", "list_borrow_records"],
        )
        self._print_records(list(records))

    # Admin user list view.
    # Delete it and there is no CLI visibility into account data.
    @role_required("admin")
    def list_users(self) -> None:
        users = self._call(self.auth_service, ["list_users", "all_users", "get_all_users"])

        # Normalize now so the print loop does not care about response shape.
        # Remove this and mixed return types turn into repetitive conditionals.
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

    # Review creation is one of the user-facing extras that proves the app is more than CRUD.
    # Delete it and ratings become read-only fiction.
    @login_required
    def add_review(self) -> None:
        print("\n=== Add Review ===")
        user_id = self._get_current_user_id()
        book_id = self._prompt_int("Book ID to review: ", min_value=1)
        rating = self._prompt_int("Rating (1-5): ", min_value=1)

        # _prompt_int only checks the floor, so this upper bound still matters.
        # Delete it and invalid 6/7/99 ratings reach the service layer.
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

    # This view prints all reviews for one book plus the average when possible.
    # Delete it and ratings exist in storage but users cannot really see them.
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

        try:
            # Average rating is optional because not every branch implemented it.
            # Delete this call and users lose the quick summary, which is kind of the useful part.
            avg_rating = self._call(
                self.review_service,
                ["get_book_average_rating", "average_rating"],
                book_id,
            )
        except (ServiceNotReadyError, TypeError):
            # Fail soft here so missing aggregate support does not kill review viewing.
            # Remove the guard and older branches crash on read.
            avg_rating = None

        print(f"\nReviews for Book ID {book_id}:")
        if avg_rating:
            print(f"Average Rating: {avg_rating:.1f}/5")
        print("-" * 40)

        for review in reviews:
            r = self._to_dict(review)

            # Stars make ratings readable in one glance.
            # Delete this and output gets more sterile and harder to scan.
            stars = "*" * self._get_field(r, "rating", default=0)
            print(f"  User {self._get_field(r, 'user_id')}: {stars}")

            # Comments stay optional so blank reviews do not print ugly filler.
            # Delete the guard and you get meaningless quote lines everywhere.
            comment = self._get_field(r, "comment", default="")
            if comment and comment != "-":
                print(f"    \"{comment}\"")

    # This is the lightweight "what do I currently have out?" screen.
    # Delete it and users have history, but no quick active snapshot.
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
            print("You have no books currently borrowed.")
            return

        print(f"\nCurrently Borrowed Books ({len(records)}/3 limit):")
        for record in records:
            r = self._to_dict(record)
            print(
                f"- Book ID: {self._get_field(r, 'book_id')} | "
                f"Borrowed: {self._get_field(r, 'borrowed_at')}"
            )

    # User menu keeps looping until logout.
    # Delete this and regular users have nowhere to actually use the app.
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
                # This ladder is boring on purpose: explicit beats clever in CLI menus.
                # Delete any branch and that menu option becomes a liar.
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
                # Catching here keeps one bad action from killing the whole menu session.
                # Delete it and users get punted out by recoverable issues.
                print(f"Action failed: {exc}")

    # Admin menu exposes catalog and user management actions.
    # Delete it and admin users are basically just regular users with a fancy title.
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

    # Main app loop for the anonymous landing menu.
    # Delete it and the CLI boots with no usable entry path.
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

                    # This guard matters because failed login should not open any menu.
                    # Delete it and bad creds can still fall into role routing.
                    if self.current_user is None:
                        continue

                    # Role decides which menu the user gets. Pretty important detail.
                    # Delete this and admins lose admin actions or users get the wrong access.
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
                # Setup issues deserve a cleaner message than a traceback.
                # Delete this and broken imports look like random crashes.
                print(f"Setup issue: {exc}")
            except Exception as exc:  # noqa: BLE001
                # Broad catch keeps the CLI from hard-crashing in class demos.
                # Delete it and one unexpected bug kills the entire session.
                print(f"Unexpected error: {exc}")


# Thin wrapper so tests and direct execution share the same entry path.
# Delete it and the module still works manually, but startup handling gets messier.
def main() -> None:
    try:
        # App creation can fail if service modules are missing.
        # Delete the guard and startup throws a raw exception instead of a sane message.
        app = LibBuddyCLI()
    except ServiceNotReadyError as exc:
        print(f"Setup issue: {exc}")
        return

    # This is the actual handoff into the CLI loop.
    # Remove it and startup ends right after creating the app. Super useful.
    app.run()


# Standard script entrypoint.
# Delete it and `python main.py` stops launching the app.
if __name__ == "__main__":
    main()
