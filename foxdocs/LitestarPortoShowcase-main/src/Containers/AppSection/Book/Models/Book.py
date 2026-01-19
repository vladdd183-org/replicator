"""Book model."""

from datetime import datetime

from piccolo.columns import UUID, Boolean, Text, Timestamptz, Varchar

from src.Ship.Parents import Model


class Book(Model):
    """Book model."""

    id = UUID(primary_key=True)
    title = Varchar(length=255, required=True)
    author = Varchar(length=255, required=True)
    isbn = Varchar(length=13, unique=True, required=True)
    description = Text(default="")
    is_available = Boolean(default=True)
    created_at = Timestamptz()
    updated_at = Timestamptz()

    @classmethod
    def get_readable(cls) -> Varchar:
        """Get readable representation."""
        return cls.title
