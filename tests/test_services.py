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


class ReviewServiceTests(ServiceTestCase):
    def test_add_review_and_compute_average_rating(self):
        service = ReviewService()
        service.add_review(1, 10, 5, " Excellent ")
        service.add_review(2, 10, 3, "Solid")

        reviews = service.get_book_reviews(10)
        average = service.get_book_rating(10)

        self.assertEqual(len(reviews), 2)
        self.assertEqual(reviews[0]["comment"], "Excellent")
        self.assertEqual(average, 4.0)

    def test_adding_second_review_for_same_user_updates_existing_review(self):
        service = ReviewService()
        first = service.add_review(1, 10, 4, "Good")
        second = service.add_review(1, 10, 5, "Great")

        reviews = service.get_book_reviews(10)

        self.assertEqual(first["id"], second["id"])
        self.assertEqual(len(reviews), 1)
        self.assertEqual(reviews[0]["rating"], 5)
        self.assertEqual(reviews[0]["comment"], "Great")


if __name__ == "__main__":
    unittest.main()
