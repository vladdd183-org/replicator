"""Piccolo configuration file."""

from piccolo.conf.apps import AppRegistry

from src.Ship.Core.Database import DB

# Database configuration
DB = DB

# App registry
APP_REGISTRY = AppRegistry(
    apps=[
        "src.Containers.AppSection.Book.PiccoloApp",
    ]
)
