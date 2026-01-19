"""Base Model class for Piccolo ORM."""

from piccolo.table import Table


class Model(Table):
    """Base Model class.
    
    All models should inherit from this class.
    It provides common functionality for all models.
    
    Example:
        class User(Model):
            id = UUID(primary_key=True, default=UUID4())
            email = Varchar(length=255, unique=True)
            name = Varchar(length=100)
    """
    
    class Meta:
        """Piccolo meta configuration."""
        
        abstract = True



