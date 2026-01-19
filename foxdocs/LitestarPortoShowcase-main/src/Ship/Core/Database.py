"""Database configuration with Piccolo ORM."""

from pathlib import Path

from piccolo.conf.apps import AppRegistry
from piccolo.engine.sqlite import SQLiteEngine

from src.Ship.Configs import get_settings


def get_engine() -> SQLiteEngine:
    """Get database engine."""
    settings = get_settings()
    
    # Extract database path from URL
    db_path = settings.database_url.replace("sqlite:///", "")
    
    # Ensure directory exists
    db_file = Path(db_path)
    db_file.parent.mkdir(parents=True, exist_ok=True)
    
    return SQLiteEngine(path=str(db_file))


# Database engine instance
DB = get_engine()

# App registry for Piccolo
APP_REGISTRY = AppRegistry(
    apps=[
        "src.Containers.AppSection.Book.PiccoloApp",
        "src.Containers.AppSection.User.PiccoloApp",
        "src.Containers.VendorSection.Payment.PiccoloApp",
        "src.Containers.VendorSection.Notification.PiccoloApp",
    ]
)
