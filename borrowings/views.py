from django.db import transaction
from django.shortcuts import render
from django.utils import timezone
from rest_framework import generics, viewsets, status, mixins
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from books.models import Book
from borrowings.models import Borrowing
from borrowings.serializers import BorrowingSerializer, BorrowingCreateViewSet


class BorrowingsViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    GenericViewSet,
):
    queryset = Borrowing.objects.all()
    serializer_class = BorrowingSerializer
    permission_classes = (IsAuthenticatedOrReadOnly,)

    def get_serializer_class(self):
        if self.action == "list":
            return BorrowingSerializer
        return BorrowingCreateViewSet

    def perform_create(self, serializer):
        with transaction.atomic():
            book = serializer.validated_data["book"]
            if book.inventory < 1:
                raise ValidationError("This book is currently not available.")

            book.inventory -= 1
            book.save()

            serializer.save(user=self.request.user)

    @action(
        detail=True,
        methods=["post"],
        permission_classes=[IsAuthenticated],
        url_path="return",
    )
    def return_act(self, request, pk=None):
        with transaction.atomic():
            borrowing = self.get_object()

            if request.user != borrowing.user:
                raise ValidationError("You do not have access to this loan.")

            if borrowing.actual_return_date:
                raise ValidationError("This book has already been returned.")

            borrowing.actual_return_date = timezone.now()
            borrowing.save()

            book = borrowing.book
            book.inventory += 1
            book.save()

            serializer = BorrowingSerializer(borrowing)
            return Response(
                {"message": "Book returned successfully.", "data": serializer.data},
                status=status.HTTP_200_OK,
            )
