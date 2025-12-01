from celery import Celery, Task
from flask import Flask

from .ext import MapWebUI


def create_app(config_object: object | str = "server.config.config"):
    app = Flask(__name__)
    app.config.from_prefixed_env()
    app.config.from_object(config_object)
    app.json.sort_keys = False  # pyright: ignore[reportAttributeAccessIssue]
    app.json.ensure_ascii = False  # pyright: ignore[reportAttributeAccessIssue]

    celery_init_app(app)
    _map_web_ui = MapWebUI(app)

    return app


def celery_init_app(app: Flask) -> Celery:
    class FlaskTask[**P, R](Task):
        def __call__(self, *args: P.args, **kwargs: P.kwargs) -> R:
            with app.app_context():
                return self.run(*args, **kwargs)

    celery_app = Celery(app.name, task_cls=FlaskTask)
    celery_app.config_from_object(app.config["CELERY"])
    celery_app.set_default()
    app.extensions["celery"] = celery_app
    return celery_app
