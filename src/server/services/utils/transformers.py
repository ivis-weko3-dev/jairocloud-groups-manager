#
# Copyright (C) 2025 National Institute of Informatics.
#

"""Services to provide resource transformers for entities."""

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
from server.exc import InvalidFormError, SystemAdminNotFound


if t.TYPE_CHECKING:
    from server.entities.repository_detail import RepositoryDetail


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
        InvalidFormError: If the repository cannot be converted to a MapService.
        SystemAdminNotFound: If no administrators are provided.
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

    service = MapService(
        id=repository.service_id or resolve_service_id(repository_id=repository_id),
        service_name=repository.service_name,
        service_url=repository.service_url,
    )
    if repository.active is not None:
        service.suspended = repository.active is False

    if not repository.entity_ids:
        error = "At least one entity ID is required to create a repository."
        raise InvalidFormError(error)

    service.entity_ids = [ServiceEntityID(value=eid) for eid in repository.entity_ids]

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
