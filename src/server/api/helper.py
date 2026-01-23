#
# Copyright (C) 2025 National Institute of Informatics.
#

"""helper for api decorator."""

import typing as t

from functools import wraps

from flask import abort, session
from flask_login import current_user, login_required

from server.config import config
from server.datastore import account_store
from server.entities.login_user import LoginUser
from server.services import permission


P = t.ParamSpec("P")
R = t.TypeVar("R")


def roles_required(*roles: str) -> t.Callable[[t.Callable[P, R]], t.Callable[P, R]]:
    """Verify that the user has the requested role.

    Args:
        *roles: List of role names to grant access to.

    Returns:
        Callable: A decorator that returns a decorated function.
    """

    def decorator(func: t.Callable[P, R]) -> t.Callable[P, R]:
        """Inner decorator that handles the function wrapping.

        Args:
            func (t.Callable[P, R]): The function to be decorated.

        Returns:
            t.Callable[P, R]: The wrapped function with role-based access control.
        """

        @wraps(func)
        @login_required
        def decorated_view(*args: P.args, **kwargs: P.kwargs) -> R:
            """The actual view function that performs the role check.

            Args:
                *args (P.args): Positional arguments for the decorated function.
                **kwargs (P.kwargs): Keyword arguments for the decorated function.

            Returns:
                R: The result of the decorated function.
            """
            res = permission.get_login_user_roles()
            user_roles = res[0] if res else []

            if not any(role in user_roles for role in roles):
                abort(403)

            return func(*args, **kwargs)

        return decorated_view

    return decorator


def refresh_session() -> None:
    """Extend the TTL of the Redis login state for login users."""
    if not current_user.is_authenticated:
        return

    session_id = getattr(current_user, "_session_id", None) or session.get("_id")
    if not session_id:
        return

    key = f"{config.REDIS.key_prefix}_login_{session_id}"
    if config.REDIS.session_ttl >= 0:
        account_store.expire(key, config.REDIS.session_ttl)


def load_user(user_id: str) -> LoginUser | None:
    """Load a user from the session using the user_id.

    Args:
        user_id (str): The unique identifier for the user.

    Returns:
        LoginUser | None: The loaded user object if found, otherwise None.
    """
    if not user_id:
        return None

    session_id: str = session.get("_id")  # pyright: ignore[reportAssignmentType]
    if not session_id:
        return None

    key = f"{config.REDIS.key_prefix}_login_{session_id}"
    data = account_store.hgetall(key)
    if not isinstance(data, dict):
        return None

    if not data["eppn"] or data["eppn"] != user_id:
        return None

    user = LoginUser(
        eppn=data["eppn"],
        login_date=data["login_date"],
        user_name=data["user_name"],
        is_member_of=data["is_member_of"],
    )
    user._session_id = session_id  # noqa: SLF001
    return user
