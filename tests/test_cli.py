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
        self.assertIn("2/2", output)

    def test_list_available_books_filters_out_unavailable_titles(self):
        cli, _, library, _ = self.make_cli()
        library.list_books.return_value = [
            {
                "id": 1,
                "title": "Clean Code",
                "author": "Robert C. Martin",
                "isbn": "9780132350884",
                "available_copies": 2,
                "total_copies": 2,
            },
            {
                "id": 2,
                "title": "Gone Book",
                "author": "Some Author",
                "isbn": "1111111111",
                "available_copies": 0,
                "total_copies": 2,
            },
        ]

        output = self.capture_output(cli.list_available_books)

        self.assertIn("Available Books:", output)
        self.assertIn("Clean Code", output)
        self.assertNotIn("Gone Book", output)

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

    def test_import_books_from_api_calls_service_with_selected_results(self):
        cli, _, library, _ = self.make_cli()
        cli.current_user = {"id": 1, "role": "admin"}
        library.fetch_books_from_open_library.return_value = [
            {
                "result_id": 1,
                "title": "Clean Architecture",
                "author": "Robert C. Martin",
                "isbn": "9780134494166",
                "first_publish_year": 2017,
            },
            {
                "result_id": 2,
                "title": "Domain-Driven Design",
                "author": "Eric Evans",
                "isbn": "9780321125217",
                "first_publish_year": 2003,
            },
        ]
        library.import_books.return_value = {"imported": [{"title": "Clean Architecture"}], "skipped": []}

        output = self.capture_output(
            cli.import_books_from_api,
            inputs=["clean", "2", "1", "3"],
        )

        self.assertIn("Open Library Results:", output)
        self.assertIn("Imported 1 book(s).", output)
        library.fetch_books_from_open_library.assert_called_once_with("clean", 2)
        library.import_books.assert_called_once()

    def test_import_books_from_api_rejects_too_short_query_before_service_call(self):
        cli, _, library, _ = self.make_cli()
        cli.current_user = {"id": 1, "role": "admin"}

        output = self.capture_output(
            cli.import_books_from_api,
            inputs=["a"],
        )

        self.assertIn("Use at least 2 characters.", output)
        library.fetch_books_from_open_library.assert_not_called()

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

    def test_borrow_book_allows_back_without_calling_service(self):
        cli, _, library, _ = self.make_cli()
        cli.current_user = {"id": 4, "role": "user"}

        output = self.capture_output(
            cli.borrow_book,
            inputs=["back"],
        )

        self.assertIn("Borrow cancelled.", output)
        library.borrow_book.assert_not_called()

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

    def test_view_book_details_prints_inventory_and_rating_summary(self):
        cli, _, library, review = self.make_cli()
        library.get_book.return_value = {
            "id": 3,
            "title": "Design Patterns",
            "author": "GoF",
            "isbn": "9780201633610",
            "available_copies": 2,
            "total_copies": 4,
        }
        review.get_book_average_rating.return_value = 4.5
        review.get_book_reviews.return_value = [{"id": 9}, {"id": 10}]

        output = self.capture_output(
            cli.view_book_details,
            inputs=["3"],
        )

        self.assertIn("=== Book Details ===", output)
        self.assertIn("Design Patterns", output)
        self.assertIn("Stock: 2/4", output)
        self.assertIn("Average rating: 4.5/5", output)

    def test_view_review_details_prints_full_review(self):
        cli, auth, _, review = self.make_cli()
        review.get_review.return_value = {
            "id": 11,
            "book_id": 3,
            "user_id": 5,
            "rating": 4,
            "comment": "Very solid read",
            "created_at": "2026-03-03T11:00:00",
        }
        auth.get_user_by_id.return_value = {"id": 5, "username": "joyburgei"}
        cli.library_service.get_book.return_value = {"id": 3, "title": "Design Patterns"}

        output = self.capture_output(
            cli.view_review_details,
            inputs=["11"],
        )

        self.assertIn("=== Review Details ===", output)
        self.assertIn("Review ID: 11", output)
        self.assertIn("Rating: 4/5", output)
        self.assertIn("Very solid read", output)


if __name__ == "__main__":
    unittest.main()
