from django.conf import settings
from django.utils.translation import gettext as _
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from books.models import Book


class Borrowing(models.Model):
    borrow_date = models.DateField(auto_now_add=True)
    expected_return_date = models.DateField()
    actual_return_date = models.DateField(
        null=True,
        blank=True,
    )
    book = models.ForeignKey(
        Book,
        on_delete=models.CASCADE,
        related_name="borrowings",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="borrowings",
    )

    def __str__(self):
        return f"Borrowed {self.book.title} by {self.user.email} on {self.borrow_date}"

    def clean(self):
        borrow_date = self.borrow_date or timezone.now().date()
        if self.expected_return_date <= borrow_date:
            raise ValidationError(
                {
                    "expected_return_date": _(
                        "Expected return date must be after borrow date."
                    )
                }
            )

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)
