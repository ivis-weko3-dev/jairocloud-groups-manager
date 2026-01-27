#
# Copyright (C) 2025 National Institute of Informatics.
#

"""API endpoints for repository-related operations."""

from flask import Blueprint
from flask_pydantic import validate

from server.entities.search_request import SearchResult
from server.services import repositories

from .schemas import RepositoriesQuery


bp = Blueprint("repositories", __name__)


@bp.get("")
@bp.get("/")
@validate(response_by_alias=True)
def get(query: RepositoriesQuery) -> tuple[SearchResult, int]:
    """Get a list of repositories based on query parameters.

    Args:
        query (RepositoriesQuery): Query parameters for filtering repositories.

    Returns:
        tuple[dict, int]:
            A tuple containing the list of repositories and the HTTP status code.
    """
    results = repositories.search(query)
    return results, 200
