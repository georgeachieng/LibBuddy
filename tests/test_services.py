import tempfile
import unittest
from io import StringIO
from unittest.mock import patch

# Patch the storage module directly so service tests never touch real app data.
# Delete that strategy and tests start mutating repo JSON files. Absolutely not.
import storage.json_store as json_store_module
from services.auth_service import AuthService
from services.library_service import LibraryService
from services.review_service import ReviewService


# This base case isolates every test inside a temp data directory.
# Delete it and service tests become stateful, flaky, and rude to local data.
class ServiceTestCase(unittest.TestCase):
    def setUp(self):
        # Temp dir keeps file-backed tests disposable.
        # Delete it and test runs start leaking files into the repo.
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)

        # Patch DATA_DIR so every JSONStore instance writes to temp space.
        # Delete this and tests hit the real data folder. That would suck.
        self.data_dir_patcher = patch.object(json_store_module, "DATA_DIR", self.temp_dir.name)
        self.data_dir_patcher.start()
        self.addCleanup(self.data_dir_patcher.stop)


class AuthServiceTests(ServiceTestCase):
    def test_first_registered_user_becomes_admin_and_can_login(self):
        service = AuthService()

        created_user = service.register("Ashanti", "ashanti@example.com", "secret123")
        logged_in_user = service.login("ashanti@example.com", "secret123")

        # First-user admin logic is easy to break in refactors, so it stays tested.
        # Delete these and auth role/session regressions get sneaky.
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

        # Username login is part of the smoother CLI flow now, so it stays tested.
        # Delete this and that nicer auth path can break quietly.
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

        # Admin creation is a real feature now, so role and identity need to stay locked in.
        # Delete this and privilege-management regressions get sneaky.
        self.assertEqual(created_admin["role"], "admin")
        self.assertEqual(created_admin["username"], "joyburgei")


class LibraryServiceTests(ServiceTestCase):
    def test_add_and_search_books(self):
        service = LibraryService()
        created_book = service.add_book("Clean Code", "Robert C. Martin", "9780132350884", 3)

        results = service.search_books("clean")

        # These asserts prove writes, reads, and filtering all still line up.
        # Delete them and search can regress without getting noticed.
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

        # This checks both side effects: stock and history.
        # Delete it and one half of the borrow flow can break silently.
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

        # The first three borrows should work because they are inside the policy limit.
        # Delete these and the test stops proving the happy path.
        for book in books[:3]:
            self.assertTrue(service.borrow_book(user_id=7, book_id=book["id"]))

        # Borrow number four should fail because the service now enforces the stated limit.
        # Delete this and that project rule can regress quietly.
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

        # Only the unreturned checkout should still count toward the borrow limit.
        # Delete these and active-borrow filtering can drift without a warning.
        self.assertEqual(len(active_records), 1)
        self.assertEqual(active_records[0]["book_id"], second_book["id"])

    def test_fetch_books_from_open_library_normalizes_results(self):
        service = LibraryService()
        fake_payload = StringIO(
            '{"docs":[{"title":"Clean Architecture","author_name":["Robert C. Martin"],'
            '"isbn":["9780134494166"],"first_publish_year":2017}]}'
        )

        # Mocking the network keeps this test fast and not weirdly dependent on Wi-Fi drama.
        # Delete it and the suite starts failing over stuff outside the repo.
        with patch("services.library_service.urlopen") as mock_urlopen:
            mock_urlopen.return_value.__enter__.return_value = fake_payload
            results = service.fetch_books_from_open_library("clean architecture", limit=3)

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["title"], "Clean Architecture")
        self.assertEqual(results[0]["author"], "Robert C. Martin")
        self.assertEqual(results[0]["isbn"], "9780134494166")

    def test_fetch_books_from_open_library_rejects_one_character_query(self):
        service = LibraryService()

        # This blocks junk searches before the API gets a chance to complain.
        # Delete it and the user is back to avoidable 422 nonsense.
        with self.assertRaises(ValueError):
            service.fetch_books_from_open_library("a", limit=3)

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

        # One duplicate and one clean import is the exact edge case this feature can mess up.
        # Delete these and duplicate detection can rot quietly.
        self.assertEqual(len(summary["imported"]), 1)
        self.assertEqual(len(summary["skipped"]), 1)
        self.assertEqual(summary["imported"][0]["title"], "Domain-Driven Design")


class ReviewServiceTests(ServiceTestCase):
    def test_add_review_rejects_user_who_never_borrowed_the_book(self):
        service = ReviewService()

        # Review access is tied to real borrow history now.
        # Delete this and the proposal rule stops being enforced.
        with self.assertRaises(PermissionError):
            service.add_review(1, 10, 5, "Looks cool, I guess")

    def test_add_review_after_borrow_succeeds(self):
        library_service = LibraryService()
        review_service = ReviewService()
        book = library_service.add_book("Clean Code", "Robert C. Martin", "9780132350884", 1)

        library_service.borrow_book(user_id=1, book_id=book["id"])
        review = review_service.add_review(1, book["id"], 5, " Excellent ")

        # Borrow history should unlock review creation for that same user/book pair.
        # Delete these and the happy path is no longer covered.
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

        # This proves comment trimming and average math both still hold.
        # Delete these and review summaries get less trustworthy.
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

        # Admin review screens depend on this staying newest-first.
        # Delete it and the moderation view gets noisy and less useful.
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

        # This blocks duplicate-review inflation from the same user.
        # Delete these and that regression can sneak back in.
        self.assertEqual(first["id"], second["id"])
        self.assertEqual(len(reviews), 1)
        self.assertEqual(reviews[0]["rating"], 5)
        self.assertEqual(reviews[0]["comment"], "Great")


if __name__ == "__main__":
    unittest.main()
