#
# Copyright (C) 2025 National Institute of Informatics.
#

"""Models for Group entity for client side."""

import typing as t

from datetime import datetime

from pydantic import BaseModel, PrivateAttr

from .common import camel_case_config, forbid_extra_config
from .map_group import Administrator, MapGroup, MemberUser, Visibility
from .summaries import UserSummary


class GroupDetail(BaseModel):
    """Model for detailed Group information in mAP Core API."""

    id: str
    """The unique identifier for the group."""

    user_defined_id: str | None = None
    """The part of group ID that is user-defined. Alias to 'userDefinedId'."""

    display_name: str
    """The display name of the group. Alias to 'displayName'."""

    description: str | None = None
    """The description of the group."""

    public: bool | None = None
    """Whether the group is public or private."""

    member_list_visibility: Visibility | None = None
    """The visibility of the member list. Alias to 'memberListVisibility'."""

    repository: Repository | None = None
    """The repository the group belongs to."""

    created: datetime | None = None
    """The creation timestamp of the group."""

    last_modified: datetime | None = None
    """The last modification timestamp of the group. Alias to 'lastModified'."""

    users_count: int | None = None
    """The number of users in the group. Alias to 'usersCount'."""

    _users: list[UserSummary] | None = PrivateAttr(None)
    """The users in the group."""

    _admins: list[UserSummary] | None = PrivateAttr(None)
    """The administrators of the group."""

    _type: t.Literal["group", "role"] | None = PrivateAttr("group")
    """The type of the group, either 'group' or 'role'."""

    model_config = camel_case_config | forbid_extra_config
    """Configure to use camelCase aliasing and forbid extra fields."""

    @classmethod
    def from_map_group(cls, group: MapGroup) -> GroupDetail:
        """Create a GroupDetail instance from a MapGroup instance.

        Args:
            group (MapGroup): The MapGroup instance to convert.

        Returns:
            GroupDetail: The created GroupDetail instance.
        """
        from server.services import repositories  # noqa: PLC0415
        from server.services.utils import detect_affiliation  # noqa: PLC0415

        detected = detect_affiliation(group.id)
        repository_id = detected.repository_id if detected else None
        user_defined_id = (
            detected.user_defined_id if detected and detected.type == "group" else None
        )
        if repository_id and (repo := repositories.get_by_id(repository_id)):
            repository = Repository(id=repository_id, service_name=repo.service_name)
        else:
            repository = None
        # fmt: off
        users = None if group.members is None else [
            UserSummary(id=member.value, user_name=member.display)
            for member in group.members
            if member.type == "User"
        ]
        admins = None if group.administrators is None else [
            UserSummary(id=admin.value, user_name=admin.display)
            for admin in group.administrators
        ]
        # fmt: on

        group_detail = cls(
            id=group.id,
            user_defined_id=user_defined_id,
            display_name=group.display_name or "",
            description=group.description,
            repository=repository,
            public=group.public,
            member_list_visibility=group.member_list_visibility,
            created=group.meta.created if group.meta else None,
            last_modified=group.meta.last_modified if group.meta else None,
            users_count=len(users) if users else None,
        )
        group_detail._users = users
        group_detail._admins = admins
        group_detail._type = detected.type if detected else None

        return group_detail

    def to_map_group(self) -> MapGroup:
        """Convert this GroupDetail instance to a MapGroup instance.

        Returns:
            MapGroup: The created MapGroup instance.
        """
        group = MapGroup(
            id=self.id, display_name=self.display_name, description=self.description
        )
        if self.public is not None:
            group.public = self.public
        if self.member_list_visibility is not None:
            group.member_list_visibility = self.member_list_visibility
        if self._users:
            group.members = [
                MemberUser(type="User", value=user.id) for user in self._users
            ]
        if self._admins:
            group.administrators = [
                Administrator(value=admin.id) for admin in self._admins
            ]
        return group


class Repository(BaseModel):
    """Model for summary Repository information in mAP Core API."""

    id: str
    """The unique identifier for the repository."""

    service_name: str | None = None
    """The name of the repository. Alias to 'serviceName'."""

    model_config = camel_case_config | forbid_extra_config
    """Configure to use camelCase aliasing and forbid extra fields."""
