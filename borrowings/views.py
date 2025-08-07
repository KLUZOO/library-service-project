from django.shortcuts import render
from rest_framework import generics, viewsets, mixins
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import GenericViewSet

from borrowings.models import Borrowing
from borrowings.serializers import BorrowingSerializer


class BorrowingsViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    GenericViewSet,
):
    queryset = Borrowing.objects.select_related("book", "user")
    serializer_class = BorrowingSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        request = self.request
        queryset = self.queryset
        user = request.user
        is_active = request.query_params.get("is_active")

        if is_active == "true":
            queryset = queryset.filter(actual_return_date__isnull=True)
        elif is_active == "false":
            queryset = queryset.exclude(actual_return_date__isnull=True)

        if user.is_staff:
            user_id = request.query_params.get("user_id")
            if user_id:
                try:
                    ids_list = [int(uid) for uid in user_id.split(",")]
                    queryset = queryset.filter(user_id__in=ids_list)
                except ValueError:
                    raise ValidationError(
                        "user_id must be a comma-separated list of integers."
                    )
            return queryset

        return queryset.filter(user=user)
