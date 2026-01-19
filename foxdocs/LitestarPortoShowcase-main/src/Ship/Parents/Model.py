"""Base Model class for Piccolo ORM."""

from piccolo.table import Table


class Model(Table):
    """Base Model class.

    All models should inherit from this class.
    It provides common functionality for all models.
    """

    class Meta:
        abstract = True
