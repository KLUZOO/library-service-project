from celery import shared_task
from django.utils import timezone

from borrowings.models import Borrowing
from .services import send_telegram_message


@shared_task
def notify_new_borrowing(message: str):
    send_telegram_message(message)


@shared_task
def check_overdue_borrowings():
    today = timezone.now().date()

    overdue_borrowings = Borrowing.objects.filter(
        expected_return_date__lt=today, actual_return_date__isnull=True
    )

    if not overdue_borrowings.exists():
        return "No overdue borrowings found."

    for borrowing in overdue_borrowings:
        message = (
            f"❗ Просрочена позика книги\n"
            f"Книга: {borrowing.book.title}\n"
            f"Користувач: {borrowing.user.email}\n"
            f"Дата позики: {borrowing.borrow_date}\n"
            f"Очікувана дата повернення: {borrowing.expected_return_date}"
        )
        send_telegram_message(message)

    return f"Notified about {overdue_borrowings.count()} overdue borrowings."


@shared_task
def notify_book_return(borrowing_id):
    from borrowings.models import Borrowing

    borrowing = Borrowing.objects.get(id=borrowing_id)

    message = (
        f"✅ Книгу повернуто\n"
        f"Книга: {borrowing.book.title}\n"
        f"Користувач: {borrowing.user.email}\n"
        f"Дата позики: {borrowing.borrow_date}\n"
        f"Дата повернення: {borrowing.actual_return_date}"
    )

    send_telegram_message(message)
    return f"Return notification sent for borrowing {borrowing_id}"
