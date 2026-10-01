"""Production safety: pooler-safe DB options, no public seeding, public health check.

app.config reads the environment when first imported, so it is imported inside
the tests: importing it at collection time, before create_app() loads .env,
would leave the other tests without DATABASE_URL_LOCAL.
"""
POOLER = 'postgresql://u:p@ep-fancy-hill-b5rwffyj-pooler.c-7.us-east-2.aws.neon.tech/neondb?sslmode=require'
DIRECT = 'postgresql://u:p@ep-fancy-hill-b5rwffyj.c-7.us-east-2.aws.neon.tech/neondb?sslmode=require'


def _startup_options(url):
    from app.config import pg_engine_options
    return pg_engine_options(url)['connect_args'].get('options', '')


def test_pooler_address_gets_no_statement_timeout():
    # Neon's pooler refuses the connection when statement_timeout is passed
    from app.config import Config, pg_engine_options
    assert pg_engine_options(POOLER) is Config._PG_POOLER_ENGINE_OPTIONS
    assert 'statement_timeout' not in _startup_options(POOLER)


def test_direct_address_keeps_statement_timeout():
    from app.config import Config, pg_engine_options
    assert pg_engine_options(DIRECT) is Config._PG_ENGINE_OPTIONS
    assert 'statement_timeout' in _startup_options(DIRECT)


def test_pooler_in_password_does_not_count():
    from app.config import Config, pg_engine_options
    url = 'postgresql://u:x-pooler@ep-fancy-hill-b5rwffyj.c-7.us-east-2.aws.neon.tech/neondb'
    assert pg_engine_options(url) is Config._PG_ENGINE_OPTIONS


def test_missing_url_does_not_crash():
    from app.config import Config, pg_engine_options
    assert pg_engine_options(None) is Config._PG_ENGINE_OPTIONS


def test_init_data_is_disabled_in_production(client, monkeypatch):
    monkeypatch.setenv('FLASK_ENV', 'production')
    assert client.get('/auth/init-data').status_code == 404


def test_health_is_public_and_hides_internals(client):
    response = client.get('/health')
    assert response.status_code == 200
    body = response.get_json()
    assert body['db_connected'] is True
    assert 'inbound_request_columns' not in body
