"""Smoke tests — verify the pytest foundation works end-to-end."""
from sqlalchemy import text


def test_create_app_returns_app(app):
    """create_app() must return a Flask application object."""
    from flask import Flask
    assert isinstance(app, Flask)


def test_db_connection(app, db_session):
    """DB connection works — execute a simple SELECT 1."""
    result = db_session.execute(text('SELECT 1')).scalar()
    assert result == 1


def test_root_redirects_unauthenticated(client):
    """Unauthenticated GET / must redirect (302) toward /auth/login."""
    response = client.get('/', follow_redirects=False)
    assert response.status_code == 302
    location = response.headers.get('Location', '')
    assert '/auth/login' in location
