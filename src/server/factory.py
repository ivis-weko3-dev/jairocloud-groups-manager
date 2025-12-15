import os

from celery import Celery, Task
from flask import Flask


def create_app(import_name: str) -> Flask:
    """Factory function to create and configure the Flask application.

    Args:
        import_name (str): The name of the application package.

    Returns:
        Flask: The configured Flask application instance.

    """
    app = Flask(import_name)
    app.config.from_mapping(
        CELERY={
            "broker_url": os.environ["CELERY_BROKER_URL"],
            "result_backend": os.environ["CELERY_RESULT_BACKEND"],
        },
    )
    app.config.from_prefixed_env()
    celery_init_app(app)

    return app


def celery_init_app(app: Flask) -> Celery:
    """Initialize and configure a Celery application with the Flask app context.

    Args:
        app (Flask): The Flask application instance.

    Returns:
        Celery: The configured Celery application instance.
    """

    class FlaskTask(Task):
        """Custom Celery Task class that wraps task execution in the Flask app context."""

        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery_app = Celery(app.name, task_cls=FlaskTask)
    celery_app.config_from_object(app.config["CELERY"])
    celery_app.set_default()
    app.extensions["celery"] = celery_app

    return celery_app
