import tempfile
import unittest
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
