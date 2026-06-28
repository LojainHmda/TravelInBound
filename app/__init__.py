import os
import logging

from flask import Flask, request

from app.api_exemptions import is_csrf_exempt

# Re-export extension singletons so `from app import db` keeps working
# across routes/services that haven't been migrated to app.extensions yet.
from app.extensions import db, login_manager, csrf  # noqa: F401


def create_app():
    """Application factory."""
    try:
        from dotenv import load_dotenv
        _root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        load_dotenv(os.path.join(_root, '.env'), override=True)
    except ImportError:
        pass

    app = Flask(__name__)

    # Load environment-based config
    from app.config import get_config
    app.config.from_object(get_config())

    # Validate DB URL is set
    if not app.config.get('SQLALCHEMY_DATABASE_URI'):
        env = os.environ.get('FLASK_ENV', 'development')
        key = 'DATABASE_URL_TEST' if env != 'production' else 'DATABASE_URL'
        raise RuntimeError(f"Missing required env var: {key}")

    # Warn if production points at non-postgres
    db_uri = app.config['SQLALCHEMY_DATABASE_URI']
    if not db_uri.startswith(('postgresql://', 'postgres://')) and os.environ.get('K_SERVICE'):
        import sys
        print('PRODUCTION WARNING: DATABASE_URL not PostgreSQL — data will not persist on Cloud Run!', file=sys.stderr)

    # Suppress noisy CSRF log
    logging.getLogger('flask_wtf.csrf').setLevel(logging.ERROR)

    # Init extensions
    from app.extensions import db, login_manager, csrf, migrate
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'warning'
    csrf.init_app(app)

    # CSRF exemption hook
    original_protect = csrf.protect
    def custom_protect():
        if is_csrf_exempt(request):
            return
        return original_protect()
    csrf.protect = custom_protect

    # User loader
    @login_manager.user_loader
    def load_user(user_id):
        from app.models.user import User
        return User.query.get(int(user_id))

    # Jinja filters & globals
    @app.template_filter('from_json')
    def from_json_filter(value):
        import json
        try:
            return json.loads(value)
        except (ValueError, TypeError):
            return {}

    @app.template_filter('pprint')
    def pprint_filter(value):
        import pprint
        return pprint.pformat(value)

    _static_version_cache: dict[str, str] = {}
    is_dev = app.config.get('DEBUG', False)

    def static_version(filename):
        try:
            if not is_dev:
                cached = _static_version_cache.get(filename)
                if cached is not None:
                    return cached
            path = os.path.join(app.static_folder or '', filename)
            ver = str(int(os.path.getmtime(path)))
            if not is_dev:
                _static_version_cache[filename] = ver
            return ver
        except Exception:
            return '1'

    app.jinja_env.globals['static_version'] = static_version

    from app.models.inbound import itinerary_row_guide_supplier_id_list
    app.jinja_env.globals['itinerary_row_guide_ids'] = itinerary_row_guide_supplier_id_list

    with app.app_context():
        # Import all models so SQLAlchemy registers them
        from app.models import User                       # noqa: F401
        from app.models.invoice import Invoice            # noqa: F401
        from app.models.expense_sheet import GuideExpenseSheet, GuidePaymentSheet  # noqa: F401

        # Register blueprints
        from app.routes.main import main_bp
        app.register_blueprint(main_bp)

        from app.routes.booking import booking_bp
        app.register_blueprint(booking_bp, url_prefix='/booking')

        from app.routes.customer import customer_bp
        app.register_blueprint(customer_bp)

        from app.routes.confirmation import confirmation_bp
        app.register_blueprint(confirmation_bp)

        from app.routes.voucher import voucher_bp
        app.register_blueprint(voucher_bp)

        from app.routes.api import api_bp
        app.register_blueprint(api_bp)
        csrf.exempt(api_bp)

        for module in ('app.routes.api.search', 'app.routes.api.chat', 'app.routes.api.invoice'):
            try:
                import importlib
                mod = importlib.import_module(module)
                blueprint = getattr(mod, module.split('.')[-1] + '_api', None) or \
                            getattr(mod, 'search_api', None) or \
                            getattr(mod, 'chat_api', None) or \
                            getattr(mod, 'invoice_api', None)
                if blueprint:
                    app.register_blueprint(blueprint, url_prefix='')
            except ImportError:
                pass

        from app.routes.finance import finance
        app.register_blueprint(finance)

        from app.routes.auth import auth_bp
        app.register_blueprint(auth_bp, url_prefix='/auth')

        from app.routes.tools import tools_bp
        app.register_blueprint(tools_bp)

        from app.routes.inbound import inbound_bp
        app.register_blueprint(inbound_bp)

        # Schema creation + upgrade (dev only — prod uses flask db upgrade)
        try:
            db.create_all()
        except Exception as e:
            app.logger.error(f'db.create_all() error: {e}')

        _run_schema_upgrades(app, db)
        _sync_sequences(app, db, db_uri)
        _bootstrap_admin(app, db, db_uri)

    return app


def _run_schema_upgrades(app, db):
    """Safe ALTER TABLE additions for columns added after initial schema."""
    import traceback
    from sqlalchemy import text, inspect

    db_uri = app.config['SQLALCHEMY_DATABASE_URI']
    is_pg = db_uri.startswith(('postgresql://', 'postgres://'))
    dt_type = 'TIMESTAMP' if is_pg else 'DATETIME'

    try:
        with db.engine.connect() as conn:
            inspector = inspect(db.engine)

            def _add_col(table, col, col_type):
                if is_pg:
                    conn.execute(text(f'ALTER TABLE {table} ADD COLUMN IF NOT EXISTS {col} {col_type}'))
                else:
                    conn.execute(text(f'ALTER TABLE {table} ADD COLUMN {col} {col_type}'))
                conn.commit()

            tables = [t.lower() if is_pg else t for t in inspector.get_table_names()]

            if 'user' in tables:
                existing = {c['name'] for c in inspector.get_columns('user')}
                for col, typ in [
                    ('first_name', 'VARCHAR(64)'), ('last_name', 'VARCHAR(64)'),
                    ('profile_image_url', 'VARCHAR(255)'), ('role', 'VARCHAR(50)'),
                    ('active', 'INTEGER'), ('created_at', dt_type), ('updated_at', dt_type),
                ]:
                    if col not in existing:
                        _add_col('"user"', col, typ)

            if 'hotel_room' in tables:
                existing = {c['name'] for c in inspector.get_columns('hotel_room')}
                if 'room_category' not in existing:
                    _add_col('hotel_room', 'room_category', 'VARCHAR(100)')

            if 'customer' in tables:
                existing = {c['name'] for c in inspector.get_columns('customer')}
                for col, typ in [
                    ('payment_terms', 'VARCHAR(100)'), ('bank_name', 'VARCHAR(120)'),
                    ('bank_account', 'VARCHAR(255)'), ('cliq_alias', 'VARCHAR(255)'),
                ]:
                    if col not in existing:
                        _add_col('customer', col, typ)

            if 'inbound_request' in tables:
                existing = {c['name'] for c in inspector.get_columns('inbound_request')}
                for col, typ in [
                    ('restaurant_voucher_note', 'TEXT'), ('hotel_voucher_note', 'TEXT'),
                    ('advance_expense_sheet_data', 'TEXT'), ('closing_guide_payment_sheet_data', 'TEXT'),
                    ('admin_invoice_data', 'TEXT'), ('customer_invoice_data', 'TEXT'),
                    ('pending_invoice_queue', 'BOOLEAN NOT NULL DEFAULT FALSE' if is_pg else 'BOOLEAN DEFAULT 0'),
                    ('deleted_reason', 'TEXT'), ('parent_request_id', 'INTEGER'),
                    ('link_type', 'VARCHAR(20)'), ('link_note', 'TEXT'),
                ]:
                    if col not in existing:
                        _add_col('inbound_request', col, typ)
    except Exception as e:
        app.logger.error(f'Schema upgrade failed: {e}\n{traceback.format_exc()}')


def _sync_sequences(app, db, db_uri):
    """Fix PostgreSQL sequences after explicit ID inserts."""
    if not db_uri.startswith(('postgresql://', 'postgres://')):
        return
    from sqlalchemy import text
    tables = [
        'inbound_request', 'itinerary_row', 'inbound_hotel', 'hotel_room',
        'inbound_transport', 'inbound_meal', 'inbound_guide', 'inbound_cash_expense',
        'arrival_departure', 'arrival_batch', 'departure_batch', 'inbound_representative',
        'inbound_optional', 'inbound_quotation', 'inbound_quotation_item',
        'quotation_attachment', 'inbound_document', 'supplier', 'booking',
        'service_item', 'customer', 'invoice',
    ]
    try:
        with db.engine.connect() as conn:
            for tbl in tables:
                try:
                    q = f'"{tbl}"' if tbl == 'user' else tbl
                    conn.execute(text(
                        f"SELECT setval(pg_get_serial_sequence('{q}', 'id'), "
                        f"COALESCE((SELECT MAX(id) FROM {q}), 1))"
                    ))
                    conn.commit()
                except Exception:
                    pass
    except Exception as e:
        app.logger.warning(f'Sequence sync (non-fatal): {e}')


def _bootstrap_admin(app, db, db_uri):
    """Ensure admin user id=1 exists."""
    try:
        from app.models.user import User, create_test_data
        if User.query.get(1) is None:
            app.logger.info('Bootstrapping admin user (id=1)')
            create_test_data()
            if db_uri.startswith(('postgresql://', 'postgres://')):
                from sqlalchemy import text
                with db.engine.connect() as conn:
                    conn.execute(text(
                        "SELECT setval(pg_get_serial_sequence('\"user\"', 'id'), "
                        "COALESCE((SELECT MAX(id) FROM \"user\"), 1))"
                    ))
                    conn.commit()
    except Exception as e:
        app.logger.warning(f'Admin bootstrap (non-fatal): {e}')
