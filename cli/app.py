from __future__ import annotations

# sys gives us the terminal handles for masked password input.
# Delete it and the CLI cannot tell whether it's running in a real terminal.
import sys
# These imports power the CLI's "work with whatever teammate code exists" trick.
# Kill them and the app either stops normalizing objects or straight-up fails to load services.
from datetime import datetime
from dataclasses import asdict, is_dataclass
from importlib import import_module
from textwrap import shorten
from typing import Any

from utils.decorators import login_required, role_required

try:
    # If tabulate is around, use it for cleaner tables without hand-rolling more UI code.
    # Delete this and the branch loses the easiest visual upgrade in the whole app.
    from tabulate import tabulate
except ImportError:  # pragma: no cover
    # Fallback matters because the CLI still has to work on plain Python installs.
    # Delete it and missing one optional package kills the app at import time.
    tabulate = None


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

    # This masks passwords with stars in a real terminal so people are not typing secrets in public.
    # Delete it and password entry stays fully visible, which is sloppy for demos and real use.
    def _get_password_input(self, prompt: str) -> str:
        # Tests and non-interactive runs do not have a proper TTY, so fall back cleanly there.
        # Delete this and the suite starts hanging or failing on terminal-only logic.
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

        # termios/tty gives Unix terminals raw character reads so we can paint one star per key.
        # Delete this path and Linux/macOS users lose the masking feature entirely.
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
                print("Enter a valid number.")

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

    # This keeps timestamps readable instead of dumping raw ISO strings everywhere.
    # Delete it and the CLI goes back to looking like a log file.
    @staticmethod
    def _format_timestamp(value: Any) -> str:
        if not value or value == "-":
            return "-"
        try:
            return datetime.fromisoformat(str(value)).strftime("%Y-%m-%d %H:%M")
        except ValueError:
            return str(value)

    # Book title lookup makes the UI human-readable instead of ID-only survival mode.
    # Delete it and the user keeps translating book IDs in their head like a machine.
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

    # User labels make review and admin screens feel like people are using them, not just IDs.
    # Delete it and the CLI keeps outputting anonymous number soup.
    def _get_user_label(self, user_id: Any) -> str:
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

    # Review prompts are nicer when users can see which books they actually touched.
    # Delete it and review entry goes back to guessing IDs from memory.
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

    # One tiny helper keeps menus compact without making them cryptic.
    # Delete it and the CLI goes back to repeating the same print boilerplate everywhere.
    def _show_menu(self, title: str, options: list[str]) -> str:
        print("\n" + "=" * 72)
        print(title.center(72))
        print("=" * 72)
        for index, option in enumerate(options, start=1):
            print(f"{index}. {option}")
        return self._get_input("Select an option: ")

    # This keeps table output readable without dragging in a package just for tests and fallback mode.
    # Delete it and every list screen goes back to uneven, scroll-heavy print spam.
    @staticmethod
    def _print_table(headers: list[str], rows: list[list[Any]]) -> None:
        if not rows:
            return

        # Use the nicer renderer when it's installed. Easy win, zero logic drama.
        # Delete this and the interface stays more basic than it needs to be.
        if tabulate is not None:
            print(tabulate(rows, headers=headers, tablefmt="fancy_grid"))
            return

        normalized = [[str(cell) for cell in row] for row in rows]
        widths = [
            max(len(str(header)), *(len(row[index]) for row in normalized))
            for index, header in enumerate(headers)
        ]

        # One renderer keeps the header and body aligned instead of drifting by accident.
        # Delete it and the table math gets duplicated immediately.
        def render(row: list[str]) -> str:
            return " | ".join(cell.ljust(widths[index]) for index, cell in enumerate(row))

        print(render(headers))
        print("-+-".join("-" * width for width in widths))
        for row in normalized:
            print(render(row))

    # A small stats panel makes the landing screen feel like an actual app, not a blank prompt farm.
    # Delete it and the first impression gets a lot flatter again.
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

        print("\n" + "=" * 72)
        print("LIBBUDDY".center(72))
        print("CLI Library Desk".center(72))
        print("=" * 72)
        print(f"Catalog: {book_count} books | Members: {user_count} users | Reviews: {review_count}")
        print("-" * 72)

    # This handles all book list output in one place.
    # Delete it and every book-printing path grows its own messy formatting logic.
    def _print_books(self, books: list[Any]) -> None:
        # Empty-state messaging matters because silence looks like a bug.
        # Remove it and users just stare at a blank screen wondering if the app died.
        if not books:
            print("No books found.")
            return

        print("\nBooks:")
        rows = []
        for book in books:
            # Normalize each item before grabbing fields.
            # Delete this and object-based responses stop printing correctly.
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

    # Same deal as books, but for borrow history and admin record views.
    # Remove it and record output turns into copy-paste soup.
    def _print_records(self, records: list[Any]) -> None:
        if not records:
            print("No borrow records found.")
            return

        print("\nBorrow Records:")
        rows = []
        for record in records:
            # Normalize the shape before field lookup so records from different branches still print.
            # Delete this and mixed return types become a runtime headache.
            r = self._to_dict(record)
            rows.append(
                [
                    self._get_field(r, "id", "record_id"),
                    self._get_user_label(self._get_field(r, "user_id")),
                    self._get_book_label(self._get_field(r, "book_id")),
                    self._get_field(r, "status"),
                    self._format_timestamp(self._get_field(r, "borrowed_at")),
                    self._format_timestamp(self._get_field(r, "returned_at", default="-")),
                ]
            )
        self._print_table(["ID", "User", "Book", "Status", "Borrowed", "Returned"], rows)

    # Registration wires the CLI prompt layer to the auth service.
    # Delete this and new users are locked out before the app even starts being useful.
    def register(self) -> None:
        print("\n=== Register ===")
        name = self._get_input("Name: ")
        username = self._get_input("Username: ")
        email = self._get_input("Email: ")
        # Use the masked prompt here because registration is the first place people expose passwords.
        # Delete it and new-account demos still leak the password on screen.
        password = self._get_password_input("Password: ")

        # Basic presence checks stop trash input before it reaches the service layer.
        # Remove this and you lean entirely on downstream exceptions for user-facing flow.
        if not (name and username and email and password):
            print("Please fill in every field.")
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
                username=username,
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
        except (PermissionError, ValueError) as exc:
            print(exc)
            return

        # This success branch is the only user feedback proving account creation worked.
        # Delete it and the CLI feels broken even when it succeeds.
        if created:
            print("Account created. You can log in now.")
        else:
            print("Could not create the account.")

    # Login is the gate to every user and admin action.
    # Delete it and the rest of the app is basically decorative.
    def login(self) -> None:
        print("\n=== Login ===")
        email = self._get_input("Email or username: ")
        # Login needs the same masking or the fix is only half real.
        # Delete it and the most common password prompt stays visible.
        password = self._get_password_input("Password: ")

        if not (email and password):
            print("Enter both your email or username and your password.")
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
        except ValueError as exc:
            print(exc)
            return

        # This protects the session from being set to garbage on failed auth.
        # Remove it and failed logins can still mutate app state.
        if not user:
            print("Login failed. Check your details and try again.")
            return

        # This is the actual session handoff.
        # Delete it and every post-login feature thinks nobody is logged in.
        self.current_user = user
        print(f"Login successful. Welcome, {self._get_field(self._to_dict(user), 'username', 'name')}.")

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
        print("You have been logged out.")

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
            print("Enter something to search for.")
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
            print("Book borrowed.")
        else:
            print("Could not borrow that book.")

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
            print("Book returned.")
        else:
            print("Could not return that book.")

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
            print("Book added to the catalog.")
        else:
            print("Could not add the book.")

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
            print("Could not update the copy count.")

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
            print("Book removed from the catalog.")
        else:
            print("Could not delete that book.")

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

    # API import gives admins a fast way to seed the catalog with real books.
    # Delete it and "fetch books" is just a thing we said, not a thing we built.
    @role_required("admin")
    def import_books_from_api(self) -> None:
        print("\n=== Import Books From Open Library ===")
        query = self._get_input("Search query: ")
        if not query:
            print("Enter something to search for.")
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

    # Admin account creation keeps role management inside the app instead of in raw JSON edits.
    # Delete it and adding a second admin goes back to manual file surgery.
    @role_required("admin")
    def create_admin(self) -> None:
        print("\n=== Create Admin ===")
        name = self._get_input("Name: ")
        username = self._get_input("Username: ")
        email = self._get_input("Email: ")
        # Admin creation handles credentials too, so it gets the masked prompt as well.
        # Delete it and only some password screens get the privacy upgrade.
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

    # Review creation is one of the user-facing extras that proves the app is more than CRUD.
    # Delete it and ratings become read-only fiction.
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
        except (PermissionError, ValueError) as exc:
            print(exc)
            return

        if review:
            print("Review saved.")
        else:
            print("Could not save the review.")

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
            print("No reviews yet for that book.")
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

        print(f"\nReviews for {self._get_book_label(book_id)}:")
        if avg_rating:
            print(f"Average Rating: {avg_rating:.1f}/5")
        print("-" * 40)

        reviews.sort(key=lambda review: self._get_field(self._to_dict(review), "created_at", default=""), reverse=True)
        for review in reviews:
            r = self._to_dict(review)

            # Stars make ratings readable in one glance.
            # Delete this and output gets more sterile and harder to scan.
            stars = "*" * self._get_field(r, "rating", default=0)
            print(
                f"  {self._get_user_label(self._get_field(r, 'user_id'))} | "
                f"{stars} ({self._get_field(r, 'rating')}/5) | "
                f"{self._format_timestamp(self._get_field(r, 'created_at', default='-'))}"
            )

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
            print("You do not have any active borrows.")
            return

        print(f"\nCurrently Borrowed Books ({len(records)}/3 limit):")
        for record in records:
            r = self._to_dict(record)
            print(
                f"- {self._get_book_label(self._get_field(r, 'book_id'))} | "
                f"Borrowed: {self._format_timestamp(self._get_field(r, 'borrowed_at'))}"
            )

    # This keeps review actions out of the main user menu so it feels less bloated.
    # Delete it and the user menu goes back to being a long grocery list.
    def reviews_menu(self) -> None:
        while self.current_user is not None:
            choice = self._show_menu("Reviews", ["Write or update review", "View book reviews", "Back"])

            if choice == "1":
                self.add_review()
            elif choice == "2":
                self.view_book_reviews()
            elif choice == "3":
                return
            else:
                print("Invalid option. Try again.")

    # This gives users one place for active loans and history instead of crowding the main menu.
    # Delete it and the user menu gets longer again for no good reason.
    def my_books_menu(self) -> None:
        while self.current_user is not None:
            choice = self._show_menu("My Books", ["Current borrows", "Borrow history", "Back"])

            if choice == "1":
                self.my_current_borrows()
            elif choice == "2":
                self.my_history()
            elif choice == "3":
                return
            else:
                print("Invalid option. Try again.")

    # Admin catalog actions are grouped here so the main admin screen stays short.
    # Delete it and admin flow goes back to dumping every action at once.
    def catalog_menu(self) -> None:
        while self.current_user is not None:
            choice = self._show_menu(
                "Catalog",
                ["Browse books", "Add book", "Import from Open Library", "Update copies", "Remove book", "Back"],
            )

            if choice == "1":
                self.list_books()
            elif choice == "2":
                self.add_book()
            elif choice == "3":
                self.import_books_from_api()
            elif choice == "4":
                self.update_book_copies()
            elif choice == "5":
                self.delete_book()
            elif choice == "6":
                return
            else:
                print("Invalid option. Try again.")

    # Grouping user actions keeps admin navigation short while still exposing account controls.
    # Delete it and the main admin menu starts bloating again.
    def users_menu(self) -> None:
        while self.current_user is not None:
            choice = self._show_menu("Users", ["List users", "Create admin", "Back"])

            if choice == "1":
                self.list_users()
            elif choice == "2":
                self.create_admin()
            elif choice == "3":
                return
            else:
                print("Invalid option. Try again.")

    # This gives admins a quick review overview instead of forcing book-by-book digging.
    # Delete it and review moderation stays awkward.
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
                    self._get_book_label(self._get_field(r, "book_id")),
                    self._get_user_label(self._get_field(r, "user_id")),
                    f"{self._get_field(r, 'rating')}/5",
                    self._format_timestamp(self._get_field(r, "created_at", default="-")),
                    shorten(str(self._get_field(r, "comment", default="")), width=36, placeholder="..."),
                ]
            )
        self._print_table(["Book", "User", "Rating", "Created", "Comment"], rows)

    # User menu keeps looping until logout.
    # Delete this and regular users have nowhere to actually use the app.
    def user_menu(self) -> None:
        while self.current_user is not None:
            choice = self._show_menu("Member Menu", ["Browse books", "Search books", "Borrow", "Return", "My books", "Reviews", "Logout"])

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
                    self.my_books_menu()
                elif choice == "6":
                    self.reviews_menu()
                elif choice == "7":
                    self.logout()
                    return
                else:
                    print("Invalid option. Try again.")
            except (ServiceNotReadyError, ValueError) as exc:
                # Catching here keeps one bad action from killing the whole menu session.
                # Delete it and users get punted out by recoverable issues.
                print(f"Could not complete that action: {exc}")

    # Admin menu exposes catalog and user management actions.
    # Delete it and admin users are basically just regular users with a fancy title.
    def admin_menu(self) -> None:
        while self.current_user is not None:
            choice = self._show_menu("Admin Menu", ["Catalog", "Users", "Borrow records", "Reviews", "Logout"])

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

    # Main app loop for the anonymous landing menu.
    # Delete it and the CLI boots with no usable entry path.
    def run(self) -> None:
        while True:
            self._show_welcome_panel()
            choice = self._show_menu("Welcome to LibBuddy", ["Register", "Login", "Exit"])

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
                print(f"Something unexpected happened: {exc}")


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
