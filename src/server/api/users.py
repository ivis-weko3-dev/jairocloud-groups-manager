#
# Copyright (C) 2025 National Institute of Informatics.
#

from flask import Blueprint, url_for
from flask_login import current_user, login_required
from flask_pydantic import validate
from server.api.helper import roles_required
from server.services.permmision import get_user_roles

from server.api.schema import ErrorResponse
from server.const import USER_ROLES
from server.entities.summaries import RepositorySummary
from server.entities.user_detail import UserDetail
from server.exc import (
    ResourceInvalid,
    ResourceNotFound,
)
from server.services import users


bp = Blueprint("users", __name__)


@bp.post("")
@bp.post("/")
@login_required
@roles_required("system_admin", "repository_admin")
@validate(response_by_alias=True)
def post(
    body: UserDetail,
) -> tuple[UserDetail, int, dict[str, str]] | tuple[ErrorResponse, int]:
    """Create user endpoint.

    Args:
        body(UserDetail): User information

    Returns:
        - If succeeded in creating user, user information
            and status code 201 and location header
        - If logged-in user does not have permission, status code 403
        - If id or eppn already exist, status code 409
        - If other error, status code 500

    """
    user = users.get_by_id(body.id)
    if user is not None:
        return ErrorResponse(code="", message="id already exist"), 409

    if body.eppns is not None:
        for eppn in body.eppns:
            user = users.get_by_eppn(eppn)
            if user is not None:
                return ErrorResponse(code="", message="eppn already exist"), 409

    is_member_of: str = current_user.is_member_of
    if not has_permission(is_member_of, body.repositories):
        return ErrorResponse(code="", message="not has permmision"), 403

    created = users.create(body)
    header = {
        "Location": url_for("api.users.id_get", user_id=created.id, _external=True)
    }
    return (created, 201, header)


@bp.get("/<string:user_id>")
@login_required
@roles_required("system_admin", "repository_admin")
@validate(response_by_alias=True)
def id_get(user_id: str) -> tuple[UserDetail | ErrorResponse, int]:
    """Get information of user endpoint.

    Args:
        user_id(str): User id

    Returns:
        - If succeeded in getting user information, user information and status code 200
        - If logged-in user does not have permission, status code 403
        - If user not found, status code 404
        - If other error, status code 500
    """
    user = users.get_by_id(user_id)
    if user is None:
        return ErrorResponse(code="", message="user not found"), 404

    is_member_of: str = current_user.is_member_of
    if not has_permission(is_member_of, user.repositories):
        return ErrorResponse(code="", message="not has permmision"), 403

    return user, 200


@bp.put("/<string:user_id>")
@login_required
@roles_required("system_admin", "repository_admin")
@validate(response_by_alias=True)
def id_put(user_id: str, body: UserDetail) -> tuple[UserDetail | ErrorResponse, int]:
    """Update user information endpoint.

    Args:
        user_id(str): User id
        body(UserDetail): User information

    Returns:
        - If succeeded in updating user informaion,
          user information and status code 200
        - If logged-in user does not have permission, status code 403
        - If user not found, status code 404
        - If coflicted user information, status code 409
        - If other error, status code 500

    """
    is_member_of: str = current_user.is_member_of
    if not has_permission(is_member_of, body.repositories):
        return ErrorResponse(code="", message="not has permmision"), 403

    try:
        return users.update(body), 200
    except ResourceNotFound as e:
        return ErrorResponse(code="", message=str(e)), 404
    except ResourceInvalid as e:
        return ErrorResponse(code="", message=str(e)), 409


def has_permission(
    is_member_of: str, repositories: list[RepositorySummary] | None
) -> bool:
    """Check user controll permmision.

    If the logged-in user is a system administrator or
    an administrator of the target repository, that user has permission.

    Args:
       is_member_of(str): The value of the user's isMemberOf attribute
       repositories(list[RepositorySummary] | None): Repositories list of request body

    Returns:
        bool:
        - True: logged-in user has permission
        - False: logged-in user does not have permission


    """
    user_roles: set[str]
    allowed_repository_ids: set[str]
    user_roles, allowed_repository_ids = get_user_roles(is_member_of)

    has_repository_permission = any(
        repo.id in allowed_repository_ids for repo in repositories or []
    )
    is_system_admin = USER_ROLES.SYSTEM_ADMIN in user_roles

    return is_system_admin or has_repository_permission
