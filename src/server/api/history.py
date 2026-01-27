#
# Copyright (C) 2025 National Institute of Informatics.
#

"""API router for history endpoints."""

import typing as t

from uuid import UUID

from flask import Blueprint, Response, send_file
from flask_login import login_required
from flask_pydantic import validate

from server.api.helper import roles_required
from server.api.schemas import ErrorResponse, HistoryPublic
from server.entities.history_detail import (
    DownloadHistory,
    HistoryDataFilter,
    HistoryQuery,
    UploadHistory,
)
from server.services import history


bp = Blueprint("history", __name__)


@bp.get("/<tub>/filter-options")
@login_required
@roles_required("system_admin", "repository_admin")
@validate()
def filter_options(
    tub: t.Literal["download", "upload"],
) -> tuple[HistoryDataFilter, int] | tuple[ErrorResponse, int]:
    """Get filter options for history data.

    Args:
        tub (t.Literal["download", "upload"]): Type of history (download or upload)

    Returns:
        HistoryDataFilter: if successful and status code 200
        ErrorResponse: if an error occurs  and status code 500
    """
    try:
        history_filter = history.get_filters(tub)
    except ValueError:
        return ErrorResponse(code="", message=""), 500

    return history_filter, 200


@bp.get("/<string:tub>")
@login_required
@roles_required("system_admin", "repository_admin")
@validate()
def get(
    query: HistoryQuery, tub: t.Literal["download", "upload"]
) -> tuple[DownloadHistory | UploadHistory | ErrorResponse, int]:
    """Get history data.

    Args:
        query (HistoryQuery): Query parameters for filtering history data
        tub (t.Literal["download", "upload"]): Type of history (download or upload)

    Returns:
        DownloadHistory | UploadHistory: if successful and status code 200
        ErrorResponse: if a connection error occurs and status code 503
    """
    try:
        if tub == "download":
            history_data = history.get_download_history_data(query)
            result = DownloadHistory(download_history_data=history_data)
        else:
            history_data = history.get_upload_history_data(query)
            result = UploadHistory(upload_history_data=history_data)
    except ConnectionError:
        return ErrorResponse(code="", message=""), 503
    return result, 200


@bp.put("/<tub>/<history_id>/public-status")
@login_required
@roles_required("system_admin", "repository_admin")
@validate()
def public_status(
    tub: t.Literal["download", "upload"], history_id: UUID, body: HistoryPublic
) -> tuple[bool, int]:
    """Update the public status of a history item.

    Args:
        tub (t.Literal["download", "upload"]): Type of history (download or upload)
        history_id (UUID): Unique identifier of the history item
        body (HistoryPublic): Request body containing the new public status

    Returns:
        bool: True if the update was successful, False otherwise
        int: HTTP status code
    """
    result: bool = history.update_public_status(
        tub=tub, history_id=history_id, public=body.public
    )

    return result, 200


@bp.get("/files/<file_id>")
@login_required
@roles_required("system_admin", "repository_admin")
@validate()
def files(file_id: UUID) -> Response:
    """Download a file associated with a history item.

    Args:
        file_id (UUID): Unique identifier of the file to be downloaded

    Returns:
        Response: Flask response object to send the file
    """
    file_path = history.get_file_path(file_id)

    return send_file(path_or_file=file_path)
