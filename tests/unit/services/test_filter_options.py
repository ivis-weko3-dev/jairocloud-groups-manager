import typing as t

import pytest

from server.services import filter_options
from server.services.utils.search_queries import (
    UsersCriteria,
)


if t.TYPE_CHECKING:
    from pytest_mock import MockerFixture


def test_search_repositories_options_normal(mocker: MockerFixture) -> None:
    """Test search_repositories_options returns correct FilterOption list."""
    expected = [
        filter_options.FilterOption(key="q", description="query", type="string", multiple=False),
        filter_options.FilterOption(
            key="k",
            description="sort key",
            type="string",
            multiple=False,
            items=[{"value": "name"}, {"value": "created_at"}],
        ),
        filter_options.FilterOption(key="d", description="direction", type="string", multiple=False),
    ]

    mocker.patch("server.services.filter_options.repository_sortable_keys", ["name", "created_at"])
    mocker.patch.object(filter_options.FilterOption, "_alias_generator", side_effect=lambda x: x)
    mocker.patch(
        "server.services.filter_options._initial_options",
        return_value=[filter_options.FilterOption(key="q", description="query", type="string", multiple=False)],
    )
    mocker.patch(
        "server.services.filter_options._common_options",
        return_value=[filter_options.FilterOption(key="d", description="direction", type="string", multiple=False)],
    )
    mocker.patch(
        "server.services.filter_options._get_description",
        return_value="sort key",
    )

    result = filter_options.search_repositories_options()
    assert result == expected


def test_search_groups_options_normal(mocker: MockerFixture) -> None:

    expected = [
        filter_options.FilterOption(key="q", description="query", type="string", multiple=False, items=None),
        filter_options.FilterOption(key="r", description="sort key", type="string", multiple=True, items=[]),
        filter_options.FilterOption(key="u", description="sort key", type="string", multiple=True, items=None),
        filter_options.FilterOption(
            key="s",
            description="sort key",
            type="number",
            multiple=False,
            items=[{"value": 0, "label": "public"}, {"value": 1, "label": "private"}],
        ),
        filter_options.FilterOption(
            key="v",
            description="sort key",
            type="number",
            multiple=False,
            items=[{"value": 0, "label": "Public"}, {"value": 1, "label": "Private"}, {"value": 2, "label": "Hidden"}],
        ),
        filter_options.FilterOption(
            key="k",
            description="sort key",
            type="string",
            multiple=False,
            items=[{"value": "gid"}, {"value": "created_at"}],
        ),
        filter_options.FilterOption(key="d", description="direction", type="string", multiple=False, items=None),
    ]
    mocker.patch("server.services.filter_options.group_sortable_keys", ["gid", "created_at"])
    mocker.patch.object(filter_options.FilterOption, "_alias_generator", side_effect=lambda x: x)
    mocker.patch(
        "server.services.filter_options._initial_options",
        return_value=[filter_options.FilterOption(key="q", description="query", type="string", multiple=False)],
    )
    mocker.patch(
        "server.services.filter_options._common_options",
        return_value=[filter_options.FilterOption(key="d", description="direction", type="string", multiple=False)],
    )
    mocker.patch(
        "server.services.filter_options._get_description",
        return_value="sort key",
    )

    result = filter_options.search_groups_options()
    assert result == expected


def test_search_users_options_normal(mocker: MockerFixture) -> None:
    expected = [
        filter_options.FilterOption(key="q", description="query", type="string", multiple=False, items=None),
        filter_options.FilterOption(
            key="r",
            description="affiliated repository IDs",
            type="string",
            multiple=True,
            items=[],
        ),
        filter_options.FilterOption(
            key="g",
            description="affiliated group IDs",
            type="string",
            multiple=True,
            items=[],
        ),
        filter_options.FilterOption(
            key="a",
            description="user roles",
            type="number",
            multiple=True,
            items=[
                {"value": 0, "label": "system_admin"},
                {"value": 1, "label": "repository_admin"},
                {"value": 2, "label": "community_admin"},
                {"value": 3, "label": "contributor"},
                {"value": 4, "label": "general_user"},
            ],
        ),
        filter_options.FilterOption(
            key="s", description="last modified date (from)", type="date", multiple=False, items=None
        ),
        filter_options.FilterOption(
            key="e", description="last modified date (to)", type="date", multiple=False, items=None
        ),
        filter_options.FilterOption(
            key="k",
            description="sort attribute key",
            type="string",
            multiple=False,
            items=[{"value": "uid"}, {"value": "created_at"}],
        ),
        filter_options.FilterOption(key="d", description="direction", type="string", multiple=False, items=None),
    ]

    mocker.patch("server.services.filter_options.user_sortable_keys", ["uid", "created_at"])
    mocker.patch.object(filter_options.FilterOption, "_alias_generator", side_effect=lambda x: x)
    mocker.patch(
        "server.services.filter_options._initial_options",
        return_value=[filter_options.FilterOption(key="q", description="query", type="string", multiple=False)],
    )
    mocker.patch(
        "server.services.filter_options._common_options",
        return_value=[filter_options.FilterOption(key="d", description="direction", type="string", multiple=False)],
    )
    mocker.patch("server.services.filter_options.is_current_user_system_admin", return_value=True)
    result = filter_options.search_users_options()
    assert result == expected


def test__initial_options_normal() -> None:
    expected = [
        filter_options.FilterOption(
            key="q",
            description="search term",
            type="string",
            multiple=False,
            items=None,
        ),
        filter_options.FilterOption(
            key="i",
            description="resource IDs",
            type="string",
            multiple=True,
            items=None,
        ),
    ]
    opts = filter_options._initial_options()  # noqa: SLF001
    assert opts == expected


def test__common_options_normal() -> None:
    expected = [
        filter_options.FilterOption(
            key="d",
            description="sort order",
            type="string",
            multiple=False,
            items=[
                {"value": "asc", "label": "Ascending"},
                {"value": "desc", "label": "Descending"},
            ],
        ),
        filter_options.FilterOption(
            key="p",
            description="page number",
            type="number",
            multiple=False,
            items=None,
        ),
        filter_options.FilterOption(
            key="l",
            description="page size",
            type="number",
            multiple=False,
            items=None,
        ),
    ]
    opts = filter_options._common_options()  # noqa: SLF001
    assert opts == expected


def test__common_options_error(monkeypatch: pytest.MonkeyPatch):

    def bad_get_description(*a, **kw):
        error_msg = "desc error"
        raise RuntimeError(error_msg)

    monkeypatch.setattr(filter_options, "_get_description", bad_get_description)
    with pytest.raises(RuntimeError) as exc_info:
        filter_options._common_options()  # noqa: SLF001
    assert "desc error" in str(exc_info.value)


def test__get_description_annotated() -> None:

    desc = filter_options._get_description(UsersCriteria, "g")  # noqa: SLF001
    assert desc == "affiliated group IDs"


def test__get_description_none() -> None:

    desc = filter_options._get_description(UsersCriteria, "-")  # noqa: SLF001
    assert desc is None


def test__get_type_variants() -> None:
    assert filter_options._get_type(UsersCriteria, "r") == "string"  # noqa: SLF001
    assert filter_options._get_type(UsersCriteria, "g") == "string"  # noqa: SLF001
    assert filter_options._get_type(UsersCriteria, "a") == "number"  # noqa: SLF001
    assert filter_options._get_type(UsersCriteria, "s") == "date"  # noqa: SLF001
    assert filter_options._get_type(UsersCriteria, "e") == "date"  # noqa: SLF001


def test__allow_multiple_variants() -> None:
    assert filter_options._allow_multiple(UsersCriteria, "r") is True  # noqa: SLF001
    assert filter_options._allow_multiple(UsersCriteria, "g") is True  # noqa: SLF001
    assert filter_options._allow_multiple(UsersCriteria, "a") is True  # noqa: SLF001
    assert filter_options._allow_multiple(UsersCriteria, "s") is False  # noqa: SLF001
    assert filter_options._allow_multiple(UsersCriteria, "e") is False  # noqa: SLF001
