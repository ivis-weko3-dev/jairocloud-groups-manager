#
# Copyright (C) 2025 National Institute of Informatics.
#

"""API endpoints for repository-related operations."""

from flask import Blueprint, url_for
from flask_pydantic import validate

from server.entities.repository_detail import RepositoryDetail
from server.entities.search_request import SearchResult
from server.exc import InvalidQueryError, ResourceInvalid
from server.services import repositories
from server.services.permissions import (
    get_permitted_repository_ids,
    is_current_user_system_admin,
)

from .schemas import ErrorResponse, RepositoriesQuery


bp = Blueprint("repositories", __name__)


@bp.get("")
@bp.get("/")
@validate(response_by_alias=True)
def get(
    query: RepositoriesQuery,
) -> tuple[SearchResult, int] | tuple[ErrorResponse, int]:
    """Get a list of repositories based on query parameters.

    Args:
        query (RepositoriesQuery): Query parameters for filtering repositories.

    Returns:
        tuple[dict, int]:
            A tuple containing the list of repositories and the HTTP status code.
    """
    try:
        results = repositories.search(query)
    except InvalidQueryError as exc:
        return ErrorResponse(code="", message=str(exc)), 400

    return results, 200


@bp.post("")
@bp.post("/")
@validate(response_by_alias=True)
def post(
    body: RepositoryDetail,
) -> tuple[RepositoryDetail, int, dict[str, str]] | tuple[ErrorResponse, int]:
    """Create repository endpoint.

    Args:
        body(RepositoryDetail): Repository information

    Returns:
        - If succeeded in creating repository, repository information
            and status code 201 and location header
        - If logged-in user does not have permission, status code 403
        - If id already exists, status code 409
    """
    try:
        created = repositories.create(body)
    except ResourceInvalid as exc:
        return ErrorResponse(code="", message=str(exc)), 409

    location = url_for("api.repositories.id_get", repository_id=created.id)
    return created, 201, {"Location": location}


@bp.get("/<string:repository_id>")
@validate(response_by_alias=True)
def id_get(repository_id: str) -> tuple[RepositoryDetail | ErrorResponse, int]:
    """Get information of repository endpoint.

    Args:
        repository_id(str): Repository id

    Returns:
        - If succeeded in getting repository information,
            repository information and status code 200
        - If logged-in user does not have permission, status code 403
        - If repository not found, status code 404
        - If other error, status code 500
    """
    if not has_permission(repository_id):
        return ErrorResponse(code="", message="not has permission"), 403

    result = repositories.get_by_id(repository_id)
    if result is None:
        return ErrorResponse(code="", message="repository not found"), 404

    return result, 200


def has_permission(repository_id: str | None) -> bool:
    """Check user controll permmision.

    If the logged-in user is a system administrator or
    an administrator of the target repository, that user has permission.

    Args:
        repository_id (str | None): Repository ID to check permission for.

    Returns:
        bool:
        - True: logged-in user has permission
        - False: logged-in user does not have permission
    """
    if is_current_user_system_admin():
        return True

    permitted_repository_ids = get_permitted_repository_ids()
    return repository_id in permitted_repository_ids
