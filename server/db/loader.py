from importlib import import_module
from pathlib import Path
from pkgutil import iter_modules

from flask_sqlalchemy.model import DefaultMeta


def load_models():
    """Dynamically import to register models with SQLAlchemy."""
    return {
        model.__tablename__: model
        for _, name, _ in iter_modules([Path(__file__).parent])
        for model in vars(import_module(f"{__package__}.{name}")).values()
        if isinstance(model, DefaultMeta)
    }
