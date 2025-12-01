from typing import cast

from flask import current_app
from flask_sqlalchemy import SQLAlchemy
from werkzeug.local import LocalProxy

db = cast(SQLAlchemy, LocalProxy(lambda: current_app.extensions["sqlalchemy"]))
"""Database instance proxy."""
