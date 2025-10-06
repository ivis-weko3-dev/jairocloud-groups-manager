from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import EmailStr, Field, HttpUrl, UUID4

from const import MAP_USER_SCHEMA
from schema.base import BaseModel


class MapUser(BaseModel):
    """A user resource entity in mAP API."""

    schemas: list[str] = [MAP_USER_SCHEMA]
    """Schema URIs that define the attributes present in the User resource."""

    id: UUID4
    """The unique identifier for the user."""

    external_id: str | None = None
    """The external identifier for the user. Alias to 'externalId'."""

    user_name: str
    """The username of the user. Alias to 'userName'."""

    preferred_language: Literal["en", "ja"]
    """The preferred language of the user. Alias to 'preferredLanguage'."""

    meta: Meta
    """Metadata about the user."""

    edu_person_principal_names: list[EPPN] = []
    """A list of ePPN values associated with the user.
    Alias to 'eduPersonPrincipalNames'.
    """

    emails: list[Email] = []
    """A list of email addresses associated with the user."""

    groups: list[Group] = []
    """A list of groups the user belongs to."""


class Meta(BaseModel):
    resource_type: Literal["User"] = "User"
    """The type of resource. Always 'User'. Alias to 'resourceType'."""

    created: datetime
    """The date and time the resource was created."""

    last_modified: datetime
    """The date and time the resource was last modified.
    Alias to 'lastModified'.
    """

    created_by: str | None
    """The ID of the user who created this resource. Alias to 'createdBy'."""


class EPPN(BaseModel):
    value: str
    """eduPersonPrincipalName value"""

    idp_entity_id: str
    """The entity ID of the Identity Provider that issued this ePPN.
    Alias to 'idpEntityId'.
    """


class Email(BaseModel):
    value: EmailStr
    """Email address"""


class Group(BaseModel):
    value: str
    """Group ID"""

    ref: HttpUrl = Field(
        ...,
        # NOTE: not using `alias` because it changes the constructor arguments.
        validation_alias="$ref",
        serialization_alias="$ref",
    )
    """The URI of the corresponding Group resource. Alias to '$ref'."""
