#
# Copyright (C) 2025 National Institute of Informatics.
#

"""Models for history entity for client side."""

import typing as t

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, computed_field

from server.entities.summaries import GroupSummary, RepositorySummary, UserSummary


class DownloadHistory(BaseModel):
    """Download history model."""

    @computed_field
    @property
    def sum_download(self) -> int:
        """Total number of downloads."""
        return len(self.download_history_data)

    @computed_field
    @property
    def first_download(self) -> int:
        """Number of first-time downloads."""
        return sum(1 for item in self.download_history_data if item.parent_id is None)

    @computed_field
    @property
    def re_download(self) -> int:
        """Number of re-downloads."""
        return self.sum_download - self.first_download

    download_history_data: list[DownloadHistoryData]


class UploadHistory(BaseModel):
    """Upload history model."""

    @computed_field
    @property
    def sum_upload(self) -> int:
        """Total number of uploads."""
        return len(self.upload_history_data)

    @computed_field
    @property
    def success_upload(self) -> int:
        """Number of successful uploads."""
        return sum(1 for item in self.upload_history_data if item.status == "S")

    @computed_field
    @property
    def failed_upload(self) -> int:
        """Number of failed uploads."""
        return sum(1 for item in self.upload_history_data if item.status == "F")

    @computed_field
    @property
    def progress_upload(self) -> int:
        """Number of uploads in progress."""
        return sum(1 for item in self.upload_history_data if item.status == "P")

    upload_history_data: list[UploadHistoryData]


class DownloadHistoryData(BaseModel):
    """Download history data model."""

    id: UUID
    """Download history ID."""

    timestamp: datetime
    """Timestamp of the download event."""

    operator: UserSummary
    """Operator who performed the download."""

    public: bool
    """Indicates if the download was public."""

    parent_id: UUID | None = None
    """Parent download history ID, if applicable."""

    file_path: str
    """Path of the downloaded file."""

    repositories: list[RepositorySummary]
    """List of repository IDs involved in the download."""

    groups: list[GroupSummary]
    """List of group IDs involved in the download."""

    users: list[UserSummary]
    """List of user IDs involved in the download."""

    children_count: int = 0
    """Number of related child elements."""


class UploadHistoryData(BaseModel):
    """Upload history data model."""

    id: UUID
    """Upload history ID."""

    timestamp: datetime
    """Timestamp of the upload event."""

    end_timestamp: datetime | None = None
    """Timestamp end of the upload event."""

    public: bool
    """Indicates if the upload was public."""

    operator: UserSummary
    """Operator who performed the upload."""

    status: t.Literal["S", "F", "P"]
    """Status of the upload operation."""

    results: list[Results] = Field(default_factory=list)
    """ """

    summary: HistorySummary | None = None
    """ """

    file_path: str
    """Path of the uploaded file."""

    repositories: list[RepositorySummary]
    """List of repository IDs involved in the upload."""

    groups: list[GroupSummary]
    """List of group IDs involved in the upload."""

    users: list[UserSummary]
    """List of user IDs involved in the upload."""


class Results(BaseModel):
    """Result of the upload operation."""

    user_id: str
    """User ID."""
    eppn: str
    """EPPN."""
    user_name: str
    """User name."""
    group: list[str]
    """Group list."""
    status: t.Literal["C", "U", "S", "D", "E"]
    """Status of the upload operation."""
    code: str | None
    """Error code if the upload failed."""


class HistorySummary(BaseModel):
    """Summary of the history operation."""

    create: int
    """Number of created items."""
    update: int
    """Number of updated items."""
    delete: int
    """Number of deleted items."""
    skip: int
    """Number of skipped items."""
    error: int
    """Number of error items."""


class HistoryQuery(BaseModel):
    """Query parameters for searching history data."""

    model_config = ConfigDict(populate_by_name=True)

    s: datetime | None = Field(default=None, description="start_date")
    """Start date for filtering history records."""

    e: datetime | None = Field(default=None, description="end_date")
    """End date for filtering history records."""

    u: list[str] | None = Field(default=None, description="user_id")
    """List of user IDs to filter history records."""

    r: list[str] | None = Field(default=None, description="repository_id")
    """List of repository IDs to filter history records."""

    g: list[str] | None = Field(default=None, description="group_id")
    """List of group IDs to filter history records."""

    o: list[str] | None = Field(default=None, description="operator")
    """List of operators to filter history records."""

    i: list[str] | None = Field(default=None, description="id")
    """List of Parent ID to retrieve child elements """

    d: t.Annotated[
        t.Literal["asc", "desc"] | None,
        "direction",
    ] = None
    """Sort order: 'asc' (ascending) or 'desc' (descending)."""

    p: t.Annotated[int | None, "page"] = None
    """Page number for pagination."""

    l: t.Annotated[int | None, "length"] = None  # noqa: E741
    """Number of users per page for pagination."""


class HistoryDataFilter(BaseModel):
    """Available filters for history data."""

    operators: list[UserSummary]
    """List of operators."""

    target_repositories: list[RepositorySummary]
    """List of target repositories."""

    target_groups: list[GroupSummary]
    """List of target groups."""

    target_users: list[UserSummary]
    """List of target users."""
