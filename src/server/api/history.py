#
# Copyright (C) 2025 National Institute of Informatics.
#

"""API router for history endpoints."""

import typing as t

from uuid import UUID

from flask import Blueprint, Response, send_file
from flask_pydantic import validate

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
@validate()
def filter_options(
    tub: t.Literal["download", "upload"],
) -> tuple[HistoryDataFilter, int] | tuple[ErrorResponse, int]:
    try:
        history_filter = history.get_filters(tub)
    except ValueError:
        return ErrorResponse(code="", message=""), 500

    return history_filter, 200


@bp.get("/<string:tub>")
@validate()
def get(
    query: HistoryQuery, tub: t.Literal["download", "upload"]
) -> tuple[DownloadHistory | UploadHistory | ErrorResponse, int]:
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
@validate()
def public_status(
    tub: t.Literal["download", "upload"], history_id: UUID, body: HistoryPublic
) -> tuple[bool, int]:
    """"""
    result: bool = history.update_public_status(
        tub=tub, history_id=history_id, public=body.public
    )

    return result, 200


@bp.get("/files/<file_id>")
@validate()
def files(file_id: UUID) -> Response:
    file_path = history.get_file_path(file_id)

    return send_file(path_or_file=file_path)
