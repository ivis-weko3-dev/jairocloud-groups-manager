from __future__ import annotations

from datetime import datetime
from typing import Literal, Annotated

from pydantic import Field, HttpUrl, UUID4

from const import MAP_GROUP_SCHEMA
from schema.base import BaseModel


class MapGroup(BaseModel):
    """A group resource entity in mAP API."""

    schemas: list[str] = [MAP_GROUP_SCHEMA]
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

    members: list[Member] = []
    """The members of the group."""

    administrators: list[Administrator] = []
    """The administrators of the group."""

    services: list[Service] = []
    """The services associated with the group."""


type Visibility = Literal["Public", "Private", "Hidden"]


class Meta(BaseModel):
    resource_type: Literal["Group"] = "Group"
    """The type of resource. Always 'Group'. Alias to 'resourceType'."""

    created: datetime
    """The date and time the resource was created."""

    last_modified: datetime
    """The date and time the resource was last modified.
    Alias to 'lastModified'.
    """


type Member = Annotated[MemberUser | MemberGroup, Field(..., discriminator="type")]


class MemberUser(BaseModel):
    ref: HttpUrl = Field(
        ...,
        # NOTE: not using `alias` because it changes the constructor arguments.
        validation_alias="$ref",
        serialization_alias="$ref",
    )
    """The URI of the corresponding User resource. Alias to '$ref'."""

    type: Literal["User"] = "User"
    """The type of the member. Always 'User'."""

    display: str
    """The display name of the user."""

    value: str
    """The user ID"""

    custom_role: list[str] = []
    """The custom roles assigned to the user. Alias to 'customRole'."""


class MemberGroup(BaseModel):
    ref: HttpUrl = Field(
        ...,
        # NOTE: not using `alias` because it changes the constructor arguments.
        validation_alias="$ref",
        serialization_alias="$ref",
    )
    """The URI of the corresponding Group resource. Alias to '$ref'."""

    type: Literal["Group"] = "Group"
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
