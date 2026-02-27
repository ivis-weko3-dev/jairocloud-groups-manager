import typing as t

import pytest

from server.services.utils import resolvers


if t.TYPE_CHECKING:
    from flask import Flask
    from pytest_mock import MockerFixture


def test_resolve_repository_id_with_fqdn(app: Flask, mocker: MockerFixture):
    """Tests resolve_repository_id returns correct id from fqdn."""

    fqdn = "repo.example-domain.com"
    expected = "repo_example_domain_com"
    mocker.patch(
        "server.services.utils.resolvers.config.REPOSITORIES.id_patterns.sp_connector", "sp_{repository_id}_suffix"
    )

    result = resolvers.resolve_repository_id(fqdn=fqdn)

    assert result == expected


def test_resolve_repository_id_with_service_id(app: Flask, mocker: MockerFixture):
    """Tests resolve_repository_id returns correct id from service_id."""
    pattern = "sp_{repository_id}_suffix"
    prefix = pattern.split("{repository_id}", maxsplit=1)[0]
    suffix = pattern.split("{repository_id}")[1]
    repository_id = "myrepo"
    service_id = f"{prefix}{repository_id}{suffix}"
    mocker.patch("server.services.utils.resolvers.config.REPOSITORIES.id_patterns.sp_connector", pattern)

    result = resolvers.resolve_repository_id(service_id=service_id)

    assert result == repository_id


def test_resolve_repository_id_error(app: Flask, mocker: MockerFixture):
    """Tests resolve_repository_id raises ValueError if neither fqdn nor service_id is provided."""

    error_msg = "Either 'fqdn' or 'resource_id' must be provided."
    mocker.patch(
        "server.services.utils.resolvers.config.REPOSITORIES.id_patterns.sp_connector", "sp_{repository_id}_suffix"
    )

    with pytest.raises(ValueError, match=error_msg):
        resolvers.resolve_repository_id()


def test_resolve_service_id_with_fqdn(app: Flask, mocker: MockerFixture):
    """Tests resolve_service_id returns correct service_id from fqdn."""
    pattern = "sp_{repository_id}_suffix"
    fqdn = "repo.example-domain.com"
    expected_repository_id = "repo_example_domain_com"
    expected_service_id = pattern.format(repository_id=expected_repository_id)
    mocker.patch("server.services.utils.resolvers.config.REPOSITORIES.id_patterns.sp_connector", pattern)

    result = resolvers.resolve_service_id(fqdn=fqdn)

    assert result == expected_service_id


def test_resolve_service_id_with_repository_id(app: Flask, mocker: MockerFixture):
    """Tests resolve_service_id returns correct service_id from repository_id."""
    pattern = "sp_{repository_id}_suffix"
    repository_id = "myrepo"
    expected_service_id = pattern.format(repository_id=repository_id)
    mocker.patch("server.services.utils.resolvers.config.REPOSITORIES.id_patterns.sp_connector", pattern)

    result = resolvers.resolve_service_id(repository_id=repository_id)

    assert result == expected_service_id


def test_resolve_service_id_error(app: Flask, mocker: MockerFixture):
    """Tests resolve_service_id raises ValueError if neither fqdn nor repository_id is provided."""

    error_msg = "Either 'fqdn' or 'repository_id' must be provided."
    mocker.patch(
        "server.services.utils.resolvers.config.REPOSITORIES.id_patterns.sp_connector", "sp_{repository_id}_suffix"
    )

    with pytest.raises(ValueError, match=error_msg):
        resolvers.resolve_service_id()
