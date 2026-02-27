from datetime import UTC, datetime
from unittest.mock import MagicMock

import pytest

from pydantic import HttpUrl

from server.entities.group_detail import (
    GroupDetail,
    Repository as GroupRepository,
    Service as GroupService_,
    UserSummary,
)
from server.entities.map_group import MapGroup
from server.entities.map_service import Administrator as ServiceAdministrator, Group, MapService, Meta as ServiceMeta
from server.entities.repository_detail import RepositoryDetail
from server.exc import InvalidFormError, SystemAdminNotFound
from server.services.utils import transformers


def test_prepare_service_normal(app, mocker, test_config):

    service_url: HttpUrl = HttpUrl(test_config.MAP_CORE.base_url)
    repo = RepositoryDetail(id="repo1", service_name="svc", service_url=service_url, entity_ids=["eid"])
    expected = MapService(
        id="svc1",
        administrators=[ServiceAdministrator.model_validate({"value": "user1"})],
        groups=[Group(value="admin-repo1")],
    )
    mocker.patch(
        "server.services.utils.transformers.validate_repository_to_map_service", return_value=MapService(id="svc1")
    )
    mocker.patch("server.services.utils.transformers.resolve_repository_id", return_value="repo1")
    mocker.patch("server.services.utils.transformers.config.GROUPS.id_patterns", {"admin": "admin-{repository_id}"})
    mocker.patch("server.services.utils.transformers.USER_ROLES", ["admin"])
    result = transformers.prepare_service(repo, {"user1"})

    assert result == expected


def test_prepare_service_no_admin(app, mocker, test_config):
    service_url: HttpUrl = HttpUrl(test_config.MAP_CORE.base_url)
    repo = RepositoryDetail(id="repo1", service_name="svc", service_url=service_url, entity_ids=["eid"])
    mocker.patch(
        "server.services.utils.transformers.validate_repository_to_map_service", return_value=MapService(id="svc1")
    )
    with pytest.raises(SystemAdminNotFound):
        transformers.prepare_service(repo, set())


def test_validate_repository_to_map_service_missing_name(app, mocker, test_config):

    service_url: HttpUrl = HttpUrl(test_config.MAP_CORE.base_url)

    repo = RepositoryDetail(id="repo1", service_name=None, service_url=service_url, entity_ids=["eid"])
    with pytest.raises(InvalidFormError):
        transformers.validate_repository_to_map_service(repo)


def test_validate_repository_to_map_service_missing_url(app, mocker, test_config):
    repo = RepositoryDetail(id="repo1", service_name="svc", service_url=None, entity_ids=["eid"])
    with pytest.raises(InvalidFormError):
        transformers.validate_repository_to_map_service(repo)


def test_validate_repository_to_map_service_url_too_long(app, mocker, test_config):
    long_url = "http://" + "a" * (test_config.REPOSITORIES.max_url_length + 10)
    repo = RepositoryDetail(id="repo1", service_name="svc", service_url=long_url, entity_ids=["eid"])
    with pytest.raises(InvalidFormError):
        transformers.validate_repository_to_map_service(repo)


def test_validate_repository_to_map_service_missing_entity_ids(app, mocker, test_config):
    service_url: HttpUrl = HttpUrl(test_config.MAP_CORE.base_url)
    repo = RepositoryDetail(id="repo1", service_name="svc", service_url=service_url, entity_ids=None)
    with pytest.raises(InvalidFormError):
        transformers.validate_repository_to_map_service(repo)
    repo2 = RepositoryDetail(id="repo1", service_name="svc", service_url=service_url, entity_ids=[])
    with pytest.raises(InvalidFormError):
        transformers.validate_repository_to_map_service(repo2)


def test_make_map_service_normal(app, mocker, test_config):
    service_url: HttpUrl = HttpUrl(test_config.MAP_CORE.base_url)

    repo = RepositoryDetail(id="repo1", service_name="svc", service_url=service_url, entity_ids=["eid"])
    result = transformers.make_map_service(repo)
    assert isinstance(result, MapService)
    assert result.service_name == "svc"


def test_prepare_group_normal(app, mocker):
    detail = GroupDetail(id="g1", display_name="Group1", public=True, member_list_visibility="Public", type="group")
    mocker.patch(
        "server.services.utils.transformers.validate_group_to_map_group", return_value=(MapGroup(id="g1"), "repo1")
    )
    mocker.patch("server.services.utils.transformers.resolve_service_id", return_value="svc1")
    result = transformers.prepare_group(detail, {"user1"})
    assert result.administrators is not None
    assert result.administrators[0].value == "user1"
    assert isinstance(result, MapGroup)


def test_prepare_group_no_admin(app, mocker):
    detail = GroupDetail(id="g1", display_name="Group1", public=True, member_list_visibility="Public", type="group")
    mocker.patch(
        "server.services.utils.transformers.validate_group_to_map_group", return_value=(MapGroup(id="g1"), "repo1")
    )
    with pytest.raises(SystemAdminNotFound):
        transformers.prepare_group(detail, set())


def test_make_group_detail_normal(mocker):
    group = MapGroup(id="g1", display_name="Group1", public=True, member_list_visibility="Public")
    mocker.patch("server.services.utils.transformers.detect_affiliation", return_value=MagicMock(type="group"))
    result = transformers.make_group_detail(group)
    assert result.id == "g1"
    assert result.type == "group"


def test_validate_group_to_map_group_missing_display_name(app):

    detail = GroupDetail(id="g1", display_name=None, public=True, member_list_visibility="Public", type="group")
    with pytest.raises(InvalidFormError):
        transformers.validate_group_to_map_group(detail, mode="create")


def test_make_map_group_normal(app):
    detail = GroupDetail(id="g1", display_name="Group1", public=True, member_list_visibility="Public", type="group")
    result = transformers.make_map_group(detail)
    assert isinstance(result, MapGroup)
    assert result.display_name == "Group1"


def test_validate_group_to_map_group_missing_id_update(app):
    detail = GroupDetail(id=None, display_name="Group1", public=True, member_list_visibility="Public", type="group")
    with pytest.raises(InvalidFormError):
        transformers.validate_group_to_map_group(detail, mode="update")


def test_validate_group_to_map_group_missing_repository_id_create(app):
    detail = GroupDetail(
        id="g1", display_name="Group1", public=True, member_list_visibility="Public", type="group", repository=None
    )
    with pytest.raises(InvalidFormError):
        transformers.validate_group_to_map_group(detail, mode="create")


def test_validate_group_to_map_group_repository_not_found(app, monkeypatch):

    detail = GroupDetail(id="g1", display_name="Group1", public=True, member_list_visibility="Public", type="group")
    detail.repository = GroupRepository(id="repo1")
    monkeypatch.setattr("server.services.repositories.get_by_id", lambda _: None)
    with pytest.raises(InvalidFormError):
        transformers.validate_group_to_map_group(detail, mode="create")


def test_validate_group_to_map_group_missing_user_defined_id(app, mocker):
    detail = GroupDetail(id="g1", display_name="Group1", public=True, member_list_visibility="Public", type="group")
    detail.repository = GroupRepository(id="repo1")
    detail.user_defined_id = None
    mocker.patch("server.services.repositories.get_by_id", return_value=None)
    with pytest.raises(InvalidFormError):
        transformers.validate_group_to_map_group(detail, mode="create")


def test_validate_group_to_map_group_user_defined_id_too_long(app, mocker):
    detail = GroupDetail(id="g1", display_name="Group1", public=True, member_list_visibility="Public", type="group")
    detail.repository = GroupRepository(id="repo1")
    repository_id = "repo1"
    max_id_length = 10
    detail.user_defined_id = "a" * (max_id_length + 1)
    mocker.patch("server.services.repositories.get_by_id", return_value=None)
    mocker.patch("server.config.config.GROUPS.max_id_length", max_id_length + len(repository_id))
    with pytest.raises(InvalidFormError):
        transformers.validate_group_to_map_group(detail, mode="create")


def test_make_repository_detail_minimal(mocker, test_config):
    """Test make_repository_detail with minimal MapService (no groups, meta, admins, etc)."""
    service_url: HttpUrl = HttpUrl(test_config.MAP_CORE.base_url)

    service = MapService(id="svc1", service_name="svc", service_url=service_url)
    mocker.patch("server.services.utils.transformers.resolve_repository_id", return_value="repo1")
    result = transformers.make_repository_detail(service)
    assert result.id == "repo1"
    assert result.service_id == "svc1"
    assert result.groups_count is None
    assert result.users_count is None
    assert result.created is None


def test_make_repository_detail_with_meta_and_admins(mocker, test_config):
    """Test make_repository_detail with meta, groups, and administrators."""

    service_url: HttpUrl = HttpUrl(test_config.MAP_CORE.base_url)
    users_count = 5
    meta = ServiceMeta.model_validate({
        "created": datetime(2024, 1, 1, tzinfo=UTC),
        "last_modified": datetime(2024, 1, 2, tzinfo=UTC),
    })

    service = MapService(
        id="svc1",
        service_name="svc",
        service_url=service_url,
        meta=meta,
        administrators=[ServiceAdministrator(value="admin1")],
        groups=[Group(value="group1")],
    )
    mocker.patch("server.services.utils.transformers.resolve_repository_id", return_value="repo1")
    mocker.patch("server.services.utils.transformers.detect_affiliation", return_value=MagicMock(type="group"))
    mocker.patch("server.services.utils.transformers.make_criteria_object", return_value={})
    mocker.patch("server.services.users.count", return_value=5)
    result = transformers.make_repository_detail(service, more_detail=True)
    assert result.created == datetime(2024, 1, 1, tzinfo=UTC)
    assert result.users_count == users_count
    assert result.groups_count == 1


def test_make_map_service_active_and_entity_ids(app, test_config):
    """Test make_map_service with active and entity_ids fields."""
    service_url: HttpUrl = HttpUrl(test_config.MAP_CORE.base_url)

    repo = RepositoryDetail(
        id="repo1", service_name="svc", service_url=service_url, active=True, entity_ids=["eid1", "eid2"]
    )
    result = transformers.make_map_service(repo)
    assert result.suspended is False
    assert result.entity_ids is not None
    assert [e.value for e in result.entity_ids] == ["eid1", "eid2"]


def test_validate_group_to_map_group_public_and_visibility_default(app, mocker):
    """Test validate_group_to_map_group sets default public/member_list_visibility if None."""

    detail = GroupDetail(id="g1", display_name="Group1", public=None, member_list_visibility=None, type="group")
    detail.repository = GroupRepository(id="repo1")
    detail.user_defined_id = "udid"
    mocker.patch("server.services.repositories.get_by_id", return_value=True)
    mocker.patch("server.config.config.GROUPS.max_id_length", 100)
    mocker.patch("server.config.config.GROUPS.id_patterns.user_defined", "{repository_id}-{user_defined_id}")
    result, _ = transformers.validate_group_to_map_group(detail, mode="create")
    assert result.public is not None
    assert result.member_list_visibility is not None


def test_make_map_group_all_fields():
    """Test make_map_group with all optional fields present."""
    detail = GroupDetail(
        id="g1", display_name="Group1", public=True, description="desc", member_list_visibility="Public", type="group"
    )
    detail._users = [UserSummary(id="u1", user_name="User1")]  # noqa: SLF001
    detail._admins = [UserSummary(id="a1", user_name="Admin1")]  # noqa: SLF001
    detail._services = [GroupService_(id="s1", service_name="Service1")]  # noqa: SLF001
    result = transformers.make_map_group(detail)
    assert isinstance(result, MapGroup)
    assert result.id == "g1"
    assert result.display_name == "Group1"
    assert result.public is True
    assert result.description == "desc"
    assert result.member_list_visibility == "Public"
    assert result.members is not None
    assert result.administrators is not None
    assert result.services is not None
    assert result.members[0].value == "u1"
    assert result.administrators[0].value == "a1"
    assert result.services[0].value == "s1"
    assert result.services[0].display == "Service1"


def test_make_map_group_minimal():
    """Test make_map_group with only required fields."""
    detail = GroupDetail(id="g2", display_name="Group2", public=False, member_list_visibility="Private", type="group")
    result = transformers.make_map_group(detail)
    assert isinstance(result, MapGroup)
    assert result.id == "g2"
    assert result.display_name == "Group2"
    assert result.public is False
    assert result.member_list_visibility == "Private"
    assert result.members is None or result.members == []
    assert result.administrators is None or result.administrators == []
    assert result.services is None or result.services == []
