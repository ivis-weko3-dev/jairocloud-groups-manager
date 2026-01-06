#
# Copyright (C) 2025 National Institute of Informatics.
#

"""Client for mAP API for User resource management."""

from http import HTTPStatus

import requests

from pydantic import TypeAdapter

from server.config import config
from server.const import MAP_EXIST_EPPN_ENDPOINT, MAP_USERS_ENDPOINT
from server.entities.map_error import MapError
from server.entities.map_user import MapUser

from .utils import compute_signature, get_time_stamp


type GetMapUserResponse = MapUser | MapError


def get_by_id(user_id: str, *, access_token: str, client_secret: str) -> MapUser | None:
    """Get a User resource by its ID from mAP API.

    Args:
        user_id (str): ID of the User resource.
        access_token (str): OAuth access token for authorization.
        client_secret (str): Client secret for Basic Authentication.

    Returns:
        MapUser: The User resource if found, otherwise None.
    """
    time_stamp = get_time_stamp()
    signature = compute_signature(client_secret, access_token, time_stamp)

    response = requests.get(
        f"{config.MAP_CORE.base_url}{MAP_USERS_ENDPOINT}/{user_id}",
        params={
            "time_stamp": time_stamp,
            "signature": signature,
        },
        headers={
            "Authorization": f"Bearer {access_token}",
        },
        timeout=config.MAP_CORE.timeout,
    )

    if response.status_code > HTTPStatus.BAD_REQUEST:
        response.raise_for_status()

    adapter: TypeAdapter[GetMapUserResponse] = TypeAdapter(GetMapUserResponse)
    result = adapter.validate_json(response.text, extra="ignore")

    if isinstance(result, MapError):
        return None
    return result


def get_by_eppn(eppn: str, access_token: str, client_secret: str) -> MapUser | None:
    """Get a User resource by its ePPN from mAP API.

    Args:
        eppn (str): ePPN of the User resource.
        access_token (str): OAuth access token for authorization.
        client_secret (str): Client secret for Basic Authentication.

    Returns:
        MapUser: The User resource if found, otherwise None.
    """
    time_stamp = get_time_stamp()
    signature = compute_signature(client_secret, access_token, time_stamp)

    response = requests.get(
        f"{config.MAP_CORE.base_url}{MAP_EXIST_EPPN_ENDPOINT}/{eppn}",
        params={
            "time_stamp": time_stamp,
            "signature": signature,
        },
        headers={
            "Authorization": f"Bearer {access_token}",
        },
        timeout=config.MAP_CORE.timeout,
    )

    if response.status_code > HTTPStatus.BAD_REQUEST:
        response.raise_for_status()

    adapter: TypeAdapter[GetMapUserResponse] = TypeAdapter(GetMapUserResponse)
    result = adapter.validate_json(response.text, extra="ignore")

    if isinstance(result, MapError):
        return None
    return result
