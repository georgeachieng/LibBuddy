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
            inputs=["", "ashanti", "ashanti@example.com", "secret123"],
        )

        self.assertIn("Please fill in every field.", output)
        auth.register.assert_not_called()

    def test_login_sets_current_user_on_success(self):
        cli, auth, _, _ = self.make_cli()
        auth.login.return_value = {
            "id": 1,
            "email": "ashanti@example.com",
            "username": "ashanti",
            "role": "user",
        }

        output = self.capture_output(
            cli.login,
            inputs=["ashanti", "secret123"],
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
        self.assertIn("Clean Code", output)
        self.assertIn("Robert C. Martin", output)
        self.assertIn("Available: 2", output)

    def test_add_review_rejects_rating_above_five_before_calling_service(self):
        cli, _, library, review = self.make_cli()
        cli.current_user = {"id": 4, "role": "user"}
        library.my_borrow_history.return_value = [{"book_id": 12}]
        library.get_book.return_value = {"id": 12, "title": "Refactoring"}

        output = self.capture_output(
            cli.add_review,
            inputs=["12", "6"],
        )

        self.assertIn("Rating must be between 1 and 5.", output)
        review.add_review.assert_not_called()

    def test_add_book_blocks_non_admin_user_before_prompting(self):
        cli, _, library, _ = self.make_cli()
        cli.current_user = {"id": 4, "role": "user"}

        output = self.capture_output(cli.add_book)

        self.assertIn("Access denied. Requires role: admin.", output)
        library.add_book.assert_not_called()

    def test_create_admin_calls_auth_service_with_admin_role(self):
        cli, auth, _, _ = self.make_cli()
        cli.current_user = {"id": 1, "role": "admin"}
        auth.register.return_value = {"id": 6, "username": "joyburgei", "role": "admin"}

        output = self.capture_output(
            cli.create_admin,
            inputs=["Joy Burgei", "joyburgei", "joy@example.com", "secret123"],
        )

        self.assertIn("Admin account created for joyburgei.", output)
        auth.register.assert_called_once_with(
            name="Joy Burgei",
            email="joy@example.com",
            password="secret123",
            role="admin",
            username="joyburgei",
        )

    def test_my_current_borrows_prints_active_record_count(self):
        cli, _, library, _ = self.make_cli()
        cli.current_user = {"id": 4, "role": "user"}
        library.get_book.return_value = {"id": 12, "title": "Refactoring"}
        library.get_user_active_borrows.return_value = [
            {"book_id": 12, "borrowed_at": "2026-03-03T11:00:00"}
        ]

        output = self.capture_output(cli.my_current_borrows)

        self.assertIn("Currently Borrowed Books (1/3 limit):", output)
        self.assertIn("Refactoring", output)

    def test_add_review_requires_book_from_borrow_history(self):
        cli, _, library, review = self.make_cli()
        cli.current_user = {"id": 4, "role": "user"}
        library.my_borrow_history.return_value = [{"book_id": 3}]
        library.get_book.return_value = {"id": 3, "title": "Design Patterns"}

        output = self.capture_output(
            cli.add_review,
            inputs=["9"],
        )

        self.assertIn("Your reviewable books:", output)
        self.assertIn("Choose a book from your borrowing history.", output)
        review.add_review.assert_not_called()


if __name__ == "__main__":
    unittest.main()
