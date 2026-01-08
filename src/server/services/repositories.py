#
# Copyright (C) 2025 National Institute of Informatics.
#

"""Services for managing repositories."""

import typing as t

from http import HTTPStatus

import requests

from pydantic_core import ValidationError

from server.clients import services
from server.entities.repository import RepositoryDetail
from server.exc import (
    CredentialsError,
    OAuthTokenError,
    UnexpectedResponseError,
)

from .token import get_access_token, get_client_secret


if t.TYPE_CHECKING:
    from server.entities.map_service import MapService


def get_by_id(service_id: str) -> RepositoryDetail | None:
    """Get a Repository resource by its ID.

    Args:
        service_id (str): ID of the Repository resource.

    Returns:
        RepositoryDetail: The Repository resource if found, otherwise None.

    Raises:
        OAuthTokenError: If the access token is invalid or expired.
        CredentialsError: If the client credentials are invalid.
        UnexpectedResponseError: If response from mAP Core API is unexpected.
    """
    try:
        access_token = get_access_token()
        client_secret = get_client_secret()
        map_service: MapService | None = services.get_by_id(
            service_id,
            access_token=access_token,
            client_secret=client_secret,
        )
    except requests.HTTPError as exc:
        code = exc.response.status_code
        if code == HTTPStatus.UNAUTHORIZED:
            error = "Access token is invalid or expired."
            raise OAuthTokenError(error) from exc

        if code == HTTPStatus.INTERNAL_SERVER_ERROR:
            error = "mAP Core API server error."
            raise UnexpectedResponseError(error) from exc

        error = "Failed to get Repository resource from mAP Core API."
        raise UnexpectedResponseError(error) from exc

    except requests.RequestException as exc:
        error = "Failed to connect to mAP Core API."
        raise UnexpectedResponseError(error) from exc

    except ValidationError as exc:
        error = "Failed to parse response from mAP Core API."
        raise UnexpectedResponseError(error) from exc

    except OAuthTokenError, CredentialsError:
        raise

    if map_service is None:
        return None

    return RepositoryDetail.from_map_service(map_service)


def create(repository: RepositoryDetail) -> RepositoryDetail:
    """Create a new Repository resource.

    Args:
        repository (RepositoryDetail): The Repository resource to create.

    Returns:
        RepositoryDetail: The created Repository resource.

    Raises:
        OAuthTokenError: If the access token is invalid or expired.
        CredentialsError: If the client credentials are invalid.
        UnexpectedResponseError: If response from mAP Core API is unexpected.
    """
    try:
        access_token = get_access_token()
        client_secret = get_client_secret()
        map_service: MapService = services.post(
            repository.to_map_service(),
            exclude={"meta"},
            access_token=access_token,
            client_secret=client_secret,
        )

    except requests.HTTPError as exc:
        code = exc.response.status_code
        if code == HTTPStatus.UNAUTHORIZED:
            error = "Access token is invalid or expired."
            raise OAuthTokenError(error) from exc

        if code == HTTPStatus.INTERNAL_SERVER_ERROR:
            error = "mAP Core API server error."
            raise UnexpectedResponseError(error) from exc

        error = "Failed to create Repository resource in mAP Core API."
        raise UnexpectedResponseError(error) from exc

    except requests.RequestException as exc:
        error = "Failed to connect to mAP Core API."
        raise UnexpectedResponseError(error) from exc

    except ValidationError as exc:
        error = "Failed to parse response from mAP Core API."
        raise UnexpectedResponseError(error) from exc

    except OAuthTokenError, CredentialsError:
        raise

    return RepositoryDetail.from_map_service(map_service)
