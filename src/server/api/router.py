#
# Copyright (C) 2025 National Institute of Informatics.
#

"""API router for the server application."""

import typing as t

from importlib import import_module
from pathlib import Path
from pkgutil import iter_modules

from flask import Blueprint

if t.TYPE_CHECKING:
    from flask import Flask


def create_blueprints(app: Flask) -> None:
    """Register blueprints for API routers.

    Args:
        app (Flask): The Flask application instance.

    """
    bp_api = Blueprint("api", __name__, url_prefix="/api")

    for _, name, _ in iter_modules([str(Path(__file__).parent)]):
        module = import_module(f"{__package__}.{name}")
        if hasattr(module, "bp"):
            bp_api.register_blueprint(module.bp)

    app.register_blueprint(bp_api)
