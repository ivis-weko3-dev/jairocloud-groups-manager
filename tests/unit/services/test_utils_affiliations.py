import pytest

from server.services.utils.affiliations import (
    _build_combined_regex,
    _Group,
    _RoleGroup,
    detect_affiliation,
    detect_affiliations,
)


def test_detect_affiliations(app):
    sys = "jc_roles_sysadm_test"
    repo = "jc_test_ac_jp_roles_repoadm_test"
    comado = "jc_test_ac_jp_roles_comadm_test"
    contributer = "jc_test_ac_jp_roles_contributor_test"
    generaluser = "jc_test_ac_jp_roles_generaluser_test"
    user = "jc_test_ac_jp_groups_test3_test"
    result = detect_affiliations([sys, repo, comado, contributer, generaluser, user])

    expected_repository_id_sys = None
    expected_roles_sys = ["system_admin"]
    expected_rolegroup_type = "role"

    expected_repository_id = "test_ac_jp"
    expected_roles = ["repository_admin", "community_admin", "contributor", "general_user"]

    expected_group_repository_id = "test_ac_jp"
    expected_group_id = "jc_test_ac_jp_groups_test3_test"
    expected_user_defined_id = "test3"
    expected_group_type = "group"

    assert isinstance(result.roles[0], _RoleGroup)
    assert result.roles[0].repository_id == expected_repository_id_sys
    assert result.roles[0].roles == expected_roles_sys
    assert result.roles[0].type == expected_rolegroup_type

    assert isinstance(result.roles[1], _RoleGroup)
    assert result.roles[1].repository_id == expected_repository_id
    assert sorted(result.roles[1].roles) == sorted(expected_roles)
    assert result.roles[1].type == expected_rolegroup_type

    assert isinstance(result.groups[0], _Group)
    assert result.groups[0].repository_id == expected_group_repository_id
    assert result.groups[0].group_id == expected_group_id
    assert result.groups[0].user_defined_id == expected_user_defined_id
    assert result.groups[0].type == expected_group_type


def test_detect_affiliation_no_match(app):
    result = detect_affiliation("test1_roles_repoadm_test")
    expected = None
    assert result == expected


@pytest.mark.parametrize(
    ("group_id", "expected_repository_id", "expected_roles", "expected_type"),
    [
        ("jc_roles_sysadm_test", None, ["system_admin"], "role"),
        ("jc_test_ac_jp_roles_repoadm_test", "test_ac_jp", ["repository_admin"], "role"),
        ("jc_test_ac_jp_roles_comadm_test", "test_ac_jp", ["community_admin"], "role"),
        ("jc_test_ac_jp_roles_contributor_test", "test_ac_jp", ["contributor"], "role"),
        ("jc_test_ac_jp_roles_generaluser_test", "test_ac_jp", ["general_user"], "role"),
    ],
    ids=["sysadm", "repoadm", "comadm", "contributer", "generaluser"]
)
def test_detect_affiliation_role_group(app, group_id, expected_repository_id, expected_roles, expected_type):
    result = detect_affiliation(group_id)
    assert result is not None
    assert isinstance(result, _RoleGroup)
    assert result.repository_id == expected_repository_id
    assert result.roles == expected_roles
    assert result.type == expected_type


def test_detect_affiliation_group(app):
    expected_repository_id = "test_ac_jp"
    expected_group_id = "jc_test_ac_jp_groups_test3_test"
    expected_user_defined_id = "test3"
    expected_type = "group"

    result = detect_affiliation("jc_test_ac_jp_groups_test3_test")
    assert result is not None
    assert isinstance(result, _Group)
    assert result.repository_id == expected_repository_id
    assert result.group_id == expected_group_id
    assert result.user_defined_id == expected_user_defined_id
    assert result.type == expected_type


def test_build_combined_regex_sys(app):
    pattern = _build_combined_regex().pattern
    expected = "(?P<system_admin>jc_roles_sysadm_test)"

    assert expected in pattern


def test_build_combined_regex_repo(app):
    pattern = _build_combined_regex().pattern
    expected = "(?P<repository_admin>jc_(?P<repository_admin__repository_id>.+?)_roles_repoadm_test)"

    assert expected in pattern


def test_build_combined_regex_com(app):
    pattern = _build_combined_regex().pattern
    expected = "(?P<community_admin>jc_(?P<community_admin__repository_id>.+?)_roles_comadm_test)"

    assert expected in pattern


def test_build_combined_regex_con(app):
    pattern = _build_combined_regex().pattern
    expected = "(?P<contributor>jc_(?P<contributor__repository_id>.+?)_roles_contributor_test)"

    assert expected in pattern


def test_build_combined_regex_gene(app):
    pattern = _build_combined_regex().pattern
    expected = "(?P<general_user>jc_(?P<general_user__repository_id>.+?)_roles_generaluser_test)"

    assert expected in pattern


def test_build_combined_regex_user(app):
    pattern = _build_combined_regex().pattern
    expected = "(?P<user_defined>jc_(?P<user_defined__repository_id>.+?)_groups_(?P<user_defined__user_defined_id>.+?)_test)"

    assert expected in pattern


def test_build_combined_regex_len(app, test_config):
    pattern = _build_combined_regex().pattern
    patterns_config = test_config.GROUPS.id_patterns.model_dump()

    assert len(patterns_config) == len(pattern.split("|"))
