"""
Gunicorn WSGI server configuration
For details about configuration precedence,
please see: https://docs.gunicorn.org/en/stable/configure.html
"""
import multiprocessing
import os
from app import set_app


def parse_bool(value: str | None) -> bool:
    """
    Parse a boolean value from a string.
    If value is None or if it is not equal to "true" string
    It will return False.
    """
    if value and str(value).lower() == "true":
        return True
    return False


debug = parse_bool(os.environ.get("DEBUG", True))
set_app(debug=debug)

host = os.environ.get("HOST", "0.0.0.0")
port = int(os.environ.get("PORT", 8000))
bind = f"{host}:{port}"
workers = multiprocessing.cpu_count() * 2 + 1
