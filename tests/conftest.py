import pytest
from pathlib import Path

from flask import Flask
from sqlalchemy_utils import create_database, database_exists

import const
from config import RuntimeConfig
from db.shared import db as db_
from factory import create_app


def is_running_in_docker() -> bool:
    try:
        with open("/.dockerenv"):
            return True
    except FileNotFoundError:
        return False


@pytest.fixture(autouse=True)
def set_test_constants():
    const.MAP_USER_SCHEMA = "urn:ietf:params:scim:schemas:mace:example.jp:core:2.0:User"
    const.MAP_GROUP_SCHEMA = "urn:ietf:params:scim:schemas:mace:example.jp:core:2.0:Group"
    const.MAP_SERVICE_SCHEMA = "urn:ietf:params:scim:schemas:mace:example.jp:core:2.0:Service"


@pytest.fixture
def instance_path(tmp_path: Path) -> Path:
    return tmp_path / "instance"


@pytest.fixture
def test_config():
    return RuntimeConfig(
        SECRET_KEY="test_secret_key",
        POSTGRES_USER="mapuser",
        POSTGRES_HOST="postgres" if is_running_in_docker() else "localhost",
        POSTGRES_PORT=5432,
        POSTGRES_PASSWORD="mappass",
        POSTGRES_DB="test",
    )


@pytest.fixture
def base_app(instance_path, test_config):
    app = create_app(test_config)
    app.instance_path = instance_path
    app.config["TESTING"] = True

    return app


@pytest.fixture
def app(base_app: Flask):
    with base_app.app_context():
        yield base_app


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def db(app):
    url = db_.engine.url.render_as_string(hide_password=False)
    if not database_exists(url):
        create_database(url)
    else:
        db_.drop_all()
    db_.create_all()

    yield db_

    db_.session.remove()
    db_.drop_all()
