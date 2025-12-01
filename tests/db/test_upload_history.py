import uuid

from typing import get_args

import pytest

from psycopg.errors import CheckViolation
from sqlalchemy.exc import IntegrityError

from server.db.upload_history import UploadHistory


def test_create_upload_history_record(app, db):
    record = UploadHistory()
    record.user_id = uuid.uuid4()
    record.file_uid = uuid.uuid4()
    record.filename = "testfile.txt"
    record.status = "P"  # In Progress

    db.session.add(record)
    db.session.commit()

    fetched_record = db.session.get(UploadHistory, record.id)
    assert fetched_record is not None
    assert fetched_record.id == 1
    assert isinstance(fetched_record.user_id, uuid.UUID)
    assert fetched_record.user_id == record.user_id
    assert isinstance(fetched_record.file_uid, uuid.UUID)
    assert fetched_record.file_uid == record.file_uid
    assert fetched_record.filename == "testfile.txt"
    assert fetched_record.status == "P"


@pytest.mark.parametrize("status", get_args(UploadHistory.Status.__value__))
def test_upload_history_status_choices(app, db, status):
    record = UploadHistory()
    record.user_id = uuid.uuid4()
    record.file_uid = uuid.uuid4()
    record.filename = "testfile.txt"
    record.status = status

    db.session.add(record)
    db.session.commit()

    fetched_record = db.session.get(UploadHistory, record.id)
    assert fetched_record is not None
    assert fetched_record.status == status


def test_invalid_status_raises_error(app, db):
    invalid_record = UploadHistory()
    invalid_record.user_id = uuid.uuid4()
    invalid_record.file_uid = uuid.uuid4()
    invalid_record.filename = "invalidstatus.txt"
    invalid_record.status = "X"  # pyright: ignore[reportAttributeAccessIssue]
    db.session.add(invalid_record)

    with pytest.raises(IntegrityError) as exc_info:
        db.session.commit()

    assert isinstance(exc_info.value.orig, CheckViolation)
    assert "ck_upload_history_status" in str(exc_info.value.orig)
