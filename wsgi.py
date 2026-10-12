"""WSGI entry point used by gunicorn in production (see deploy/Dockerfile)."""
from app import create_app

app = create_app()
