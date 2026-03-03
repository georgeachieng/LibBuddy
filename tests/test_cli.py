import io
import unittest
from contextlib import redirect_stdout
from unittest.mock import Mock, patch

# Import the CLI module once and stub services underneath it.
# Delete this and the tests stop exercising the real menu methods.
import main as cli_module


# CLI tests stay small on purpose: just enough to lock down key flows.
# Delete this file and menu regressions become manual QA homework.
class CLITests(unittest.TestCase):
    def make_cli(self, auth=None, library=None, review=None):
        # Default mocks keep tests tiny and focused.
        # Delete this convenience and every test gets repetitive fast.
        auth = auth or Mock()
        library = library or Mock()
        review = review or Mock()

        # Patch service loading so tests never hit real disk-backed services.
        # Delete this and CLI tests become integration tests by accident.
        with patch.object(
            cli_module.LibBuddyCLI,
            "_load_service",
            side_effect=[auth, library, review],
        ):
            cli = cli_module.LibBuddyCLI()

        return cli, auth, library, review

    def capture_output(self, fn, inputs=None):
        # StringIO catches prints so assertions can inspect CLI output.
        # Delete it and these tests can only guess what got printed.
        buffer = io.StringIO()
        inputs = inputs or []

        # Mock input so prompts do not block test execution forever.
        # Delete this and the tests hang waiting for a human.
        with patch("builtins.input", side_effect=inputs), redirect_stdout(buffer):
            fn()

        return buffer.getvalue()

    def test_register_requires_all_fields(self):
        cli, auth, _, _ = self.make_cli()

        output = self.capture_output(
            cli.register,
            inputs=["", "ashanti@example.com", "secret123"],
        )

        # This proves the CLI blocks empty fields before touching auth.
        # Delete these and the guard can break silently.
        self.assertIn("All fields are required.", output)
        auth.register.assert_not_called()

    def test_login_sets_current_user_on_success(self):
        cli, auth, _, _ = self.make_cli()
        auth.login.return_value = {"id": 1, "email": "ashanti@example.com", "role": "user"}

        output = self.capture_output(
            cli.login,
            inputs=["ashanti@example.com", "secret123"],
        )

        # Session mutation is the whole point of login from the CLI side.
        # Delete these and auth flow regressions get missed.
        self.assertIn("Login successful.", output)
        self.assertEqual(cli.current_user["email"], "ashanti@example.com")

    def test_list_books_prints_book_details(self):
        cli, _, library, _ = self.make_cli()
        library.list_books.return_value = [
            {
                "id": 1,
                "title": "Clean Code",
                "author": "Robert C. Martin",
                "isbn": "9780132350884",
                "available_copies": 2,
            }
        ]

        output = self.capture_output(cli.list_books)

        # These checks lock down the actual user-facing book output.
        # Delete them and formatting can drift without anybody noticing.
        self.assertIn("Books:", output)
        self.assertIn("Clean Code by Robert C. Martin", output)
        self.assertIn("Available: 2", output)

    def test_add_review_rejects_rating_above_five_before_calling_service(self):
        cli, _, _, review = self.make_cli()
        cli.current_user = {"id": 4, "role": "user"}

        output = self.capture_output(
            cli.add_review,
            inputs=["12", "6"],
        )

        # This proves the CLI does its own upper-bound check before the service sees bad input.
        # Delete it and invalid ratings can leak deeper into the stack.
        self.assertIn("Rating must be between 1 and 5.", output)
        review.add_review.assert_not_called()

    def test_add_book_blocks_non_admin_user_before_prompting(self):
        cli, _, library, _ = self.make_cli()
        cli.current_user = {"id": 4, "role": "user"}

        output = self.capture_output(cli.add_book)

        # The decorator should stop the action before the service ever sees it.
        # Delete these and role protection can quietly disappear.
        self.assertIn("Access denied. Requires role: admin.", output)
        library.add_book.assert_not_called()

    def test_my_current_borrows_prints_active_record_count(self):
        cli, _, library, _ = self.make_cli()
        cli.current_user = {"id": 4, "role": "user"}
        library.get_user_active_borrows.return_value = [
            {"book_id": 12, "borrowed_at": "2026-03-03T11:00:00"}
        ]

        output = self.capture_output(cli.my_current_borrows)

        # This proves the CLI can now render the active-borrow view instead of erroring out.
        # Delete these and that user flow loses coverage again.
        self.assertIn("Currently Borrowed Books (1/3 limit):", output)
        self.assertIn("Book ID: 12", output)


if __name__ == "__main__":
    unittest.main()
