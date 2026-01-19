"""Book loan model - связывает книги и пользователей."""

from datetime import datetime

from piccolo.columns import UUID, ForeignKey, Timestamptz, Boolean

from src.Ship.Parents import Model


class BookLoan(Model):
    """Book loan model - представляет выдачу книги пользователю."""

    id = UUID(primary_key=True)
    book_id = ForeignKey("Book", required=True)
    user_id = ForeignKey("User", required=True) 
    loaned_at = Timestamptz(default=datetime.utcnow)
    due_date = Timestamptz(required=True)
    returned_at = Timestamptz(null=True)
    is_returned = Boolean(default=False)
    created_at = Timestamptz()
    updated_at = Timestamptz()
