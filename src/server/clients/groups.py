#
# Copyright (C) 2025 National Institute of Informatics.
#

"""Client for Group resources of mAP Core API."""

import typing as t

from http import HTTPStatus

import requests

from pydantic import TypeAdapter

from server.config import config
from server.const import MAP_GROUPS_ENDPOINT
from server.entities.map_error import MapError
from server.entities.map_group import MapGroup
from server.entities.search_request import SearchRequestParameter, SearchResponse

from .utils import compute_signature, get_time_stamp


type GetMapGroupResponse = MapGroup | MapError
"""Type alias for response of getting a MapGroup."""
adapter: TypeAdapter[GetMapGroupResponse] = TypeAdapter(GetMapGroupResponse)


type GroupsSearchResponse = SearchResponse[MapGroup]
"""Type alias for search response containing MapGroup resources."""
adapter_search: TypeAdapter[GroupsSearchResponse] = TypeAdapter(GroupsSearchResponse)


def search(
    query: SearchRequestParameter,
    /,
    include: set[str] | None = None,
    exclude: set[str] | None = None,
    *,
    access_token: str,
    client_secret: str,
) -> GroupsSearchResponse:
    """Search for Group resources in mAP API.

    Args:
        query (SearchRequestParameter): The search query parameters.
        include (set[str] | None):
            Attribute names to include in the response. Optional.
        exclude (set[str] | None):
            Attribute names to exclude from the response. Optional.
        access_token (str): OAuth access token for authorization.
        client_secret (str): Client secret for Basic Authentication.

    Returns:
        GroupsSearchResponse: The search response containing Group resources.
    """
    time_stamp = get_time_stamp()
    signature = compute_signature(client_secret, access_token, time_stamp)
    auth_params = {
        "time_stamp": time_stamp,
        "signature": signature,
    }

    attributes_params: dict[str, str] = {}
    if include:
        attributes_params[alias_generator("attributes")] = ",".join([
            alias_generator(name) for name in include | {"id"}
        ])
    if exclude:
        attributes_params[alias_generator("excludeAttributes")] = ",".join([
            alias_generator(name) for name in exclude
        ])

    query_params = query.model_dump(
        mode="json",
        by_alias=True,
    )

    response = requests.get(
        f"{config.MAP_CORE.base_url}{MAP_GROUPS_ENDPOINT}",
        params=auth_params | attributes_params | query_params,
        headers={
            "Authorization": f"Bearer {access_token}",
        },
        timeout=config.MAP_CORE.timeout,
    )

    if response.status_code > HTTPStatus.BAD_REQUEST:
        response.raise_for_status()

    return adapter_search.validate_json(response.text, extra="ignore")


def _get_alias_generator() -> t.Callable[[str], str]:
    generator = MapGroup.model_config.get("alias_generator")
    if generator and not callable(generator):
        generator = generator.serialization_alias
    if generator is None:
        generator = lambda x: x  # noqa: E731

    return generator


alias_generator: t.Callable[[str], str] = _get_alias_generator()
del _get_alias_generator
