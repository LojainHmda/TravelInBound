import os
import pytest

os.environ['FLASK_ENV'] = 'testing'

from app import create_app
from app.extensions import db as _db


@pytest.fixture(scope='session')
def app():
    application = create_app()
    application.config['TESTING'] = True
    application.config['WTF_CSRF_ENABLED'] = False
    with application.app_context():
        _db.create_all()
        yield application
        _db.session.remove()


@pytest.fixture(scope='function')
def client(app):
    c = app.test_client()
    # Ensure the client starts unauthenticated by clearing any session
    with c:
        pass  # Fresh client with no cookies
    return c


@pytest.fixture(scope='function')
def db_session(app):
    """Provide a DB session scoped to the test function."""
    with app.app_context():
        yield _db.session
        _db.session.remove()


@pytest.fixture(scope='function')
def admin_user(app):
    from app.models.user import User
    with app.app_context():
        user = User.query.filter_by(username='admin').first()
        if not user:
            user = User(id=1, username='admin', email='admin@test.com',
                        role='admin', active=True)
            user.set_password('admin123')
            _db.session.add(user)
            _db.session.commit()
        return user


@pytest.fixture(scope='function')
def auth_client(client, admin_user):
    """Client pre-authenticated as admin."""
    client.post('/auth/login', data={'username': 'admin', 'password': 'admin123'})
    return client
