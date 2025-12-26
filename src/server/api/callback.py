#
# Copyright (C) 2025 National Institute of Informatics.
#

"""API router for callback endpoints."""

from flask import Blueprint, Response

bp = Blueprint("callback", __name__)


@bp.get("/auth-code")
def auth_code() -> Response:
    """Handle the authorization code callback.

    This endpoint receives the authorization code from the
    mAP Core Authorization Server after user consent.

    Returns:
        Response: An empty response with status 204.
    """
    return Response(status=204)
