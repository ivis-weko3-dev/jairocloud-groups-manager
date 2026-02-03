#
# Copyright (C) 2025 National Institute of Informatics.
#

"""helper for api decorator."""

import typing as t

from datetime import UTC, datetime
from functools import wraps

from flask import abort, session
from flask_login import current_user

from server.config import config
from server.datastore import account_store
from server.entities.login_user import LoginUser
from server.services import permissions


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
        def decorated_view(*args: P.args, **kwargs: P.kwargs) -> R:
            """The actual view function that performs the role check.

            Args:
                *args (P.args): Positional arguments for the decorated function.
                **kwargs (P.kwargs): Keyword arguments for the decorated function.

            Returns:
                R: The result of the decorated function.
            """
            res = permissions.get_login_user_roles()
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

    key = build_account_store_key(session_id)
    login_date_raw = account_store.hget(key, "loginDate")
    if not isinstance(login_date_raw, str):
        return
    login_date = datetime.fromisoformat(login_date_raw)
    login_time = datetime.now(UTC) - login_date
    if login_time.total_seconds() > config.SESSION.absolute_lifetime:
        account_store.delete(key)
        return
    session_ttl: int = config.SESSION.sliding_lifetime
    if session_ttl >= 0:
        account_store.expire(key, session_ttl)


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

    key = build_account_store_key(session_id)
    raw = account_store.hgetall(key)
    data = {k.decode("utf-8"): v.decode("utf-8") for k, v in raw.items()}  # pyright: ignore[reportAttributeAccessIssue]
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


def build_account_store_key(session_id: str) -> str:
    """Build the account_store key.

    Args:
        session_id(str):Logged-in user's session ID

    Returns:
        str:Session information key for account_store
    """
    return f"{config.REDIS.key_prefix}_login_{session_id}"
