"""
Gunicorn WSGI server configuration
For details about configuration precedence,
please see: https://docs.gunicorn.org/en/stable/configure.html
"""
import os
from app import set_app

debug: bool = bool(os.getenv("DEBUG"))
set_app(debug=debug)
host: str = os.environ.get("HOST", "0.0.0.0")
port: int = int(os.environ.get("PORT", 8002))
bind: str = f"{host}:{port}"
workers: int = 1
threads: int = 10
