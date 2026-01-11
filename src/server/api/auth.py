#
# Copyright (C) 2025 National Institute of Informatics.
#

"""API router for authentication endpoints."""

from flask import Blueprint, Response, jsonify


bp = Blueprint("auth", __name__)


@bp.get("/check")
def check() -> tuple[Response, int]:
    """Check the authentication status.

    Returns:
        dict: Authentication status.
    """
    # NOTE: Placeholder to keep the session alive.
    return jsonify(id="anonymous", name="Anonymous User"), 200
