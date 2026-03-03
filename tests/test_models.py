import unittest

from models.book import Book
from models.borrow_record import BorrowRecord
from models.person import Person
from models.review import Review
from models.user import User


class PersonModelTests(unittest.TestCase):
    def test_person_initializes_with_valid_name_and_email(self):
        person = Person("Ashanti", "ashanti@example.com")

        self.assertEqual(person.name, "Ashanti")
        self.assertEqual(person.email, "ashanti@example.com")

    def test_person_rejects_blank_name(self):
        with self.assertRaises(ValueError):
            Person("", "ashanti@example.com")

    def test_person_rejects_invalid_email(self):
        with self.assertRaises(ValueError):
            Person("Ashanti", "invalid-email")


class UserModelTests(unittest.TestCase):
    def test_user_inherits_from_person_and_verifies_password(self):
        user = User(1, "Ashanti", "ashanti@example.com", "secret123", "admin")

        self.assertIsInstance(user, Person)
        self.assertEqual(user.role, "admin")
        self.assertTrue(user.verify_password("secret123"))
        self.assertFalse(user.verify_password("wrong-password"))

    def test_user_rejects_invalid_role(self):
        with self.assertRaises(ValueError):
            User(1, "Ashanti", "ashanti@example.com", "secret123", "staff")


class BookModelTests(unittest.TestCase):
    def test_book_borrow_and_return_updates_available_copies(self):
        book = Book(1, "Clean Code", "Robert C. Martin", "9780132350884", 2)

        book.borrow_copy()
        self.assertEqual(book.available_copies, 1)

        book.return_copy()
        self.assertEqual(book.available_copies, 2)

    def test_book_rejects_invalid_available_copy_count(self):
        book = Book(1, "Clean Code", "Robert C. Martin", "9780132350884", 2)

        with self.assertRaises(ValueError):
            book.available_copies = -1

        with self.assertRaises(ValueError):
            book.available_copies = 3

    def test_book_cannot_borrow_when_no_copies_are_available(self):
        book = Book(1, "Clean Code", "Robert C. Martin", "9780132350884", 1)
        book.borrow_copy()

        with self.assertRaises(ValueError):
            book.borrow_copy()

    def test_book_cannot_return_past_total_copies(self):
        book = Book(1, "Clean Code", "Robert C. Martin", "9780132350884", 1)

        with self.assertRaises(ValueError):
            book.return_copy()


class BorrowRecordModelTests(unittest.TestCase):
    def test_borrow_record_defaults_to_borrowed_status(self):
        record = BorrowRecord(1, 2, 3)

        self.assertEqual(record.status, "borrowed")
        self.assertIsNotNone(record.borrowed_at)
        self.assertIsNone(record.returned_at)

    def test_borrow_record_marks_returned(self):
        record = BorrowRecord(1, 2, 3)

        record.mark_returned()

        self.assertEqual(record.status, "returned")
        self.assertIsNotNone(record.returned_at)

    def test_borrow_record_rejects_invalid_status(self):
        record = BorrowRecord(1, 2, 3)

        with self.assertRaises(ValueError):
            record.status = "lost"


class ReviewModelTests(unittest.TestCase):
    def test_review_trims_comment_and_stores_rating(self):
        review = Review(1, 2, 3, 5, "  Great book.  ")

        self.assertEqual(review.rating, 5)
        self.assertEqual(review.comment, "Great book.")
        self.assertIsNotNone(review.created_at)

    def test_review_rejects_non_integer_rating(self):
        with self.assertRaises(TypeError):
            Review(1, 2, 3, "5")

    def test_review_rejects_out_of_range_rating(self):
        with self.assertRaises(ValueError):
            Review(1, 2, 3, 0)

        with self.assertRaises(ValueError):
            Review(1, 2, 3, 6)

    def test_review_rejects_overlong_comment(self):
        with self.assertRaises(ValueError):
            Review(1, 2, 3, 4, "a" * 501)


if __name__ == "__main__":
    unittest.main()
