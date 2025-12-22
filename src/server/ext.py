#
# Copyright (C) 2025 National Institute of Informatics.
#

"""Extension for the server application."""

import typing as t

from .api.router import create_blueprints
from .config import RuntimeConfig, setup_config
from .const import DEFAULT_CONFIG_PATH

if t.TYPE_CHECKING:
    from flask import Flask


class JAIROCloudGroupsManager:
    """Flask extension for JAIRO Cloud Groups management."""

    def __init__(
        self, app: Flask | None = None, config: RuntimeConfig | str | None = None
    ) -> None:
        """Initialize the MapWebUI application.

        Args:
            app (Flask | None): The Flask application instance.
            config (RuntimeConfig | str | None): The runtime configuration
                instance or path to the configuration file.

        """
        self.app = app
        self.config = config or DEFAULT_CONFIG_PATH

        if app is not None:
            self.init_app(app)

    def init_app(self, app: Flask) -> None:
        """Initialize the MapWebUI application with a Flask app.

        Args:
            app (Flask): The Flask application instance.

        """
        self.app = app
        self.init_config(app)

        create_blueprints(app)

        app.extensions["jairocloud-groups-manager"] = self

    def init_config(self, app: Flask) -> None:
        """Initialize the configuration for the Flask app.

        Args:
            app (Flask): The Flask application instance.

        """
        self.config = setup_config(self.config)

        app.config.from_object(self.config)
        app.config.from_prefixed_env()
