import os
from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from app.api_exemptions import is_csrf_exempt

# Create the db instance with a model class inheriting from DeclarativeBase
class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)
login_manager = LoginManager()
csrf = CSRFProtect()

def create_app():
    """Application factory function"""
    # Load project .env so DATABASE_URL (e.g. PostgreSQL) is used when starting via start_server.py.
    # override=True makes .env authoritative over any stale shell env vars left from earlier sessions.
    try:
        from dotenv import load_dotenv
        _project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        load_dotenv(os.path.join(_project_root, '.env'), override=True)
    except ImportError:
        pass

    # Create the Flask app
    app = Flask(__name__)
    
    # Configure secret key and database URI
    app.secret_key = os.environ.get("SESSION_SECRET", "dev-key-for-testing")
    database_uri = os.environ.get("DATABASE_URL", "sqlite:///app.db")
    app.config["SQLALCHEMY_DATABASE_URI"] = database_uri

    # CRITICAL: Production (Cloud Run) must use DATABASE_URL with PostgreSQL.
    # SQLite on Cloud Run is ephemeral - data is lost on every container restart.
    if not database_uri.startswith(("postgresql://", "postgres://")) and os.environ.get("K_SERVICE"):
        import sys
        print("PRODUCTION WARNING: DATABASE_URL not set. Using SQLite - data will NOT persist on Cloud Run!", file=sys.stderr)
    
    # Configure engine options based on database type
    if database_uri.startswith(("postgresql://", "postgres://")):
        # PostgreSQL-specific configuration with improved timeout handling
        app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
            "pool_recycle": 280,
            "pool_pre_ping": True,  # Verify connections before using
            "pool_size": 5,  # Reduced from 10 to prevent connection exhaustion
            "max_overflow": 10,  # Reduced from 20
            "pool_timeout": 20,  # Reduced timeout to fail faster
            "connect_args": {
                "connect_timeout": 5,  # Reduced from 10 seconds
                "keepalives": 1,
                "keepalives_idle": 30,
                "keepalives_interval": 10,
                "keepalives_count": 5,
                "options": "-c statement_timeout=30000"  # 30 second query timeout
            }
        }
    else:
        # SQLite or other database configuration
        app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
            "pool_pre_ping": True,
            "pool_timeout": 20,  # Add timeout for SQLite too
            "connect_args": {
                "timeout": 20  # SQLite connection timeout
            }
        }
    
    # CSRF Configuration
    app.config['WTF_CSRF_ENABLED'] = True
    app.config['WTF_CSRF_TIME_LIMIT'] = None
    app.config['WTF_CSRF_SSL_STRICT'] = False
    app.config['WTF_CSRF_CHECK_DEFAULT'] = False  # Don't check by default, only when token is present
    app.config['WTF_CSRF_METHODS'] = ['POST', 'PUT', 'PATCH', 'DELETE']
    
    # Session Configuration
    # For Cloud Run, use filesystem (ephemeral) or consider Redis for production
    # Cloud Run has ephemeral filesystem, so sessions will be lost on container restart
    # For production, consider using Redis or signed cookies
    app.config['SESSION_TYPE'] = 'filesystem'
    app.config['SESSION_COOKIE_SECURE'] = os.environ.get('SESSION_COOKIE_SECURE', 'False').lower() == 'true'
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    app.config['SESSION_COOKIE_PATH'] = '/'
    app.config['SESSION_COOKIE_DOMAIN'] = None
    app.config['PERMANENT_SESSION_LIFETIME'] = 3600  # 1 hour

    # Development-only cache behavior: always reflect code/template/static changes.
    is_dev_env = os.environ.get('FLASK_ENV', '').lower() == 'development'
    is_debug_env = os.environ.get('FLASK_DEBUG', '').lower() in ('1', 'true', 'yes', 'on')
    if is_dev_env or is_debug_env:
        app.config['TEMPLATES_AUTO_RELOAD'] = True
        app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
        app.jinja_env.auto_reload = True
    
    # Suppress CSRF logging
    import logging
    logging.getLogger('flask_wtf.csrf').setLevel(logging.ERROR)
    
    # Initialize extensions
    db.init_app(app)
    # Initialize login_manager (required for Flask-Login even if authentication is disabled)
    # This prevents AttributeError when Flask-Login tries to access app.login_manager
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page'
    login_manager.login_message_category = 'warning'
    
    # Provide a user_loader to prevent Flask-Login errors (authentication disabled)
    @login_manager.user_loader
    def load_user(user_id):
        # Return None since authentication is disabled
        # The MockUser in context_processor handles template access
        return None
    
    # Initialize CSRF protection
    csrf.init_app(app)
    
    # Override CSRF protection to allow exemptions
    original_protect = csrf.protect
    def custom_protect():
        if is_csrf_exempt(request):
            return  # Skip CSRF protection for exempt routes
        return original_protect()
    csrf.protect = custom_protect
    
    # Register custom Jinja2 filters
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

    from app.models.inbound import itinerary_row_guide_supplier_id_list
    app.jinja_env.globals['itinerary_row_guide_ids'] = itinerary_row_guide_supplier_id_list

    # Static asset cache-buster: stable version based on file mtime, so browsers
    # keep CSS/JS cached across page loads and only re-download when the file actually changes.
    _static_version_cache: dict[str, str] = {}

    def static_version(filename):
        """Return a stable query-string version for a file under /static, based on its mtime.

        Falls back to '1' if the file is missing. Cached per-process so we don't stat the
        file on every request.
        """
        try:
            if not (is_dev_env or is_debug_env):
                cached = _static_version_cache.get(filename)
                if cached is not None:
                    return cached
            path = os.path.join(app.static_folder or '', filename)
            ver = str(int(os.path.getmtime(path)))
            if not (is_dev_env or is_debug_env):
                _static_version_cache[filename] = ver
            return ver
        except Exception:
            return '1'

    app.jinja_env.globals['static_version'] = static_version
    
    # Default user for templates - system always operates under user id=1 (no auth required)
    class MockUser:
        is_authenticated = True
        id = 1
        username = 'admin'
        role = 'admin'
        
        def can_access_finance(self):
            return True
        
        def is_admin(self):
            return True
    
    @app.context_processor
    def inject_mock_user():
        return {'current_user': MockUser()}
    
    with app.app_context():
        # Import models to ensure they are registered with SQLAlchemy
        from app.models import User
        from app.models.invoice import Invoice
        
        # Register blueprints
        from app.routes.main import main_bp
        app.register_blueprint(main_bp)
        
        from app.routes.booking import booking_bp
        app.register_blueprint(booking_bp, url_prefix='/booking')
        
        # Register supplier and customer blueprints - removed conflicting supplier routes
        
        from app.routes.customer import customer_bp
        app.register_blueprint(customer_bp)
        
        # Register confirmation blueprint
        from app.routes.confirmation import confirmation_bp
        app.register_blueprint(confirmation_bp)
        
        # Register voucher blueprint
        from app.routes.voucher import voucher_bp
        app.register_blueprint(voucher_bp)
        
        # Register main API blueprint with CSRF exemption for passport scanning
        from app.routes.api import api_bp
        app.register_blueprint(api_bp)
        csrf.exempt(api_bp)
        
        # Register other API modules if they exist
        try:
            from app.routes.api.search import search_api
            app.register_blueprint(search_api, url_prefix='')
        except ImportError:
            pass
            
        try:
            from app.routes.api.chat import chat_api
            app.register_blueprint(chat_api, url_prefix='')
        except ImportError:
            pass
            
        try:
            from app.routes.api.invoice import invoice_api
            app.register_blueprint(invoice_api, url_prefix='')
        except ImportError:
            pass
        
        # Register finance blueprint
        from app.routes.finance import finance
        app.register_blueprint(finance)
        
        # Register auth blueprint
        from app.routes.auth import auth_bp
        app.register_blueprint(auth_bp, url_prefix='/auth')
        
        # Register tools blueprint
        from app.routes.tools import tools_bp
        app.register_blueprint(tools_bp)
        
        # Register inbound tour operator blueprint
        from app.routes.inbound import inbound_bp
        app.register_blueprint(inbound_bp)
        
        # Login manager disabled - authentication removed
        # from app.models import User
        # @login_manager.user_loader
        # def load_user(user_id):
        #     return User.query.get(int(user_id))
        
        # Create database tables
        try:
            db.create_all()
        except Exception as e:
            app.logger.error(f"Database table creation error: {e}")
        
        # Add missing columns (safe ALTER TABLE for schema upgrades) - run BEFORE bootstrap
        import traceback
        is_pg = database_uri.startswith(("postgresql://", "postgres://"))
        try:
            with db.engine.connect() as conn:
                from sqlalchemy import text, inspect
                inspector = inspect(db.engine)
                dt_type = "TIMESTAMP" if is_pg else "DATETIME"

                def _run_alter(table, col, col_type):
                    if is_pg:
                        conn.execute(text(f'ALTER TABLE {table} ADD COLUMN IF NOT EXISTS {col} {col_type}'))
                    else:
                        conn.execute(text(f'ALTER TABLE {table} ADD COLUMN {col} {col_type}'))
                    conn.commit()

                tables = [t.lower() if is_pg else t for t in inspector.get_table_names()]
                # User table - add columns that may be missing from older schemas
                if "user" in tables:
                    user_cols = [col['name'] for col in inspector.get_columns('user')]
                    col_defs = [
                        ('first_name', 'VARCHAR(64)'), ('last_name', 'VARCHAR(64)'),
                        ('profile_image_url', 'VARCHAR(255)'), ('role', 'VARCHAR(50)'),
                        ('active', 'INTEGER'), ('created_at', dt_type), ('updated_at', dt_type)
                    ]
                    for col_name, col_type in col_defs:
                        if col_name not in user_cols:
                            _run_alter('"user"', col_name, col_type)
                            app.logger.info(f"Added {col_name} column to user table")
                if 'hotel_room' in tables:
                    columns = [col['name'] for col in inspector.get_columns('hotel_room')]
                    if 'room_category' not in columns:
                        _run_alter('hotel_room', 'room_category', 'VARCHAR(100)')
                        app.logger.info("Added room_category column to hotel_room table")
                if 'customer' in tables:
                    cust_cols = {c['name'] for c in inspector.get_columns('customer')}
                    for col_name, col_type in (
                        ('payment_terms', 'VARCHAR(100)'),
                        ('bank_name', 'VARCHAR(120)'),
                        ('bank_account', 'VARCHAR(255)'),
                        ('cliq_alias', 'VARCHAR(255)'),
                    ):
                        if col_name not in cust_cols:
                            _run_alter('customer', col_name, col_type)
                            app.logger.info(
                                'Added %s column to customer table',
                                col_name,
                            )
                            cust_cols.add(col_name)
                if 'inbound_request' in tables:
                    req_columns = [col['name'] for col in inspector.get_columns('inbound_request')]
                    for col_name, col_type in [
                        ('restaurant_voucher_note', 'TEXT'),
                        ('hotel_voucher_note', 'TEXT'),
                        ('advance_expense_sheet_data', 'TEXT'),
                        ('closing_guide_payment_sheet_data', 'TEXT'),
                        ('admin_invoice_data', 'TEXT'),
                        ('customer_invoice_data', 'TEXT'),
                        (
                            'pending_invoice_queue',
                            'BOOLEAN NOT NULL DEFAULT FALSE'
                            if is_pg
                            else 'BOOLEAN DEFAULT 0',
                        ),
                        ('deleted_reason', 'TEXT'),
                        ('parent_request_id', 'INTEGER'),
                        ('link_type', 'VARCHAR(20)'),
                        ('link_note', 'TEXT'),
                    ]:
                        if col_name not in req_columns:
                            _run_alter('inbound_request', col_name, col_type)
                            app.logger.info(f"Added {col_name} column to inbound_request")
        except Exception as e:
            app.logger.error(f"Schema upgrade FAILED: {e}\n{traceback.format_exc()}")

        # Fix PostgreSQL sequences if out of sync (prevents "Key (id)=X already exists")
        if is_pg:
            try:
                from sqlalchemy import text
                tables = [
                    'inbound_request', 'itinerary_row', 'inbound_hotel', 'hotel_room',
                    'inbound_transport', 'inbound_meal', 'inbound_guide', 'inbound_cash_expense',
                    'arrival_departure', 'arrival_batch', 'departure_batch', 'inbound_representative',
                    'inbound_optional', 'inbound_quotation', 'inbound_quotation_item',
                    'quotation_attachment', 'inbound_document', 'supplier', 'booking',
                    'service_item', 'customer', 'invoice',
                ]
                with db.engine.connect() as conn:
                    for tbl in tables:
                        try:
                            q = f'"{tbl}"' if tbl in ('user',) else tbl
                            conn.execute(text(f"""
                                SELECT setval(pg_get_serial_sequence('{q}', 'id'),
                                    COALESCE((SELECT MAX(id) FROM {q}), 1))
                            """))
                            conn.commit()
                        except Exception:
                            pass  # Skip tables without sequence
                app.logger.info("PostgreSQL sequences synced")
            except Exception as e:
                app.logger.warning(f"Sequence sync (non-fatal): {e}")
        
        # Bootstrap: ensure default user (id=1) exists - required for inbound requests, bookings, etc.
        # System operates under this user without authentication (dev and production)
        try:
            from app.models.user import create_test_data
            if User.query.get(1) is None:
                app.logger.info("Bootstrapping default user (id=1) for inbound/booking operations")
                create_test_data()
                # PostgreSQL: sync user sequence after explicit id=1 insert (prevents next insert from reusing 1)
                if is_pg:
                    try:
                        from sqlalchemy import text
                        with db.engine.connect() as conn:
                            conn.execute(text("""
                                SELECT setval(pg_get_serial_sequence('"user"', 'id'),
                                    COALESCE((SELECT MAX(id) FROM "user"), 1))
                            """))
                            conn.commit()
                        app.logger.info("User sequence synced after bootstrap")
                    except Exception as seq_err:
                        app.logger.warning(f"User sequence sync (non-fatal): {seq_err}")
        except Exception as e:
            app.logger.warning(f"Bootstrap default user: {e}")
        
        # Test data creation moved to separate initialization script
        # Run `python init_db.py` manually if needed
        
    return app