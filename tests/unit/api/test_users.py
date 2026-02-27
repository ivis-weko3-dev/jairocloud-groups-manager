import inspect
import typing as t

import pytest

from flask import Flask
from pytest_mock import MockerFixture

from server.api import groups as groups_api, users as users_api
from server.api.groups import (
    GroupsQuery,
    ResourceInvalid,
    ResourceNotFound,
)
from server.api.users import ErrorResponse
from server.const import USER_ROLES
from server.entities.user_detail import RepositoryRole, UserDetail
from tests.helpers import UnexpectedError


if t.TYPE_CHECKING:
    from flask import Flask
    from pytest_mock import MockerFixture


def test_get_success(app: Flask, mocker: MockerFixture) -> None:
    """Tests group search returns SearchResult and 200 when found."""
    expected_result = object()  # Replace with actual SearchResult if available
    query = GroupsQuery(q="test-group", r=["repo1"], u=["user1"], s=0, v=1, k="display_name", d="asc", p=1, l=30)
    expected_status = 200
    mocker.patch("server.api.groups.has_permission", return_value=True)
    mocker.patch("server.services.groups.search", return_value=expected_result)
    original_func = inspect.unwrap(groups_api.get)
    result, status = original_func(query)
    assert result == expected_result
    assert status == expected_status


def test_get_not_found(app: Flask, mocker: MockerFixture) -> None:
    """Tests group search returns ErrorResponse and 404 when not found."""
    query = GroupsQuery(q="missing-group", r=[], u=[], s=0, v=1, k="display_name", d="asc", p=1, l=30)
    error_detail = "group not found"
    mocker.patch("server.api.groups.has_permission", return_value=True)
    mocker.patch("server.services.groups.search", side_effect=ResourceNotFound(error_detail))
    original_func = inspect.unwrap(groups_api.get)
    with pytest.raises(ResourceNotFound) as exc_info:
        original_func(query)
    assert str(exc_info.value) == error_detail


def test_get_invalid_request(app: Flask, mocker: MockerFixture) -> None:
    """Tests group search returns ErrorResponse and 400 when invalid request."""
    query = GroupsQuery(q="", r=[], u=[], s=0, v=1, k="display_name", d="asc", p=1, l=30)
    error_detail = "invalid request"
    mocker.patch("server.api.groups.has_permission", return_value=True)
    mocker.patch("server.services.groups.search", side_effect=ResourceInvalid(error_detail))
    original_func = inspect.unwrap(groups_api.get)
    with pytest.raises(ResourceInvalid) as exc_info:
        original_func(query)
    assert str(exc_info.value) == error_detail


def test_get_unexpected_error(app: Flask, mocker: MockerFixture) -> None:
    """Tests group search raises UnexpectedError when unexpected error occurs."""
    query = GroupsQuery(q="error-group", r=[], u=[], s=0, v=1, k="display_name", d="asc", p=1, l=30)
    error_detail = "unexpected error in get"
    mocker.patch("server.api.groups.has_permission", return_value=True)
    mocker.patch("server.services.groups.search", side_effect=UnexpectedError(error_detail))
    original_func = inspect.unwrap(groups_api.get)
    with pytest.raises(UnexpectedError) as exc_info:
        original_func(query)
    assert str(exc_info.value) == error_detail


def test_post_success(app: Flask, mocker: MockerFixture) -> None:
    """Tests user creation returns UserDetail, 201, and Location header."""

    user = UserDetail(
        id="u1",
        user_name="test user",
        emails=["test@example.com"],
        eppns=["eppn1"],
        preferred_language="en",
        repository_roles=[RepositoryRole(id="repo1", user_role=USER_ROLES.REPOSITORY_ADMIN)],
    )
    expected_status = 201
    expected_headers = {"Location": "https://host/api/users/u1"}
    mocker.patch("server.api.users.has_permission", return_value=True)
    mocker.patch("server.services.users.create", return_value=user)
    mocker.patch("server.api.users.url_for", return_value=expected_headers["Location"])

    original_func = inspect.unwrap(users_api.post)
    result, status, headers = original_func(user)
    assert result == user
    assert status == expected_status
    assert headers == expected_headers


def test_post_no_permission(app: Flask, mocker: MockerFixture) -> None:
    """Tests user creation returns ErrorResponse and 403 when no permission."""

    user = UserDetail(
        id="u2",
        user_name="no permission user",
        emails=["no_permission@example.com"],
        eppns=["eppn2"],
        preferred_language="en",
        repository_roles=[RepositoryRole(id="repo2", user_role=USER_ROLES.GENERAL_USER)],
    )
    expected_status = 403
    mocker.patch("server.api.users.has_permission", return_value=False)

    original_func = inspect.unwrap(users_api.post)
    result, status = original_func(user)

    assert isinstance(result, ErrorResponse)
    assert status == expected_status
    assert "not has permission" in result.message


def test_post_id_conflict(app: Flask, mocker: MockerFixture) -> None:
    """Tests user creation returns ErrorResponse and 409 when id or eppn already exist."""

    user = UserDetail(
        id="u3",
        user_name="conflict user",
        emails=["conflict@example.com"],
        eppns=["eppn3"],
        preferred_language="en",
        repository_roles=[RepositoryRole(id="repo3", user_role=USER_ROLES.REPOSITORY_ADMIN)],
    )
    error_detail = "id already exist"
    expected_status = 409
    mocker.patch("server.api.users.has_permission", return_value=True)
    mocker.patch("server.services.users.create", side_effect=ResourceInvalid(error_detail))

    original_func = inspect.unwrap(users_api.post)
    result, status = original_func(user)

    assert isinstance(result, ErrorResponse)
    assert status == expected_status
    assert error_detail in result.message


def test_id_get_success(app: Flask, mocker: MockerFixture) -> None:
    """Tests id_get returns UserDetail and 200 when user exists and has permission."""

    user = UserDetail(
        id="u10",
        user_name="user10",
        emails=["user10@example.com"],
        eppns=["eppn10"],
        preferred_language="en",
        repository_roles=[RepositoryRole(id="repo10", user_role=USER_ROLES.REPOSITORY_ADMIN)],
    )
    expected_status = 200
    mocker.patch("server.services.users.get_by_id", return_value=user)
    mocker.patch("server.api.users.has_permission", return_value=True)

    original_func = inspect.unwrap(users_api.id_get)
    result, status = original_func("u10")
    assert result == user
    assert status == expected_status


def test_id_get_no_permission(app: Flask, mocker: MockerFixture) -> None:
    """Tests id_get returns ErrorResponse and 403 when user exists but no permission."""

    user = UserDetail(
        id="u11",
        user_name="user11",
        emails=["user11@example.com"],
        eppns=["eppn11"],
        preferred_language="en",
        repository_roles=[RepositoryRole(id="repo11", user_role=USER_ROLES.GENERAL_USER)],
    )
    expected_status = 403
    mocker.patch("server.services.users.get_by_id", return_value=user)
    mocker.patch("server.api.users.has_permission", return_value=False)

    original_func = inspect.unwrap(users_api.id_get)
    result, status = original_func("u11")

    assert isinstance(result, ErrorResponse)
    assert status == expected_status
    assert "not has permission" in result.message


def test_id_get_not_found(app: Flask, mocker: MockerFixture) -> None:
    """Tests id_get returns ErrorResponse and 404 when user does not exist."""
    expected_status = 404
    mocker.patch("server.services.users.get_by_id", return_value=None)

    original_func = inspect.unwrap(users_api.id_get)
    result, status = original_func("u12")

    assert isinstance(result, ErrorResponse)
    assert status == expected_status
    assert "user not found" in result.message


def test_id_put_success(app: Flask, mocker: MockerFixture) -> None:
    """Tests id_put returns UserDetail and 200 when update succeeds."""

    user = UserDetail(
        id="u20",
        user_name="user20",
        emails=["user20@example.com"],
        eppns=["eppn20"],
        preferred_language="en",
        repository_roles=[RepositoryRole(id="repo20", user_role=USER_ROLES.REPOSITORY_ADMIN)],
    )
    expected_status = 200
    mocker.patch("server.api.users.has_permission", return_value=True)
    mocker.patch("server.services.users.update", return_value=user)

    original_func = inspect.unwrap(users_api.id_put)
    result, status = original_func("u20", user)
    assert result == user
    assert status == expected_status


def test_id_put_id_mismatch(app: Flask, mocker: MockerFixture) -> None:
    """Tests id_put returns ErrorResponse and 409 when user_id and body.id mismatch."""

    user = UserDetail(
        id="u21",
        user_name="user21",
        emails=["user21@example.com"],
        eppns=["eppn21"],
        preferred_language="en",
        repository_roles=[RepositoryRole(id="repo21", user_role=USER_ROLES.REPOSITORY_ADMIN)],
    )
    expected_status = 409

    original_func = inspect.unwrap(users_api.id_put)
    result, status = original_func("u22", user)

    assert isinstance(result, ErrorResponse)
    assert status == expected_status
    assert "user id mismatch" in result.message


def test_id_put_no_permission(app: Flask, mocker: MockerFixture) -> None:
    """Tests id_put returns ErrorResponse and 403 when no permission."""

    user = UserDetail(
        id="u23",
        user_name="user23",
        emails=["user23@example.com"],
        eppns=["eppn23"],
        preferred_language="en",
        repository_roles=[RepositoryRole(id="repo23", user_role=USER_ROLES.GENERAL_USER)],
    )
    expected_status = 403
    mocker.patch("server.api.users.has_permission", return_value=False)

    original_func = inspect.unwrap(users_api.id_put)
    result, status = original_func("u23", user)

    assert isinstance(result, ErrorResponse)
    assert status == expected_status
    assert "not has permmision" in result.message


def test_id_put_not_found(app: Flask, mocker: MockerFixture) -> None:
    """Tests id_put returns ErrorResponse and 404 when user not found."""

    user = UserDetail(
        id="u24",
        user_name="user24",
        emails=["user24@example.com"],
        eppns=["eppn24"],
        preferred_language="en",
        repository_roles=[RepositoryRole(id="repo24", user_role=USER_ROLES.REPOSITORY_ADMIN)],
    )
    expected_status = 404
    mocker.patch("server.api.users.has_permission", return_value=True)
    mocker.patch("server.services.users.update", side_effect=ResourceNotFound("not found"))

    original_func = inspect.unwrap(users_api.id_put)
    result, status = original_func("u24", user)

    assert isinstance(result, ErrorResponse)
    assert status == expected_status
    assert "not found" in result.message


def test_id_put_resource_invalid(app: Flask, mocker: MockerFixture) -> None:
    """Tests id_put returns ErrorResponse and 409 when resource invalid."""

    user = UserDetail(
        id="u25",
        user_name="user25",
        emails=["user25@example.com"],
        eppns=["eppn25"],
        preferred_language="en",
        repository_roles=[RepositoryRole(id="repo25", user_role=USER_ROLES.REPOSITORY_ADMIN)],
    )
    expected_status = 409
    mocker.patch("server.api.users.has_permission", return_value=True)
    mocker.patch("server.services.users.update", side_effect=ResourceInvalid("resource invalid"))

    original_func = inspect.unwrap(users_api.id_put)
    result, status = original_func("u25", user)

    assert isinstance(result, ErrorResponse)
    assert status == expected_status
    assert "resource invalid" in result.message


def test_has_permission_system_admin(mocker: MockerFixture) -> None:
    """Tests has_permission returns True for system admin."""

    mocker.patch("server.api.users.is_current_user_system_admin", return_value=True)

    result = users_api.has_permission([RepositoryRole(id="repoA", user_role=None)])
    assert result is True


def test_has_permission_repo_admin(mocker: MockerFixture) -> None:
    """Tests has_permission returns True for permitted repo admin."""

    mocker.patch("server.api.users.is_current_user_system_admin", return_value=False)
    mocker.patch("server.api.users.get_permitted_repository_ids", return_value=["repoB"])

    result = users_api.has_permission([RepositoryRole(id="repoB", user_role=None)])
    assert result is True


def test_has_permission_no_permission(mocker: MockerFixture) -> None:
    """Tests has_permission returns False for user without permission."""

    mocker.patch("server.api.users.is_current_user_system_admin", return_value=False)
    mocker.patch("server.api.users.get_permitted_repository_ids", return_value=["repoC"])

    result = users_api.has_permission([RepositoryRole(id="repoD", user_role=None)])
    assert result is False
