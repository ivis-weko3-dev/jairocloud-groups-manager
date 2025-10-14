import uuid
from datetime import datetime
from typing import get_args, Literal
from zoneinfo import ZoneInfo

from sqlalchemy import CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column

from db.shared import db


class UploadHistory(db.Model):
    """Model representing the upload history of files."""

    __tablename__ = "upload_history"

    type Status = Literal["S", "P", "F", "C"]
    """Allowed status values for the upload history.
    - 'S': Success
    - 'P': In Progress
    - 'F': Failed
    - 'C': Canceled
    """

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )
    """Primary key for the upload history record."""

    file_uid: Mapped[uuid.UUID] = mapped_column(
        unique=True,
        default=uuid.uuid4,
    )
    """Unique identifier for the upload record."""

    user_id: Mapped[uuid.UUID]
    """Identifier of the user who uploaded the file."""

    filename: Mapped[str] = mapped_column(
        db.String(255),
    )
    """Name of the uploaded file."""

    upload_time: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(tz=ZoneInfo("UTC")),
    )
    """Timestamp of when the file was uploaded."""

    status: Mapped[Status] = mapped_column(
        db.String(1),
    )
    """Status of the upload (e.g., 'success', 'failed')."""

    __table_args__ = (
        CheckConstraint(
            status.in_(get_args(Status.__value__)),
            name="status",
        ),
    )
