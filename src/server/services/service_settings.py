#
# Copyright (C) 2025 National Institute of Informatics.
#

"""Services for managing service settings.

Provides functions to get and save service configuration data in the database.
"""

import typing as t

from pydantic_core import ValidationError

from server.db import db
from server.db.service_settings import ServiceSettings
from server.exc import ClientCredentialsError
from server.schemas.auth import ClientCredentials


def get_client_credentials() -> ClientCredentials | None:
    """Get client credentials from service settings.

    Returns:
        ClientCredentials: The credentials if present and valid, otherwise None.

    Raises:
        ClientCredentialsError: If the stored credentials are invalid.
    """
    setting = _get_setting("client_credentials")
    if setting is None:
        return None

    try:
        creds = ClientCredentials(**setting)
    except ValidationError as exc:
        error = "Invalid client credentials in service settings."
        raise ClientCredentialsError(error) from exc

    return creds


def save_client_credentials(credentials: ClientCredentials) -> None:
    """Save client credentials to service settings.

    Args:
        credentials (ClientCredentials): The credentials to save.
    """
    _save_setting("client_credentials", credentials.model_dump(mode="json"))


def _get_setting(key: str) -> dict[str, t.Any] | None:
    """Get the value of a service setting by key.

    Args:
        key (str): The setting key.

    Returns:
        dict: The setting value as a dictionary, or None if not found.
    """
    setting = db.session.get(ServiceSettings, key)
    return setting.value if setting else None


def _save_setting(key: str, value: dict[str, t.Any]) -> None:
    """Save or update the value of a service setting.

    Args:
        key (str): The setting key.
        value (dict[str, Any]): The setting value to save.
    """
    setting = db.session.get(ServiceSettings, key)
    if setting:
        setting.value = value
    else:
        setting = ServiceSettings(key=key, value=value)  # pyright: ignore[reportCallIssue]
        db.session.add(setting)
    db.session.commit()
