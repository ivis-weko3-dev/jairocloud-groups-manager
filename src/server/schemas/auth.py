#
# Copyright (C) 2025 National Institute of Informatics.
#

"""Schemas for authentication and authorization.

These are used in the mAP Core Authorization Server.
"""

from pydantic import BaseModel, ConfigDict


class ClientCredentials(BaseModel):
    """Schema for client credentials."""

    client_id: str
    """Client identifier."""

    client_secret: str
    """Client secret."""

    model_config = ConfigDict(extra="ignore")
