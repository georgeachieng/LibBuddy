import io
import unittest
from contextlib import redirect_stdout
from unittest.mock import Mock, patch

import main as cli_module


class CLITests(unittest.TestCase):
    def make_cli(self, auth=None, library=None, review=None):
        auth = auth or Mock()
        library = library or Mock()
        review = review or Mock()

        with patch.object(
            cli_module.LibBuddyCLI,
            "_load_service",
            side_effect=[auth, library, review],
        ):
            cli = cli_module.LibBuddyCLI()

        return cli, auth, library, review

    def capture_output(self, fn, inputs=None):
        buffer = io.StringIO()
        inputs = inputs or []

        with patch("builtins.input", side_effect=inputs), redirect_stdout(buffer):
            fn()

        return buffer.getvalue()

    def test_register_requires_all_fields(self):
        cli, auth, _, _ = self.make_cli()

        output = self.capture_output(
            cli.register,
            inputs=["", "ashanti@example.com", "secret123"],
        )

        self.assertIn("All fields are required.", output)
        auth.register.assert_not_called()

    def test_login_sets_current_user_on_success(self):
        cli, auth, _, _ = self.make_cli()
        auth.login.return_value = {"id": 1, "email": "ashanti@example.com", "role": "user"}

        output = self.capture_output(
            cli.login,
            inputs=["ashanti@example.com", "secret123"],
        )

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

        self.assertIn("Rating must be between 1 and 5.", output)
        review.add_review.assert_not_called()


if __name__ == "__main__":
    unittest.main()
