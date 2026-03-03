import tempfile
import unittest
from io import StringIO
from unittest.mock import patch

import storage.json_store as json_store_module
from services.auth_service import AuthService
from services.library_service import LibraryService
from services.review_service import ReviewService


class ServiceTestCase(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)

        self.data_dir_patcher = patch.object(json_store_module, "DATA_DIR", self.temp_dir.name)
        self.data_dir_patcher.start()
        self.addCleanup(self.data_dir_patcher.stop)


class AuthServiceTests(ServiceTestCase):
    def test_first_registered_user_becomes_admin_and_can_login(self):
        service = AuthService()

        created_user = service.register("Ashanti", "ashanti@example.com", "secret123")
        logged_in_user = service.login("ashanti@example.com", "secret123")

        self.assertEqual(created_user["role"], "admin")
        self.assertEqual(logged_in_user["email"], "ashanti@example.com")
        self.assertEqual(service.get_current_user()["id"], created_user["id"])

    def test_register_rejects_duplicate_email(self):
        service = AuthService()
        service.register("Ashanti", "ashanti@example.com", "secret123")

        with self.assertRaises(ValueError):
            service.register("Another", "ashanti@example.com", "different123")

    def test_login_accepts_username_as_identifier(self):
        service = AuthService()
        created_user = service.register(
            "Ashanti",
            "ashanti@example.com",
            "secret123",
            username="ashanti",
        )

        logged_in_user = service.login("ashanti", "secret123")

        self.assertEqual(logged_in_user["id"], created_user["id"])
        self.assertEqual(logged_in_user["username"], "ashanti")

    def test_admin_can_create_another_admin_account(self):
        service = AuthService()
        first_admin = service.register(
            "Ashanti",
            "ashanti@example.com",
            "secret123",
            username="ashanti",
        )
        service.current_user = first_admin

        created_admin = service.register(
            "Joy Burgei",
            "joy@example.com",
            "secret123",
            username="joyburgei",
            role="admin",
        )

        self.assertEqual(created_admin["role"], "admin")
        self.assertEqual(created_admin["username"], "joyburgei")


class LibraryServiceTests(ServiceTestCase):
    def test_add_and_search_books(self):
        service = LibraryService()
        created_book = service.add_book("Clean Code", "Robert C. Martin", "9780132350884", 3)

        results = service.search_books("clean")

        self.assertEqual(created_book["available_copies"], 3)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["title"], "Clean Code")

    def test_borrow_and_return_book_updates_inventory_and_records(self):
        service = LibraryService()
        book = service.add_book("Clean Code", "Robert C. Martin", "9780132350884", 2)

        borrowed = service.borrow_book(user_id=7, book_id=book["id"])
        returned = service.return_book(user_id=7, book_id=book["id"])
        updated_book = service.get_book(book["id"])
        records = service.view_all_borrow_records()

        self.assertTrue(borrowed)
        self.assertTrue(returned)
        self.assertEqual(updated_book["available_copies"], 2)
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["status"], "returned")

    def test_borrow_limit_blocks_fourth_active_checkout(self):
        service = LibraryService()
        books = [
            service.add_book(f"Book {index}", "Author", f"isbn-{index}", 1)
            for index in range(1, 5)
        ]

        for book in books[:3]:
            self.assertTrue(service.borrow_book(user_id=7, book_id=book["id"]))

        with self.assertRaises(ValueError):
            service.borrow_book(user_id=7, book_id=books[3]["id"])

    def test_get_user_active_borrows_only_returns_unreturned_records(self):
        service = LibraryService()
        first_book = service.add_book("Clean Code", "Robert C. Martin", "9780132350884", 2)
        second_book = service.add_book("Refactoring", "Martin Fowler", "9780201485677", 1)

        service.borrow_book(user_id=7, book_id=first_book["id"])
        service.borrow_book(user_id=7, book_id=second_book["id"])
        service.return_book(user_id=7, book_id=first_book["id"])

        active_records = service.get_user_active_borrows(user_id=7)

        self.assertEqual(len(active_records), 1)
        self.assertEqual(active_records[0]["book_id"], second_book["id"])

    def test_fetch_books_from_open_library_normalizes_results(self):
        service = LibraryService()
        fake_payload = StringIO(
            '{"docs":[{"title":"Clean Architecture","author_name":["Robert C. Martin"],'
            '"isbn":["9780134494166"],"first_publish_year":2017}]}'
        )

        with patch("services.library_service.urlopen") as mock_urlopen:
            mock_urlopen.return_value.__enter__.return_value = fake_payload
            results = service.fetch_books_from_open_library("clean architecture", limit=3)

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["title"], "Clean Architecture")
        self.assertEqual(results[0]["author"], "Robert C. Martin")
        self.assertEqual(results[0]["isbn"], "9780134494166")

    def test_import_books_skips_duplicates_and_saves_new_books(self):
        service = LibraryService()
        service.add_book("Clean Code", "Robert C. Martin", "9780132350884", 2)

        summary = service.import_books(
            [
                {"title": "Clean Code", "author": "Robert C. Martin", "isbn": "9780132350884"},
                {"title": "Domain-Driven Design", "author": "Eric Evans", "isbn": "9780321125217"},
            ],
            total_copies=3,
        )

        self.assertEqual(len(summary["imported"]), 1)
        self.assertEqual(len(summary["skipped"]), 1)
        self.assertEqual(summary["imported"][0]["title"], "Domain-Driven Design")


class ReviewServiceTests(ServiceTestCase):
    def test_add_review_rejects_user_who_never_borrowed_the_book(self):
        service = ReviewService()

        with self.assertRaises(PermissionError):
            service.add_review(1, 10, 5, "Looks cool, I guess")

    def test_add_review_after_borrow_succeeds(self):
        library_service = LibraryService()
        review_service = ReviewService()
        book = library_service.add_book("Clean Code", "Robert C. Martin", "9780132350884", 1)

        library_service.borrow_book(user_id=1, book_id=book["id"])
        review = review_service.add_review(1, book["id"], 5, " Excellent ")

        self.assertEqual(review["book_id"], book["id"])
        self.assertEqual(review["comment"], "Excellent")

    def test_add_review_and_compute_average_rating(self):
        library_service = LibraryService()
        service = ReviewService()
        book = library_service.add_book("Clean Code", "Robert C. Martin", "9780132350884", 2)
        library_service.borrow_book(user_id=1, book_id=book["id"])
        library_service.borrow_book(user_id=2, book_id=book["id"])
        service.add_review(1, book["id"], 5, " Excellent ")
        service.add_review(2, book["id"], 3, "Solid")

        reviews = service.get_book_reviews(book["id"])
        average = service.get_book_rating(book["id"])

        self.assertEqual(len(reviews), 2)
        self.assertEqual(reviews[0]["comment"], "Excellent")
        self.assertEqual(average, 4.0)

    def test_list_recent_reviews_returns_latest_first(self):
        library_service = LibraryService()
        service = ReviewService()
        first_book = library_service.add_book("Clean Code", "Robert C. Martin", "9780132350884", 1)
        second_book = library_service.add_book("Refactoring", "Martin Fowler", "9780201485677", 1)
        library_service.borrow_book(user_id=1, book_id=first_book["id"])
        library_service.borrow_book(user_id=2, book_id=second_book["id"])
        service.add_review(1, first_book["id"], 4, "First")
        service.add_review(2, second_book["id"], 5, "Second")

        recent = service.list_recent_reviews()

        self.assertEqual(recent[0]["comment"], "Second")
        self.assertEqual(recent[1]["comment"], "First")

    def test_adding_second_review_for_same_user_updates_existing_review(self):
        library_service = LibraryService()
        service = ReviewService()
        book = library_service.add_book("Clean Code", "Robert C. Martin", "9780132350884", 1)
        library_service.borrow_book(user_id=1, book_id=book["id"])
        first = service.add_review(1, book["id"], 4, "Good")
        second = service.add_review(1, book["id"], 5, "Great")

        reviews = service.get_book_reviews(book["id"])

        self.assertEqual(first["id"], second["id"])
        self.assertEqual(len(reviews), 1)
        self.assertEqual(reviews[0]["rating"], 5)
        self.assertEqual(reviews[0]["comment"], "Great")


if __name__ == "__main__":
    unittest.main()
