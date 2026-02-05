import hashlib
import inspect
import json
import time
import typing as t

import pytest

from requests.exceptions import HTTPError

from server.clients import users
from server.entities.map_error import MapError
from server.entities.map_user import MapUser
from tests.helpers import load_json_data


if t.TYPE_CHECKING:
    from flask import Flask
    from pytest_mock import MockerFixture


def test_get_by_id_success(app: Flask, mocker: MockerFixture) -> None:
    """Test that a user is returned when a valid user_id is provided."""
    json_data = load_json_data("data/map_user.json")

    expected_user = MapUser.model_validate(json_data)
    user_id: str = json_data["id"]
    access_token = "token"
    expected_time_stamp = str(int(time.time()))
    expected_signature = hashlib.sha256(b"dummy_hash").hexdigest()
    expected_headers = {"Authorization": f"Bearer {access_token}"}
    expected_timeout = users.config.MAP_CORE.timeout
    expected_params = {
        "time_stamp": expected_time_stamp,
        "signature": expected_signature,
    }

    mocker.patch("server.clients.users.get_time_stamp", return_value=expected_time_stamp)
    mocker.patch("server.clients.users.compute_signature", return_value=expected_signature)
    mock_response = mocker.patch("server.clients.users.requests.get")
    mock_response.return_value.text = json.dumps(json_data)
    mock_response.return_value.status_code = 200

    original_func = inspect.unwrap(users.get_by_id)
    result = original_func(user_id, access_token=access_token, client_secret="secret")
    mock_response.assert_called_once()
    call_args, called_kwargs = mock_response.call_args

    assert result == expected_user
    assert user_id in call_args[0]
    assert users.config.MAP_CORE.base_url in call_args[0]
    assert called_kwargs["params"] == expected_params
    assert called_kwargs["headers"] == expected_headers
    assert called_kwargs["timeout"] == expected_timeout


def test_get_by_id_with_include_exclude(app: Flask, mocker: MockerFixture) -> None:
    """Test that include/exclude params are reflected in attributes_params."""
    json_data = load_json_data("data/map_user.json")

    expected_user = MapUser.model_validate(json_data)
    user_id: str = json_data["id"]
    expected_time_stamp = str(int(time.time()))
    expected_signature = hashlib.sha256(b"dummy_hash").hexdigest()
    include = {"name", "email"}
    exclude = {"phone"}
    expected_params = _build_expected_params(expected_time_stamp, expected_signature, include, exclude)

    mocker.patch("server.clients.users.get_time_stamp", return_value=expected_time_stamp)
    mocker.patch("server.clients.users.compute_signature", return_value=expected_signature)
    mock_response = mocker.patch("server.clients.users.requests.get")
    mock_response.return_value.text = json.dumps(json_data)
    mock_response.return_value.status_code = 200

    original_func = inspect.unwrap(users.get_by_id)
    result = original_func(user_id, include=include, exclude=exclude, access_token="token", client_secret="secret")

    mock_response.assert_called_once()
    call_args, called_kwargs = mock_response.call_args
    params = called_kwargs["params"]

    assert result == expected_user
    assert params == expected_params
    assert user_id in call_args[0]
    assert users.config.MAP_CORE.base_url in call_args[0]


def test_get_by_id_not_found(app: Flask, mocker: MockerFixture) -> None:
    """Test that None is returned when the user is not found (404)."""
    json_data = load_json_data("data/map_error.json")
    user_id = "nonexistent_user"
    expected_error = MapError.model_validate(json_data | {"detail": json_data["detail"] % user_id})

    mock_response = mocker.patch("server.clients.users.requests.get")
    mock_response.return_value.text = expected_error.model_dump_json()
    mock_response.return_value.status_code = 200

    original_func = inspect.unwrap(users.get_by_id)
    result = original_func(user_id, access_token="token", client_secret="secret")

    assert isinstance(result, MapError)
    assert "Not Found" in result.detail


def test_get_by_id_http_error(app: Flask, mocker: MockerFixture) -> None:
    """Test that HTTP errors are raised when status_code > 400."""
    json_data = load_json_data("data/map_user.json")
    user_id: str = json_data["id"]

    mock_response = mocker.patch("server.clients.users.requests.get")
    mock_response.return_value.text = json.dumps(json_data)
    mock_response.return_value.raise_for_status.side_effect = HTTPError("401 Unauthorized")
    mock_response.return_value.status_code = 401

    original_func = inspect.unwrap(users.get_by_id)
    with pytest.raises(HTTPError, match="401 Unauthorized"):
        original_func(user_id, access_token="token", client_secret="secret")


def _build_expected_params(
    time_stamp: str,
    signature: str,
    include: set[str],
    exclude: set[str],
) -> dict:
    attributes_key = users.alias_generator("attributes")
    excluded_key = users.alias_generator("excluded_attributes")
    return {
        "time_stamp": time_stamp,
        "signature": signature,
        attributes_key: ",".join([users.alias_generator(n) for n in include | {"id"}]),
        excluded_key: ",".join([users.alias_generator(n) for n in exclude]),
    }
