from typing import Protocol

from pydantic import BaseModel

from db import db
from db.service_settings import ServiceSettings
from schema.others import ClientCert, OAuthToken


def _get_setting[T: BaseModel](key: str, model: type[T]) -> T | None:
    """Retrieve a setting by key and validate it against the provided Pydantic model.

    Args:
        key (str): The key of the setting to retrieve.
        model (type[T]): The Pydantic model class to represent the setting value.

    Returns:
        T | None: An instance of the setting value, or None if the setting does not exist.
    """
    setting = db.session.get(ServiceSettings, key)
    if setting:
        return model.model_validate(setting.value, extra="ignore")
    return None


def _set_setting(key: str, value: BaseModel) -> None:
    """Set or update a setting in the database.

    Args:
        key (str): The key of the setting to set or update.
        value (BaseModel): The Pydantic model instance representing the setting value.
    """
    setting = db.session.get(ServiceSettings, key)
    if setting:
        setting.value = value.model_dump(mode="json")
    else:
        setting = ServiceSettings()
        setting.key = key
        setting.value = value.model_dump(mode="json")
        db.session.add(setting)
    db.session.commit()


class _ClientCert(Protocol):
    client_id: str
    client_secret: str


def get_client_cert():
    """Retrieve the stored client certificate.

    Returns:
        ClientCert | None: The stored client certificate, or None if not found.
    """
    return _get_setting("client_cert", ClientCert)


def set_client_cert(cert: _ClientCert) -> None:
    """Store or update the client certificate.

    Args:
        cert (ClientCert): The client certificate to store.
    """
    if not isinstance(cert, ClientCert):
        cert = ClientCert(**cert.__dict__)
    _set_setting("client_cert", cert)


class _OAuthToken(Protocol):
    access_token: str
    token_type: str
    expires_in: int
    refresh_token: str | None = None
    scope: str | None = None


def get_access_token():
    """Retrieve the stored OAuth access token.

    Returns:
        OAuthToken | None: The stored OAuth access token, or None if not found.
    """
    return _get_setting("access_token", OAuthToken)


def set_access_token(token: _OAuthToken) -> None:
    """Store or update the OAuth access token.

    Args:
        token (OAuthToken): The OAuth access token to store.
    """
    if not isinstance(token, OAuthToken):
        token = OAuthToken(**token.__dict__)
    _set_setting("access_token", token)
