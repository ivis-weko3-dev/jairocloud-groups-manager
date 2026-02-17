#
# Copyright (C) 2025 National Institute of Informatics.
#

"""Services to provide resource transformers for entities."""

# ruff: noqa: SLF001

import typing as t

from server.config import config
from server.const import USER_ROLES
from server.entities.map_group import (
    Administrator as GroupAdministrator,
    MapGroup,
)
from server.entities.map_service import (
    Administrator,
    Group as MapServiceGroup,
    MapService,
    ServiceEntityID,
)
from server.entities.repository_detail import RepositoryDetail
from server.exc import InvalidFormError, SystemAdminNotFound

from .affiliations import detect_affiliation
from .resolvers import resolve_repository_id, resolve_service_id
from .search_queries import make_criteria_object


def prepare_service(
    repository: RepositoryDetail, administrators: set[str]
) -> MapService:
    """Prepare MapService instance from RepositoryDetail to create.

    Args:
        repository (RepositoryDetail): The repository detail to be converted.
        administrators (set[str]): The set of administrator user IDs.

    Returns:
        MapService: The converted MapService instance.

    Raises:
        SystemAdminNotFound: If no administrators are provided.
    """
    service = validate_repository_to_map_service(repository)
    repository_id = resolve_repository_id(service_id=service.id)

    if not administrators:
        error = "At least one administrator is required to create a repository."
        raise SystemAdminNotFound(error)

    service.administrators = [
        Administrator(value=user_id) for user_id in administrators
    ]
    service.groups = [
        MapServiceGroup(
            value=config.GROUPS.id_patterns[role].format(repository_id=repository_id)
        )
        for role in USER_ROLES
    ]
    return service


def prepare_role_groups(
    repository_id: str, service_name: str, administrators: set[str]
) -> list[MapGroup]:
    """Prepare role groups for a repository creation.

    Args:
        repository_id (str): The ID of the repository.
        service_name (str): The name of the service.
        administrators (set[str]): The set of administrator user IDs.

    Returns:
        list[MapGroup]: A list of MapGroup instances representing the role groups.
    """
    role_groups = []
    for role in USER_ROLES:
        if role == USER_ROLES.SYSTEM_ADMIN:
            continue  # System admin group is not necessary.

        id_pattern = config.GROUPS.id_patterns[role]
        name_pattern = config.GROUPS.name_patterns[role]
        role_groups.append(
            MapGroup(
                id=id_pattern.format(repository_id=repository_id),
                display_name=name_pattern.format(repository_name=service_name),
                public=False,
                member_list_visibility="Private",
                administrators=[
                    GroupAdministrator(value=user_id) for user_id in administrators
                ],
            )
        )
    return role_groups


def make_repository_detail(
    service: MapService, *, more_detail: bool = False
) -> RepositoryDetail:
    """Convert a MapService instance to a RepositoryDetail instance.

    Args:
        service (MapService): The MapService instance to convert.
        more_detail (bool): Whether to include more details such as groups and users.

    Returns:
        RepositoryDetail: The converted RepositoryDetail instance.
    """
    repository_id = resolve_repository_id(service_id=service.id)

    entity_ids = None
    if service.entity_ids:
        entity_ids = [eid.value for eid in service.entity_ids]

    repository = RepositoryDetail(
        id=repository_id,
        service_id=service.id,
        service_name=service.service_name,
        service_url=service.service_url,
        active=not service.suspended if service.suspended is not None else None,
        entity_ids=entity_ids,
    )

    if not more_detail or not service.groups:
        return repository

    from server.services import users  # noqa: PLC0415

    valid_groups = [
        (g.value, detected)
        for g in service.groups
        if (detected := detect_affiliation(g.value)) is not None
    ]
    detected_rolegroups = [i for i, g in valid_groups if g.type == "role"]
    detected_groups = [i for i, g in valid_groups if g.type == "group"]

    groups_count = len(detected_groups)
    users_count = users.count(make_criteria_object("users", g=detected_groups))

    repository.groups_count = groups_count
    repository.users_count = users_count
    repository.created = service.meta.created if service.meta else None
    repository._groups = detected_groups
    repository._rolegroups = detected_rolegroups
    repository._admins = (
        [admin.value for admin in service.administrators]
        if service.administrators
        else None
    )

    return repository


def validate_repository_to_map_service(repository: RepositoryDetail) -> MapService:
    """Validate the RepositoryDetail instance and convert it to a MapService instance.

    Args:
        repository (RepositoryDetail): The RepositoryDetail instance to convert.

    Returns:
        MapService: The converted MapService instance.

    Raises:
        InvalidFormError:  If the repository cannot be converted to a MapService.
    """
    repository_id = repository.id
    service_url = repository.service_url

    if repository.service_name is None:
        error = "Service name is required to create a repository."
        raise InvalidFormError(error)

    if service_url is None:
        error = "Service URL is required to create a repository."
        raise InvalidFormError(error)

    if repository_id is None:
        fqdn = service_url.host
        repository_id = resolve_repository_id(fqdn=fqdn) if fqdn else None

    if repository_id is None:
        error = "Service URL must contain a valid host."
        raise InvalidFormError(error)

    max_url_length = config.REPOSITORIES.max_url_length
    without_scheme_url = str(service_url).replace(f"{service_url.scheme}://", "")
    if len(without_scheme_url) > max_url_length:
        error = "Service URL is too long."
        raise InvalidFormError(error)

    if not repository.entity_ids:
        error = "At least one entity ID is required to create a repository."
        raise InvalidFormError(error)

    repository.service_id = resolve_service_id(repository_id=repository_id)
    return make_map_service(repository)


def make_map_service(repository: RepositoryDetail) -> MapService:
    """Convert a RepositoryDetail instance to a MapService instance.

    Args:
        repository (RepositoryDetail): The RepositoryDetail instance to convert.

    Returns:
        MapService: The converted MapService instance.
    """
    service_id = repository.service_id or resolve_service_id(
        repository_id=t.cast("str", repository.id)
    )
    service = MapService(
        id=service_id,
        service_name=repository.service_name,
        service_url=repository.service_url,
    )
    if repository.active is not None:
        service.suspended = repository.active is False
    if repository.entity_ids:
        service.entity_ids = [
            ServiceEntityID(value=eid) for eid in repository.entity_ids
        ]
    return service
