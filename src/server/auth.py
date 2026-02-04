#
# Copyright (C) 2025 National Institute of Informatics.
#

"""helper for api decorator."""

import typing as t

from datetime import UTC, datetime

from flask import session
from flask_login import LoginManager, current_user

from server.config import config
from server.datastore import account_store
from server.entities.login_user import LoginUser


login_manager = LoginManager()


def refresh_session() -> None:
    """Extend the TTL of the Redis login state for login users."""
    if not current_user.is_authenticated:
        return

    session_id: str = t.cast("LoginUser", current_user).session_id or session["_id"]

    key = build_account_store_key(session_id)
    login_date_raw = account_store.hget(key, "loginDate")
    if not isinstance(login_date_raw, str):
        return

    login_date = datetime.fromisoformat(login_date_raw)
    time_since_login = datetime.now(UTC) - login_date
    if time_since_login.total_seconds() > config.SESSION.absolute_lifetime:
        account_store.delete(key)
        return

    session_ttl: int = config.SESSION.sliding_lifetime
    if session_ttl >= 0:
        account_store.expire(key, session_ttl)


@login_manager.user_loader
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
    raw = account_store.hgetall(key)  # pyright: ignore[reportAssignmentType]
    if not raw:
        return None

    data = {
        k.decode("utf-8"): v.decode("utf-8")
        for k, v in t.cast("dict[bytes, bytes]", raw).items()
    }

    if data["id"] != user_id:
        return None

    return LoginUser.model_validate(data | {"session_id": session_id})


def build_account_store_key(session_id: str) -> str:
    """Build the account_store key.

    Args:
        session_id(str):Logged-in user's session ID

    Returns:
        str:Session information key for account_store
    """
    return f"{config.REDIS.key_prefix}_login_{session_id}"
