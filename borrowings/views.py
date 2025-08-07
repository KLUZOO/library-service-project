from django.db import transaction
from django.shortcuts import render
from rest_framework import generics, viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly

from borrowings.models import Borrowing
from borrowings.serializers import BorrowingSerializer, BorrowingCreateViewSet


class BorrowingsViewSet(viewsets.ModelViewSet):
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
