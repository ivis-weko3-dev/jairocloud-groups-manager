from typing import Any

from sqlalchemy import JSON, String
from sqlalchemy.dialects import postgresql
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.orm import Mapped, mapped_column

from .shared import db


class ServiceSettings(db.Model):
    """Model representing the current settings of the application."""

    __tablename__ = "service_settings"

    key: Mapped[str] = mapped_column(
        String(100),
        primary_key=True,
    )
    """Primary key for the setting, representing the setting name."""

    value: Mapped[dict[str, Any]] = mapped_column(
        MutableDict.as_mutable(JSON().with_variant(postgresql.JSONB, "postgresql")),
    )
    """Value of the setting, stored as a JSON object."""
