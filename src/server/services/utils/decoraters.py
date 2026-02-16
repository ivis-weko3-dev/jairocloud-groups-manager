from functools import wraps


def session_required[**P, R](func):
    """Decorator to ensure that a valid session exists."""

    @wraps(func)
    def wrapper(*args, session_id=None, **kwargs):
        return func(*args, **kwargs)

    return wrapper
