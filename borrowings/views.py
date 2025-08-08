from django.db import transaction
from django.utils import timezone
from rest_framework import status, mixins
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from borrowings.models import Borrowing
from borrowings.serializers import BorrowingSerializer, BorrowingCreateViewSet
from notifications.services import send_telegram_message

from notifications.tasks import notify_new_borrowing, notify_book_return


class BorrowingsViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    GenericViewSet,
):
    queryset = Borrowing.objects.select_related("book", "user")
    serializer_class = BorrowingSerializer
    permission_classes = (IsAuthenticated,)

    def get_serializer_class(self):
        if self.action in ("list", "retrieve"):
            return BorrowingSerializer
        return BorrowingCreateViewSet

    def perform_create(self, serializer):
        with transaction.atomic():
            book = serializer.validated_data["book"]
            if book.inventory < 1:
                raise ValidationError("This book is currently not available.")

            book.inventory -= 1
            book.save()

            borrowing = serializer.save(user=self.request.user)
            message = (
                f"📚 <b>New Borrowing</b>\n"
                f"👤 User: {borrowing.user.email}\n"
                f"📖 Book: {borrowing.book.title}\n"
                f"📅 Borrowed: {borrowing.borrow_date}\n"
                f"📆 Expected return: {borrowing.expected_return_date}"
            )
            notify_new_borrowing.delay(message)

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

            notify_book_return.delay(borrowing.id)

            serializer = BorrowingSerializer(borrowing)
            return Response(
                {"message": "Book returned successfully.", "data": serializer.data},
                status=status.HTTP_200_OK,
            )

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
