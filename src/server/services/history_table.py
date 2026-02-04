#
# Copyright (C) 2025 National Institute of Informatics.
#

"""Services for managing history table."""

import typing as t

from datetime import UTC, datetime
from uuid import UUID  # noqa: TC003

from sqlalchemy import func
from sqlalchemy.orm import selectinload

from server.db import db
from server.db.history import Files, UploadHistory


def get_upload_by_id(history_id: UUID):
    return db.session.get(
        UploadHistory, history_id, options=[selectinload(UploadHistory.file)]
    )


def get_upload_results(history_id: UUID, attribute: str):
    result = (
        db.session
        .query(UploadHistory.results[attribute])
        .filter(UploadHistory.id == history_id)
        .first()
    )
    return result[0] if result else {}


def get_paginated_upload_results(
    history_id: UUID, offset: int, size: int, status_filter: list[str]
):
    if offset < 1 or size < 1:
        raise ValueError("Invalid offset or size")

    elements = func.jsonb_array_elements(
        UploadHistory.results["results"]
    ).column_valued("item")
    query = (
        db.session
        .query(elements)
        .select_from(UploadHistory)
        .filter(UploadHistory.id == history_id)
    )

    if status_filter:
        query = query.filter(elements.op("->>")("status").in_(status_filter))

    offset_val = (offset - 1) * size

    raw_results = query.limit(size).offset(offset_val).all()

    return [r[0] for r in raw_results]


def create_upload(file_id: UUID, results: dict, operator_id: str, operator_name: str):
    history_record = UploadHistory()
    history_record.file_id = file_id
    history_record.results = results
    history_record.operator_id = operator_id
    history_record.operator_name = operator_name
    db.session.add(history_record)
    db.session.commit()
    return history_record.id


def update_upload_status(
    history_id: UUID,
    status: t.Literal["P", "S", "F"],
    new_results: dict | None = None,
    file_id: UUID | None = None,
):
    obj = db.session.get(UploadHistory, history_id)
    if obj is None:
        return
    if new_results:
        obj.results = new_results

    obj.status = status
    now = datetime.now(UTC)
    if status == "P":
        obj.timestamp = now
    else:
        obj.end_timestamp = now

    if file_id:
        obj.file_id = file_id

    db.session.commit()


def get_history_by_file_id(file_id: UUID):
    return db.session.query(UploadHistory).filter_by(file_id=file_id).one()


def get_file_by_id(file_id: UUID):
    return db.session.query(Files).filter_by(id=file_id).one()


def delete_file_by_id(file_id: UUID):
    Files.query.filter(Files.id == file_id).delete()
    db.session.commit()


def create_file(file_path: str, file_content: dict, file_id: UUID | None = None):
    file_record = Files()
    if file_id:
        file_record.id = file_id
    file_record.file_path = str(file_path)
    file_record.file_content = file_content
    db.session.add(file_record)
    db.session.commit()
    return file_record.id
