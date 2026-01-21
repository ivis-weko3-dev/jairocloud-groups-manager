#
# Copyright (C) 2025 National Institute of Informatics.
#

"""Schema definitions for the API endpoints.

These schemas used in request and response validation.
"""

from pydantic import BaseModel, ConfigDict


class OAuthTokenQuery(BaseModel):
    """Schema for OAuth token query parameters."""

    code: str
    """Authorization code received from the Authorization Server."""

    state: str
    """State parameter to prevent CSRF attacks."""

    model_config = ConfigDict(extra="ignore")


class ErrorResponse(BaseModel):
    """Schema for error paremeters."""

    code: str
    """Message code."""

    message: str
    """Error message."""
