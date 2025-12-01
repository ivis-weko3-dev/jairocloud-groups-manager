import typing as t

from pydantic import Field

from server.const import MAP_ERROR_SCHEMA

from .base import BaseModel


class MapError(BaseModel):
    """An error response entity in mAP API."""

    schemas: t.Sequence[str] = Field(default_factory=lambda: [MAP_ERROR_SCHEMA])
    """Schema URIs that define the attributes present in the Error resource."""

    status: t.Literal[
        "307",
        "308",
        "400",
        "401",
        "403",
        "404",
        "409",
        "412",
        "413",
        "415",
        "500",
        "501",
    ]
    """The HTTP status code of the error as a string."""

    scim_type: t.Literal[
        "invalidFilter",
        "tooMany",
        "uniqueness",
        "mutability",
        "invalidValue",
        "invalidSyntax",
        "noTarget",
        "invalidVers",
        "sensitive",
    ]
    """The SCIM error type. Alias to 'scimType'."""

    detail: str
    """A detailed description of the error."""

    error_code: int | None = None
    """An error response code. Alias to 'errorCode'."""
