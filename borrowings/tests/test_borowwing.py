from datetime import datetime, timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from books.models import Book
from borrowings.models import Borrowing
from borrowings.serializers import BorrowingSerializer, BorrowingCreateViewSet

BORROWING_URL = reverse("borrowings:borrowing-list")


def sample_borrowing(self):
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
    self.borrowing1 = Borrowing.objects.create(
        expected_return_date=timezone.now().date() + timedelta(days=1),
        book=self.book1,
        user=self.user,
    )
    self.borrowing2 = Borrowing.objects.create(
        expected_return_date=timezone.now().date() + timedelta(days=2),
        book=self.book2,
        user=self.admin,
    )
    self.borrowing3 = Borrowing.objects.create(
        expected_return_date=timezone.now().date() + timedelta(days=2),
        actual_return_date=timezone.now().date() + timedelta(days=1),
        book=self.book2,
        user=self.user,
    )


class UnauthenticatedBorrowingApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        res = self.client.get(BORROWING_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthenticatedBorrowingApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            "test@test.com",
            "testpass",
        )
        self.admin = get_user_model().objects.create_user(
            "admin@admin.com", "testpass", is_staff=True
        )
        self.client.force_authenticate(self.user)

    def test_list_borrowing(self):
        sample_borrowing(self)
        res = self.client.get(BORROWING_URL)
        borrowings = Borrowing.objects.order_by("id").filter(user=self.user)
        serializer = BorrowingSerializer(borrowings, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(serializer.data, res.data)

    def test_retrieve_borrowing(self):
        sample_borrowing(self)
        borrowing_id = self.borrowing1.id
        res = self.client.get(
            reverse("borrowings:borrowing-detail", args=[borrowing_id])
        )
        borrowing = Borrowing.objects.get(id=borrowing_id)
        serializer = BorrowingSerializer(borrowing)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(serializer.data, res.data)

    def test_filter_by_is_active(self):
        sample_borrowing(self)
        res = self.client.get(BORROWING_URL, {"is_active": "true"})
        borrowings = Borrowing.objects.order_by("id").filter(
            user=self.user, actual_return_date__isnull=True
        )
        serializer = BorrowingSerializer(borrowings, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(serializer.data, res.data)

    def test_return_borrowing(self):
        sample_borrowing(self)
        borrowing_id = self.borrowing1.id
        url = reverse("borrowings:borrowing-return-act", kwargs={"pk": borrowing_id})
        res = self.client.post(url)
        borrowing = Borrowing.objects.get(id=borrowing_id)
        serializer = BorrowingSerializer(borrowing)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(serializer.data, res.data["data"])
        self.assertEqual("Book returned successfully.", res.data["message"])

    def test_create_new_borrowing(self):
        sample_borrowing(self)
        payload = {
            "expected_return_date": timezone.now().date() + timedelta(days=2),
            "book": self.book1.id,
        }
        res = self.client.post(BORROWING_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        borrowing = Borrowing.objects.order_by("id").filter(user=self.user)
        serializer = BorrowingCreateViewSet(borrowing, many=True)

        self.assertIn(res.data, serializer.data)


class AdminBorrowingApiTests(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            "test@test.com",
            "testpass",
        )
        self.admin = get_user_model().objects.create_user(
            "admin@admin.com", "testpass", is_staff=True
        )
        self.client.force_authenticate(self.admin)

    def test_list_borrowing(self):
        sample_borrowing(self)
        res = self.client.get(BORROWING_URL)
        borrowings = Borrowing.objects.order_by("id")
        serializer = BorrowingSerializer(borrowings, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(serializer.data, res.data)

    def test_retrieve_borrowing(self):
        sample_borrowing(self)
        borrowing_id = self.borrowing2.id
        res = self.client.get(
            reverse("borrowings:borrowing-detail", args=[borrowing_id])
        )
        borrowing = Borrowing.objects.get(id=borrowing_id)
        serializer = BorrowingSerializer(borrowing)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(serializer.data, res.data)

    def test_filter_by_is_active(self):
        sample_borrowing(self)
        res = self.client.get(BORROWING_URL, {"is_active": "true"})
        borrowings = Borrowing.objects.order_by("id").filter(
            actual_return_date__isnull=True
        )
        serializer = BorrowingSerializer(borrowings, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(serializer.data, res.data)

    def test_filter_by_user_id(self):
        sample_borrowing(self)
        res = self.client.get(BORROWING_URL, {"user_id": "2,3"})
        borrowings = Borrowing.objects.order_by("id").filter(user_id__in=[2, 3])
        serializer = BorrowingSerializer(borrowings, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(serializer.data, res.data)

    def test_return_borrowing(self):
        sample_borrowing(self)
        borrowing_id = self.borrowing2.id
        url = reverse("borrowings:borrowing-return-act", kwargs={"pk": borrowing_id})
        res = self.client.post(url)
        borrowing = Borrowing.objects.get(id=borrowing_id)
        serializer = BorrowingSerializer(borrowing)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(serializer.data, res.data["data"])
        self.assertEqual("Book returned successfully.", res.data["message"])

    def test_create_new_borrowing(self):
        sample_borrowing(self)
        payload = {
            "expected_return_date": timezone.now().date() + timedelta(days=2),
            "book": self.book1.id,
        }
        res = self.client.post(BORROWING_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        borrowing = Borrowing.objects.order_by("id")
        serializer = BorrowingCreateViewSet(borrowing, many=True)

        self.assertIn(res.data, serializer.data)
