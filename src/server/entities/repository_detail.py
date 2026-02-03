#
# Copyright (C) 2025 National Institute of Informatics.
#

"""Models for Repository entity for client side."""

import typing as t

from datetime import datetime

from pydantic import BaseModel, Field, HttpUrl, PrivateAttr

from server.config import config

from .common import camel_case_config, forbid_extra_config
from .map_service import (
    Administrator,
    Group as MapServiceGroup,
    MapService,
    ServiceEntityID,
)


class RepositoryDetail(BaseModel):
    """Model for detailed Repository information in mAP Core API."""

    _fqdn: str | None = PrivateAttr(None)
    """The fully qualified domain name of the repository."""

    id: str
    """The unique identifier for the repository."""

    service_name: str
    """The name of the repository. Alias to 'serviceName'."""

    service_url: HttpUrl | None = None
    """The URL of the service. Alias for 'serviceUrl'."""

    active: bool | None = None
    """Whether the service is active."""

    service_id: t.Annotated[
        str | None,
        Field(
            validation_alias="spConnectorId",
            serialization_alias="spConnectorId",
        ),
    ] = None
    """The ID of the corresponding resource. Alias to 'spConnectorId'."""
    entity_ids: list[str] | None = None
    """The entity IDs associated with the repository. Alias to 'entityIds'."""

    created: datetime | None = None
    """The creation timestamp of sp connector."""

    users_count: int | None = None
    """The number of users in the group. Alias to 'usersCount'."""

    groups_count: int | None = None
    """The number of user-defined groups in the repository. Alias to 'groupsCount'."""

    _groups: list[str] | None = PrivateAttr(None)
    """The user-defined groups in the repository."""

    _rolegroups: list[str] | None = PrivateAttr(None)
    """The role-type groups in the repository."""

    _admins: list[str] | None = PrivateAttr(None)
    """The administrators of the group."""

    model_config = camel_case_config | forbid_extra_config
    """Configure to use camelCase aliasing and forbid extra fields."""

    @classmethod
    def from_map_service(cls, service: MapService) -> RepositoryDetail:
        """Create a RepositoryDetail instance from a MapService instance.

        Args:
            service (MapService): The MapService instance to convert.

        Returns:
            RepositoryDetail: The created RepositoryDetail instance.
        """
        from server.services import users  # noqa: PLC0415
        from server.services.utils import (  # noqa: PLC0415
            detect_affiliation,
            make_criteria_object,
        )

        service_id = resolve_repository_id(service_id=service.id)

        detected_groups: list[str] | None = None
        detected_rolegroups: list[str] | None = None
        groups_count = None
        users_count = None
        if service.groups:
            valid_groups = [
                (g.value, detected)
                for g in service.groups
                if (detected := detect_affiliation(g.value)) is not None
            ]
            detected_rolegroups = [i for i, g in valid_groups if g.type == "role"]
            detected_groups = [i for i, g in valid_groups if g.type == "group"]

            groups_count = len(detected_groups)
            users_count = len(
                users.search(make_criteria_object("users", g=detected_groups)).resources
            )

        entity_ids: list[str] | None = None
        if service.entity_ids:
            entity_ids = [eid.value for eid in service.entity_ids]
        active = service.suspended is False if service.suspended is not None else None

        repository_detail = cls(
            id=service_id,
            service_name=service.service_name or "",
            service_url=service.service_url,
            active=active,
            service_id=service.id,
            entity_ids=entity_ids,
            groups_count=groups_count,
            users_count=users_count,
            created=service.meta.created if service.meta else None,
        )
        repository_detail._groups = detected_groups
        repository_detail._rolegroups = detected_rolegroups
        repository_detail._admins = (
            [admin.value for admin in service.administrators]
            if service.administrators
            else None
        )

        return repository_detail

    def to_map_service(self) -> MapService:
        """Convert RepositoryDetail to MapService instance.

        Returns:
            MapService: The converted MapService instance.
        """
        service = MapService(
            id=self.service_id or resolve_service_id(repository_id=self.id)
        )
        service.service_name = self.service_name
        service.service_url = self.service_url
        if self.active is not None:
            service.suspended = self.active is False
        if self.entity_ids:
            service.entity_ids = [ServiceEntityID(value=eid) for eid in self.entity_ids]
        if self._groups or self._rolegroups:
            service.groups = [MapServiceGroup(value=gid) for gid in self._groups or []]
            service.groups.extend([
                MapServiceGroup(value=gid) for gid in self._rolegroups or []
            ])
        if self._admins:
            service.administrators = [Administrator(value=uid) for uid in self._admins]
        return service


@t.overload
def resolve_repository_id(*, fqdn: str) -> str: ...
@t.overload
def resolve_repository_id(*, service_id: str) -> str: ...


def resolve_repository_id(
    *, fqdn: str | None = None, service_id: str | None = None
) -> str:
    """Resolve the repository ID from either FQDN or service ID.

    Args:
        fqdn (str): The fully qualified domain name.
        service_id (str): The service ID.

    Returns:
        str: The corresponding repository ID.

    Raises:
        ValueError: If neither `fqdn` nor `resource_id` is provided.
    """
    pattern = config.REPOSITORIES.id_patterns.sp_connecter
    prefix = pattern.split("{repository_id}")[0]
    suffix = pattern.split("{repository_id}")[1]

    if fqdn is not None:
        return fqdn.replace(".", "_").replace("-", "_")
    if service_id is not None:
        return service_id.removeprefix(prefix).removesuffix(suffix)

    error = "Either 'fqdn' or 'resource_id' must be provided."
    raise ValueError(error)


@t.overload
def resolve_service_id(*, fqdn: str) -> str: ...
@t.overload
def resolve_service_id(*, repository_id: str) -> str: ...


def resolve_service_id(
    *, fqdn: str | None = None, repository_id: str | None = None
) -> str:
    """Resolve the service ID from either FQDN or repository ID.

    Args:
        repository_id (str): The repository ID.
        fqdn (str): The fully qualified domain name.

    Returns:
        str: The corresponding service ID.

    Raises:
        ValueError: If neither `fqdn` nor `repository_id` is provided.
    """
    pattern = config.REPOSITORIES.id_patterns.sp_connecter

    if fqdn is not None:
        repository_id = resolve_repository_id(fqdn=fqdn)
    if repository_id is not None:
        return pattern.format(repository_id=repository_id)

    error = "Either 'fqdn' or 'repository_id' must be provided."
    raise ValueError(error)
