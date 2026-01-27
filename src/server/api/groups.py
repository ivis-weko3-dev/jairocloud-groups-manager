#
# Copyright (C) 2025 National Institute of Informatics.
#

"""API endpoints for group-related operations."""

from flask import Blueprint
from flask_pydantic import validate

from server.entities.search_request import FilterOption, SearchResult
from server.services import groups
from server.services.filter_options import search_groups_options

from .schemas import GroupsQuery


bp = Blueprint("groups", __name__)


@bp.get("")
@bp.get("/")
@validate(response_by_alias=True)
def get(query: GroupsQuery) -> tuple[SearchResult, int]:
    """Get a list of groups based on query parameters.

    Args:
        query (GroupsQuery): Query parameters for filtering groups.

    Returns:
        tuple[dict, int]:
            A tuple containing the list of groups and the HTTP status code.
    """
    results = groups.search(query)
    return results, 200


@bp.get("/filter-options")
@validate(response_many=True)
def filter_options() -> list[FilterOption]:
    """Get filter options for groups search.

    Returns:
        list[FilterOption]: List of filter options for group search.
    """
    return search_groups_options()
