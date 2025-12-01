import typing as t

from datetime import datetime  # noqa: TC003

from const import MAP_GROUP_SCHEMA
from pydantic import UUID4, Field, HttpUrl

from .base import BaseModel


class MapGroup(BaseModel):
    """A group resource entity in mAP API."""

    schemas: t.Sequence[str] = Field(default_factory=lambda: [MAP_GROUP_SCHEMA])
    """Schema URIs that define the attributes present in the Group resource."""

    id: UUID4
    """The unique identifier for the group."""

    external_id: str | None = None
    """The external identifier for the group. Alias to 'externalId'."""

    display_name: str
    """The display name of the group. Alias to 'displayName'."""

    public: bool
    """Whether the group is public or private."""

    description: str | None = None
    """The description of the group."""

    suspended: bool = False
    """Whether the group is suspended."""

    member_list_visibility: Visibility = "Private"
    """The visibility of the member list. Alias to 'memberListVisibility'."""

    meta: Meta
    """Metadata about the group."""

    members: list[Member] = Field(default_factory=list)
    """The members of the group."""

    administrators: list[Administrator] = Field(default_factory=list)
    """The administrators of the group."""

    services: list[Service] = Field(default_factory=list)
    """The services associated with the group."""


type Visibility = t.Literal["Public", "Private", "Hidden"]


class Meta(BaseModel):
    resource_type: t.Literal["Group"] = "Group"
    """The type of resource. Always 'Group'. Alias to 'resourceType'."""

    created: datetime
    """The date and time the resource was created."""

    last_modified: datetime
    """The date and time the resource was last modified.
    Alias to 'lastModified'.
    """


type Member = t.Annotated[MemberUser | MemberGroup, Field(..., discriminator="type")]


class MemberUser(BaseModel):
    ref: HttpUrl = Field(
        ...,
        # NOTE: not using `alias` because it changes the constructor arguments.
        validation_alias="$ref",
        serialization_alias="$ref",
    )
    """The URI of the corresponding User resource. Alias to '$ref'."""

    type: t.Literal["User"] = "User"
    """The type of the member. Always 'User'."""

    display: str
    """The display name of the user."""

    value: str
    """The user ID"""

    custom_role: list[str] = Field(default_factory=list)
    """The custom roles assigned to the user. Alias to 'customRole'."""


class MemberGroup(BaseModel):
    ref: HttpUrl = Field(
        ...,
        # NOTE: not using `alias` because it changes the constructor arguments.
        validation_alias="$ref",
        serialization_alias="$ref",
    )
    """The URI of the corresponding Group resource. Alias to '$ref'."""

    type: t.Literal["Group"] = "Group"
    """The type of the member. Always 'Group'."""

    display: str
    """The display name of the group."""

    value: str
    """The group ID"""


class Administrator(BaseModel):
    ref: HttpUrl = Field(
        ...,
        # NOTE: not using `alias` because it changes the constructor arguments.
        validation_alias="$ref",
        serialization_alias="$ref",
    )
    """The URI of the corresponding User resource. Alias to '$ref'."""

    display: str
    """The display name of the user."""

    value: str
    """The user ID"""


class Service(BaseModel):
    ref: HttpUrl = Field(
        ...,
        # NOTE: not using `alias` because it changes the constructor arguments.
        validation_alias="$ref",
        serialization_alias="$ref",
    )
    """The URI of the corresponding Service resource. Alias to '$ref'."""

    display: str
    """The display name of the service."""

    value: str
    """The service ID"""

    administrator_of_group: int
    """The flag indicating whether the service is an administrator of the group.
    Alias to 'administratorOfGroup'.
    """
