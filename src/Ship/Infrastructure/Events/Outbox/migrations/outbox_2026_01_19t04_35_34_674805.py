"""Initial migration for OutboxEvent table.

Creates the outbox_events table for Transactional Outbox pattern.
"""

from piccolo.apps.migrations.auto.migration_manager import MigrationManager
from piccolo.columns.column_types import Boolean, Integer, Text, Timestamptz, UUID, Varchar
from piccolo.columns.defaults.timestamptz import TimestamptzNow
from piccolo.columns.defaults.uuid import UUID4
from piccolo.columns.indexes import IndexMethod


ID = "2026-01-19T04:35:34:674805"
VERSION = "1.30.0"
DESCRIPTION = "Create outbox_events table for Transactional Outbox pattern"


async def forwards():
    manager = MigrationManager(
        migration_id=ID, app_name="outbox", description=DESCRIPTION
    )

    # Create table
    manager.add_table(
        class_name="OutboxEvent",
        tablename="outbox_events",
        schema=None,
        columns=None,
    )

    # Primary key: id (UUID)
    manager.add_column(
        table_class_name="OutboxEvent",
        tablename="outbox_events",
        column_name="id",
        db_column_name="id",
        column_class_name="UUID",
        column_class=UUID,
        params={
            "default": UUID4(),
            "null": False,
            "primary_key": True,
            "unique": False,
            "index": False,
            "index_method": IndexMethod.btree,
            "choices": None,
            "db_column_name": None,
            "secret": False,
        },
        schema=None,
    )

    # Event name
    manager.add_column(
        table_class_name="OutboxEvent",
        tablename="outbox_events",
        column_name="event_name",
        db_column_name="event_name",
        column_class_name="Varchar",
        column_class=Varchar,
        params={
            "length": 255,
            "default": "",
            "null": False,
            "primary_key": False,
            "unique": False,
            "index": True,
            "index_method": IndexMethod.btree,
            "choices": None,
            "db_column_name": None,
            "secret": False,
        },
        schema=None,
    )

    # Payload (JSON serialized event data)
    manager.add_column(
        table_class_name="OutboxEvent",
        tablename="outbox_events",
        column_name="payload",
        db_column_name="payload",
        column_class_name="Text",
        column_class=Text,
        params={
            "default": "",
            "null": False,
            "primary_key": False,
            "unique": False,
            "index": False,
            "index_method": IndexMethod.btree,
            "choices": None,
            "db_column_name": None,
            "secret": False,
        },
        schema=None,
    )

    # Aggregate type (optional, for debugging)
    manager.add_column(
        table_class_name="OutboxEvent",
        tablename="outbox_events",
        column_name="aggregate_type",
        db_column_name="aggregate_type",
        column_class_name="Varchar",
        column_class=Varchar,
        params={
            "length": 100,
            "default": "",
            "null": True,
            "primary_key": False,
            "unique": False,
            "index": True,
            "index_method": IndexMethod.btree,
            "choices": None,
            "db_column_name": None,
            "secret": False,
        },
        schema=None,
    )

    # Aggregate ID (optional, for debugging)
    manager.add_column(
        table_class_name="OutboxEvent",
        tablename="outbox_events",
        column_name="aggregate_id",
        db_column_name="aggregate_id",
        column_class_name="Varchar",
        column_class=Varchar,
        params={
            "length": 100,
            "default": "",
            "null": True,
            "primary_key": False,
            "unique": False,
            "index": True,
            "index_method": IndexMethod.btree,
            "choices": None,
            "db_column_name": None,
            "secret": False,
        },
        schema=None,
    )

    # Created at timestamp
    manager.add_column(
        table_class_name="OutboxEvent",
        tablename="outbox_events",
        column_name="created_at",
        db_column_name="created_at",
        column_class_name="Timestamptz",
        column_class=Timestamptz,
        params={
            "default": TimestamptzNow(),
            "null": False,
            "primary_key": False,
            "unique": False,
            "index": True,
            "index_method": IndexMethod.btree,
            "choices": None,
            "db_column_name": None,
            "secret": False,
        },
        schema=None,
    )

    # Published at timestamp (null until published)
    manager.add_column(
        table_class_name="OutboxEvent",
        tablename="outbox_events",
        column_name="published_at",
        db_column_name="published_at",
        column_class_name="Timestamptz",
        column_class=Timestamptz,
        params={
            "default": None,
            "null": True,
            "primary_key": False,
            "unique": False,
            "index": False,
            "index_method": IndexMethod.btree,
            "choices": None,
            "db_column_name": None,
            "secret": False,
        },
        schema=None,
    )

    # Is published flag
    manager.add_column(
        table_class_name="OutboxEvent",
        tablename="outbox_events",
        column_name="is_published",
        db_column_name="is_published",
        column_class_name="Boolean",
        column_class=Boolean,
        params={
            "default": False,
            "null": False,
            "primary_key": False,
            "unique": False,
            "index": True,
            "index_method": IndexMethod.btree,
            "choices": None,
            "db_column_name": None,
            "secret": False,
        },
        schema=None,
    )

    # Retry count
    manager.add_column(
        table_class_name="OutboxEvent",
        tablename="outbox_events",
        column_name="retry_count",
        db_column_name="retry_count",
        column_class_name="Integer",
        column_class=Integer,
        params={
            "default": 0,
            "null": False,
            "primary_key": False,
            "unique": False,
            "index": False,
            "index_method": IndexMethod.btree,
            "choices": None,
            "db_column_name": None,
            "secret": False,
        },
        schema=None,
    )

    # Max retries
    manager.add_column(
        table_class_name="OutboxEvent",
        tablename="outbox_events",
        column_name="max_retries",
        db_column_name="max_retries",
        column_class_name="Integer",
        column_class=Integer,
        params={
            "default": 5,
            "null": False,
            "primary_key": False,
            "unique": False,
            "index": False,
            "index_method": IndexMethod.btree,
            "choices": None,
            "db_column_name": None,
            "secret": False,
        },
        schema=None,
    )

    # Error message (last error if failed)
    manager.add_column(
        table_class_name="OutboxEvent",
        tablename="outbox_events",
        column_name="error_message",
        db_column_name="error_message",
        column_class_name="Text",
        column_class=Text,
        params={
            "default": "",
            "null": True,
            "primary_key": False,
            "unique": False,
            "index": False,
            "index_method": IndexMethod.btree,
            "choices": None,
            "db_column_name": None,
            "secret": False,
        },
        schema=None,
    )

    # Next retry timestamp (for exponential backoff)
    manager.add_column(
        table_class_name="OutboxEvent",
        tablename="outbox_events",
        column_name="next_retry_at",
        db_column_name="next_retry_at",
        column_class_name="Timestamptz",
        column_class=Timestamptz,
        params={
            "default": None,
            "null": True,
            "primary_key": False,
            "unique": False,
            "index": True,
            "index_method": IndexMethod.btree,
            "choices": None,
            "db_column_name": None,
            "secret": False,
        },
        schema=None,
    )

    return manager
