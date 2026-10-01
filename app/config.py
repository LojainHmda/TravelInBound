import os
from urllib.parse import urlsplit


class Config:
    SECRET_KEY = os.environ.get('SESSION_SECRET', 'dev-key-change-in-production')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = None
    WTF_CSRF_SSL_STRICT = False
    WTF_CSRF_CHECK_DEFAULT = True
    WTF_CSRF_METHODS = ['POST', 'PUT', 'PATCH', 'DELETE']
    SESSION_COOKIE_SECURE = False
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = 3600
    TEMPLATES_AUTO_RELOAD = True

    # PostgreSQL pool settings (shared)
    _PG_ENGINE_OPTIONS = {
        'pool_recycle': 280,
        'pool_pre_ping': True,
        'pool_size': 5,
        'max_overflow': 10,
        'pool_timeout': 20,
        'connect_args': {
            'connect_timeout': 5,
            'keepalives': 1,
            'keepalives_idle': 30,
            'keepalives_interval': 10,
            'keepalives_count': 5,
            'options': '-c statement_timeout=30000',
        },
    }


    # Neon pooler-compatible engine options (no statement_timeout in connect_args)
    _PG_POOLER_ENGINE_OPTIONS = {
        'pool_recycle': 280,
        'pool_pre_ping': True,
        'pool_size': 5,
        'max_overflow': 10,
        'pool_timeout': 20,
        'connect_args': {
            'connect_timeout': 5,
            'keepalives': 1,
            'keepalives_idle': 30,
            'keepalives_interval': 10,
            'keepalives_count': 5,
        },
    }


def _first_env(*names):
    """Value of the first variable that is set. .env names the databases
    DATABASE_URL_LOCAL and DATABASE_URL_LIVE; the old names still work, and
    the Cloud Run service itself sets DATABASE_URL."""
    for name in names:
        if os.environ.get(name):
            return os.environ[name]
    return None


class DevelopmentConfig(Config):
    DEBUG = True
    TESTING = False
    SQLALCHEMY_DATABASE_URI = _first_env('DATABASE_URL_LOCAL', 'DATABASE_URL_TEST')
    SQLALCHEMY_ENGINE_OPTIONS = Config._PG_POOLER_ENGINE_OPTIONS
    SEND_FILE_MAX_AGE_DEFAULT = 0


class TestingConfig(Config):
    DEBUG = False
    TESTING = True
    SQLALCHEMY_DATABASE_URI = _first_env('DATABASE_URL_LOCAL', 'DATABASE_URL_TEST')
    SQLALCHEMY_ENGINE_OPTIONS = Config._PG_POOLER_ENGINE_OPTIONS
    WTF_CSRF_ENABLED = False


def pg_engine_options(url):
    """Neon's pooler rejects statement_timeout as a startup option, so pooler
    addresses get the pooler-safe set; direct addresses keep the timeout."""
    host = urlsplit(url or '').hostname or ''
    if '-pooler' in host:
        return Config._PG_POOLER_ENGINE_OPTIONS
    return Config._PG_ENGINE_OPTIONS


class ProductionConfig(Config):
    DEBUG = False
    TESTING = False
    SQLALCHEMY_DATABASE_URI = _first_env('DATABASE_URL', 'DATABASE_URL_LIVE')
    SQLALCHEMY_ENGINE_OPTIONS = pg_engine_options(SQLALCHEMY_DATABASE_URI)
    SESSION_COOKIE_SECURE = os.environ.get('SESSION_COOKIE_SECURE', 'False').lower() == 'true'


_config_map = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
}


def get_config():
    env = os.environ.get('FLASK_ENV', 'development').lower()
    return _config_map.get(env, DevelopmentConfig)
