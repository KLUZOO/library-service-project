from datetime import datetime, timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from books.models import Book
from books.serializers import BookSerializer
from borrowings.models import Borrowing
from borrowings.serializers import BorrowingSerializer, BorrowingCreateViewSet

BOOK_URL = reverse("books:book-list")


def sample_book(self):
    self.book1 = Book.objects.create(
        title="Book 1",
        author="Author 1",
        cover="HARD",
        inventory=2,
        daily_fee=5.5,
    )
    self.book2 = Book.objects.create(
        title="Book 2",
        author="Author 2",
        cover="SOFT",
        inventory=3,
        daily_fee=5.5,
    )
    self.book3 = Book.objects.create(
        title="Book 3",
        author="Author 3",
        cover="SOFT",
        inventory=5,
        daily_fee=5.5,
    )


class UnauthenticatedBookApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_list_book(self):
        sample_book(self)
        res = self.client.get(BOOK_URL)
        books = Book.objects.order_by("id")
        serializer = BookSerializer(books, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_retrieve_book(self):
        sample_book(self)
        book_id = self.book1.id
        url = reverse("books:book-detail", args=[book_id])
        res = self.client.get(url)
        books = Book.objects.get(id=book_id)
        serializer = BookSerializer(books)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)


class AuthenticatedBookApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            "test@test.com",
            "testpass",
        )
        self.client.force_authenticate(self.user)

    def test_create_book(self):
        sample_book(self)
        payload = {
            "title": "Book test",
            "author": "Author test",
            "cover": "SOFT",
            "inventory": 5,
            "daily_fee": 5.5,
        }
        books_before = Book.objects.order_by("id")
        serializer_before = BookSerializer(books_before, many=True)
        res = self.client.post(BOOK_URL, payload)
        books_after = Book.objects.order_by("id")
        serializer_after = BookSerializer(books_after, many=True)

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(serializer_before.data, serializer_after.data)

    def test_update_book(self):
        sample_book(self)
        payload = {
            "title": "Book test",
            "author": "Author test",
            "cover": "SOFT",
            "inventory": 5,
            "daily_fee": 5.5,
        }
        book_id = self.book1.id
        url = reverse("books:book-detail", args=[book_id])
        books_before = Book.objects.order_by("id")
        serializer_before = BookSerializer(books_before, many=True)
        res = self.client.put(url, payload)
        books_after = Book.objects.order_by("id")
        serializer_after = BookSerializer(books_after, many=True)

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(serializer_before.data, serializer_after.data)


class AdminBorrowingApiTests(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.admin = get_user_model().objects.create_user(
            "admin@admin.com", "testpass", is_staff=True
        )
        self.client.force_authenticate(self.admin)

    def test_create_book(self):
        sample_book(self)
        payload = {
            "title": "Book test",
            "author": "Author test",
            "cover": "SOFT",
            "inventory": 5,
            "daily_fee": 5.5,
        }
        books_before_count = Book.objects.count()
        res = self.client.post(BOOK_URL, payload)
        books_after_count = Book.objects.count()

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(books_after_count, books_before_count + 1)

    def test_update_book(self):
        sample_book(self)  # створює self.book1
        payload = {
            "title": "Book test",
            "author": "Author test",
            "cover": "SOFT",
            "inventory": 5,
            "daily_fee": 5.5,
        }

        book_id = self.book1.id
        url = reverse("books:book-detail", args=[book_id])

        res = self.client.put(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)

        self.book1.refresh_from_db()

        self.assertEqual(self.book1.title, payload["title"])
        self.assertEqual(self.book1.author, payload["author"])
        self.assertEqual(self.book1.cover, payload["cover"])
        self.assertEqual(self.book1.inventory, payload["inventory"])
        self.assertEqual(float(self.book1.daily_fee), payload["daily_fee"])
