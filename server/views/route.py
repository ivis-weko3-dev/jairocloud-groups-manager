import typing as t

from server.views.auth import bp as auth_bp
from server.views.users import bp as users_bp

if t.TYPE_CHECKING:
    from flask import Flask


def create_blueprints(app: Flask):
    """Register all blueprints with the Flask application."""
    app.register_blueprint(auth_bp)
    app.register_blueprint(users_bp)
