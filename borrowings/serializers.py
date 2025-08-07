from rest_framework import serializers, viewsets

from books.models import Book
from books.serializers import BookSerializer
from borrowings.models import Borrowing
from users.models import User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "email")


class BorrowingSerializer(serializers.ModelSerializer):
    book = BookSerializer(read_only=True, many=False)
    user = UserSerializer(read_only=True, many=False)

    class Meta:
        model = Borrowing
        fields = (
            "id",
            "borrow_date",
            "expected_return_date",
            "actual_return_date",
            "book",
            "user",
        )


class BorrowingCreateViewSet(serializers.ModelSerializer):
    class Meta:
        model = Borrowing
        fields = (
            "id",
            "borrow_date",
            "expected_return_date",
            "book",
        )
