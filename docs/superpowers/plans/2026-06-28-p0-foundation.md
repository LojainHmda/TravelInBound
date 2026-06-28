# P0 Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Establish enterprise foundation — config system, extracted extensions, real Flask-Login auth, and Flask-Migrate wired to DATABASE_URL_TEST only.

**Architecture:** Extract `db`/`login_manager`/`csrf` into `app/extensions.py` so models don't import from the app package (circular import prevention). Introduce `app/config.py` with `DevelopmentConfig` (→ TEST DB) and `ProductionConfig` (→ prod DB). Enable Flask-Login with real session-based login. All migrations run against TEST DB via FLASK_ENV=development.

**Tech Stack:** Flask, Flask-Login 0.6.3, Flask-SQLAlchemy 3.1.1, Flask-Migrate (new), Flask-WTF, psycopg2-binary, python-dotenv

## Global Constraints

- DATABASE_URL_TEST is used for ALL schema changes — never DATABASE_URL
- UI templates stay pixel-perfect as-is — no HTML changes except auth.py logic
- All new Python files follow existing import style (absolute imports from `app.`)
- Admin password: `admin123` (user id=1, already seeded by create_test_data)
- FLASK_ENV=development → TEST DB; FLASK_ENV=production → prod DB
- Never commit real credentials — .env stays gitignored

---

## File Map

```
MODIFY  app/__init__.py               remove inline db/login_manager/csrf; use config; use extensions
CREATE  app/config.py                 DevelopmentConfig, ProductionConfig, config dict
CREATE  app/extensions.py             db, login_manager, csrf instances only
MODIFY  app/models/user.py            import db from app.extensions
MODIFY  app/models/inbound.py         import db from app.extensions
MODIFY  app/models/booking.py         import db from app.extensions
MODIFY  app/models/customer.py        import db from app.extensions
MODIFY  app/models/supplier.py        import db from app.extensions
MODIFY  app/models/finance.py         import db from app.extensions
MODIFY  app/models/invoice.py         import db from app.extensions
MODIFY  app/models/service.py         import db from app.extensions
MODIFY  app/routes/auth.py            real login/logout with Flask-Login
MODIFY  requirements.txt              add Flask-Migrate, add FLASK_ENV note
MODIFY  .gitignore                    ensure .env, *.log, uploads/, app.db excluded
MODIFY  .env.example                  sanitized template, add FLASK_ENV=development
MODIFY  .env                          add FLASK_ENV=development line
CREATE  tests/__init__.py             empty, marks tests as package
CREATE  tests/conftest.py             pytest fixtures: app, client, test db session
```

---

### Task 1: Secure .gitignore and .env.example

**Files:**
- Modify: `.gitignore`
- Modify: `.env.example`

- [ ] **Step 1: Update .gitignore**

Read current `.gitignore` then ensure these lines exist:

```
# Secrets
.env
*.env.local

# Database
app.db
*.db
*.sqlite3

# Logs
*.log
error.txt
output.txt
server.log
server_error.log
server_output.log
output.log

# Uploads (store in cloud, not git)
uploads/

# Test artifacts
*.pdf
cookies.txt

# Python
__pycache__/
*.py[cod]
.venv/
venv/

# OS
.DS_Store
Thumbs.db
```

- [ ] **Step 2: Create sanitized .env.example**

```bash
# Copy from production — DO NOT commit real values
DATABASE_URL=postgresql://user:password@host/dbname?sslmode=require
DATABASE_URL_TEST=postgresql://user:password@host/testdb?sslmode=require

# Flask
SESSION_SECRET=change-me-to-a-random-32-char-string
FLASK_ENV=development

# AI features (optional)
OPENAI_API_KEY=sk-...

# Cloud Storage (optional — local fallback used if unset)
GCS_BUCKET_NAME=your-bucket-name
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json
```

- [ ] **Step 3: Add FLASK_ENV to .env**

Open `.env`, add line at top:
```
FLASK_ENV=development
```
This makes the app use DATABASE_URL_TEST automatically.

- [ ] **Step 4: Verify .env is gitignored**

```bash
git check-ignore -v .env
```
Expected: `.gitignore:.env   .env`

If not listed, the .gitignore update didn't take. Fix before continuing.

- [ ] **Step 5: Commit**

```bash
git add .gitignore .env.example
git commit -m "chore: harden gitignore, add sanitized env example"
```

---

### Task 2: Create app/extensions.py

**Files:**
- Create: `app/extensions.py`

**Produces:** `db`, `login_manager`, `csrf` importable from `app.extensions`

- [ ] **Step 1: Create the file**

```python
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect


class Base(DeclarativeBase):
    pass


db = SQLAlchemy(model_class=Base)
login_manager = LoginManager()
csrf = CSRFProtect()
```

- [ ] **Step 2: Verify imports work**

```bash
cd "c:/Users/lojai/OneDrive/Desktop/Projects/TravelInbound7050126 - Copy"
.venv/Scripts/python.exe -c "from app.extensions import db, login_manager, csrf; print('OK')"
```
Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add app/extensions.py
git commit -m "feat: extract db/login_manager/csrf into app/extensions.py"
```

---

### Task 3: Create app/config.py

**Files:**
- Create: `app/config.py`

**Produces:** `get_config()` function returning the right config class for FLASK_ENV

- [ ] **Step 1: Create the file**

```python
import os


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


class DevelopmentConfig(Config):
    DEBUG = True
    TESTING = False
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL_TEST')
    SQLALCHEMY_ENGINE_OPTIONS = Config._PG_ENGINE_OPTIONS
    SEND_FILE_MAX_AGE_DEFAULT = 0


class TestingConfig(Config):
    DEBUG = False
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL_TEST')
    SQLALCHEMY_ENGINE_OPTIONS = Config._PG_ENGINE_OPTIONS
    WTF_CSRF_ENABLED = False


class ProductionConfig(Config):
    DEBUG = False
    TESTING = False
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    SQLALCHEMY_ENGINE_OPTIONS = Config._PG_ENGINE_OPTIONS
    SESSION_COOKIE_SECURE = os.environ.get('SESSION_COOKIE_SECURE', 'False').lower() == 'true'


_config_map = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
}


def get_config():
    env = os.environ.get('FLASK_ENV', 'development').lower()
    return _config_map.get(env, DevelopmentConfig)
```

- [ ] **Step 2: Verify**

```bash
.venv/Scripts/python.exe -c "
import os; os.environ['FLASK_ENV']='development'
from app.config import get_config
c = get_config()
print(c.__name__)  # DevelopmentConfig
"
```
Expected: `DevelopmentConfig`

- [ ] **Step 3: Commit**

```bash
git add app/config.py
git commit -m "feat: add environment-based config (dev→TEST DB, prod→prod DB)"
```

---

### Task 4: Update app/models — import db from extensions

**Files:**
- Modify: `app/models/user.py`
- Modify: `app/models/inbound.py`
- Modify: `app/models/booking.py`
- Modify: `app/models/customer.py`
- Modify: `app/models/supplier.py`
- Modify: `app/models/finance.py`
- Modify: `app/models/invoice.py`
- Modify: `app/models/service.py`
- Modify: `app/models/oauth.py`

**Change:** In every model file, replace:
```python
from app import db
```
with:
```python
from app.extensions import db
```

- [ ] **Step 1: Apply the replacement in all model files**

Run this to confirm which files need changing:
```bash
grep -rl "from app import db" app/models/
```

For each file listed, change `from app import db` → `from app.extensions import db`

Also check for:
```bash
grep -rl "from app import db, login_manager" app/
```
Change those to:
```bash
from app.extensions import db, login_manager
```

- [ ] **Step 2: Verify no model still imports from app directly**

```bash
grep -r "from app import db" app/models/
```
Expected: no output.

- [ ] **Step 3: Commit**

```bash
git add app/models/
git commit -m "refactor: models import db from app.extensions (breaks circular import risk)"
```

---

### Task 5: Rewrite app/__init__.py to use config + extensions

**Files:**
- Modify: `app/__init__.py`

- [ ] **Step 1: Replace __init__.py**

```python
import os
import logging

from flask import Flask, request

from app.api_exemptions import is_csrf_exempt


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
    from app.extensions import db, login_manager, csrf
    db.init_app(app)
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
```

- [ ] **Step 2: Verify app starts**

```bash
.venv/Scripts/python.exe -c "
from app import create_app
app = create_app()
print('DB URI:', app.config['SQLALCHEMY_DATABASE_URI'][:50])
print('ENV:', app.config.get('DEBUG'))
"
```
Expected: DB URI starts with `postgresql://` pointing at TEST DB (ep-nameless-union...). DEBUG=True.

- [ ] **Step 3: Commit**

```bash
git add app/__init__.py
git commit -m "refactor: __init__.py uses config.py + extensions.py, removes inline setup"
```

---

### Task 6: Enable real Flask-Login authentication

**Files:**
- Modify: `app/routes/auth.py`

- [ ] **Step 1: Replace auth.py with real login/logout**

```python
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash

from app.extensions import db
from app.models.user import User, create_test_data

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        if not username or not password:
            flash('Username and password are required.', 'error')
            return render_template('auth/login.html')

        user = User.query.filter_by(username=username).first()

        if user is None or not user.check_password(password):
            flash('Invalid username or password.', 'error')
            return render_template('auth/login.html')

        if not user.active:
            flash('Your account is disabled. Contact admin.', 'error')
            return render_template('auth/login.html')

        login_user(user, remember=False)
        next_page = request.args.get('next')
        return redirect(next_page or url_for('main.index'))

    return render_template('auth/login.html')


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))


@auth_bp.route('/admin/users')
@login_required
def admin_users():
    if not current_user.is_admin():
        flash('Admin access required.', 'error')
        return redirect(url_for('main.index'))
    users = User.query.order_by(User.username).all()
    return render_template('auth/admin_users.html', users=users)


@auth_bp.route('/admin/users/new', methods=['GET', 'POST'])
@login_required
def create_user():
    if not current_user.is_admin():
        flash('Admin access required.', 'error')
        return redirect(url_for('main.index'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        first_name = request.form.get('first_name', '').strip()
        last_name = request.form.get('last_name', '').strip()
        role = request.form.get('role', '').strip()
        password = request.form.get('password', '')

        if not all([username, email, password, role]):
            flash('All required fields must be filled.', 'error')
            return render_template('auth/create_user.html')

        if User.query.filter_by(username=username).first():
            flash('Username already exists.', 'error')
            return render_template('auth/create_user.html')

        if User.query.filter_by(email=email).first():
            flash('Email already exists.', 'error')
            return render_template('auth/create_user.html')

        user = User(username=username, email=email, first_name=first_name,
                    last_name=last_name, role=role)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        flash(f'User {username} created successfully.', 'success')
        return redirect(url_for('auth.admin_users'))

    return render_template('auth/create_user.html')


@auth_bp.route('/admin/users/<int:user_id>/toggle-status', methods=['POST'])
@login_required
def toggle_user_status(user_id):
    if not current_user.is_admin():
        flash('Admin access required.', 'error')
        return redirect(url_for('main.index'))

    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash('You cannot deactivate your own account.', 'error')
        return redirect(url_for('auth.admin_users'))

    user.active = not user.active
    db.session.commit()
    flash(f'User {user.username} {"activated" if user.active else "deactivated"}.', 'success')
    return redirect(url_for('auth.admin_users'))


@auth_bp.route('/init-data')
def init_data():
    """Seed admin user — callable only if no users exist yet."""
    if User.query.count() > 0:
        flash('Data already initialized.', 'info')
        return redirect(url_for('auth.login'))
    try:
        create_test_data()
        flash('Admin user created. Username: admin / Password: admin123', 'success')
    except Exception as e:
        flash(f'Error: {e}', 'error')
    return redirect(url_for('auth.login'))
```

- [ ] **Step 2: Add @login_required to inbound blueprint**

In `app/routes/inbound.py`, find the blueprint-level decorator pattern. Add to the top of the file (after imports):

```python
from flask_login import login_required, current_user
```

Then on the `index` route function (and all other inbound routes), add `@login_required` decorator above the route function. The pattern:

```python
@inbound_bp.route('/')
@login_required
def index():
    ...
```

Apply `@login_required` to ALL route functions in `inbound.py`, `finance.py`, `customer.py`, `main.py` (not auth.py or api routes — those stay open or have their own guards).

- [ ] **Step 3: Test login flow**

Start server:
```bash
.venv/Scripts/python.exe start_server.py
```

Open http://127.0.0.1:5000 — should redirect to /auth/login
Enter `admin` / `admin123` — should redirect to hub
Visit /auth/logout — should redirect back to login

- [ ] **Step 4: Commit**

```bash
git add app/routes/auth.py app/routes/inbound.py app/routes/main.py app/routes/finance.py app/routes/customer.py
git commit -m "feat: enable Flask-Login authentication (admin/admin123, all routes protected)"
```

---

### Task 7: Install Flask-Migrate and init Alembic on TEST DB

**Files:**
- Modify: `requirements.txt`
- Create: `migrations/` (auto-generated by flask db init)

**Produces:** `flask db upgrade` command wired to DATABASE_URL_TEST

- [ ] **Step 1: Add Flask-Migrate to requirements.txt**

Add line:
```
flask-migrate>=4.0.7
```

- [ ] **Step 2: Install**

```bash
.venv/Scripts/pip.exe install flask-migrate
```
Expected: Successfully installed Flask-Migrate and Alembic

- [ ] **Step 3: Register Migrate in extensions.py**

Add to `app/extensions.py`:
```python
from flask_migrate import Migrate
migrate = Migrate()
```

- [ ] **Step 4: Init Migrate in create_app (app/__init__.py)**

After `db.init_app(app)` line, add:
```python
from app.extensions import migrate
migrate.init_app(app, db)
```

- [ ] **Step 5: Init migrations directory (run once)**

```bash
.venv/Scripts/python.exe -m flask --app start_server:app db init
```
Expected: `migrations/` directory created with `alembic.ini`, `env.py`, `versions/`

- [ ] **Step 6: Generate initial migration from current schema**

```bash
.venv/Scripts/python.exe -m flask --app start_server:app db migrate -m "initial schema from existing tables"
```
Expected: New file in `migrations/versions/xxxx_initial_schema_from_existing_tables.py`

- [ ] **Step 7: Apply migration to TEST DB**

```bash
.venv/Scripts/python.exe -m flask --app start_server:app db upgrade
```
Expected: `Running upgrade -> xxxx, initial schema...`

This creates all tables in DATABASE_URL_TEST based on current models.

- [ ] **Step 8: Verify TEST DB has tables**

```bash
.venv/Scripts/python.exe -c "
import os; os.environ['FLASK_ENV']='development'
from app import create_app
from app.extensions import db
from sqlalchemy import inspect
app = create_app()
with app.app_context():
    tables = inspect(db.engine).get_table_names()
    print(f'Tables in TEST DB: {len(tables)}')
    print(sorted(tables))
"
```
Expected: 20+ tables listed, all from models.

- [ ] **Step 9: Commit**

```bash
git add requirements.txt app/extensions.py app/routes/auth.py migrations/
git commit -m "feat: add Flask-Migrate, init Alembic on TEST DB, first migration applied"
```

---

### Task 8: Set up pytest foundation

**Files:**
- Create: `tests/__init__.py`
- Create: `tests/conftest.py`
- Create: `tests/test_auth.py`

- [ ] **Step 1: Install pytest**

```bash
.venv/Scripts/pip.exe install pytest pytest-flask
```

Add to requirements.txt:
```
pytest>=8.0.0
pytest-flask>=1.3.0
```

- [ ] **Step 2: Create tests/__init__.py**

Empty file — marks directory as Python package.

- [ ] **Step 3: Create tests/conftest.py**

```python
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
    return app.test_client()


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
```

- [ ] **Step 4: Create tests/test_auth.py**

```python
def test_login_page_loads(client):
    response = client.get('/auth/login')
    assert response.status_code == 200
    assert b'Log In' in response.data


def test_login_redirects_to_hub(client, admin_user):
    response = client.post('/auth/login',
                           data={'username': 'admin', 'password': 'admin123'},
                           follow_redirects=True)
    assert response.status_code == 200
    # Hub page has "Hub" title
    assert b'Hub' in response.data


def test_invalid_password_rejected(client, admin_user):
    response = client.post('/auth/login',
                           data={'username': 'admin', 'password': 'wrongpassword'})
    assert b'Invalid username or password' in response.data


def test_unauthenticated_inbound_redirects_to_login(client):
    response = client.get('/inbound/', follow_redirects=False)
    assert response.status_code == 302
    assert '/auth/login' in response.headers['Location']


def test_logout_clears_session(auth_client):
    response = auth_client.get('/auth/logout', follow_redirects=True)
    assert b'Log In' in response.data
```

- [ ] **Step 5: Run tests**

```bash
.venv/Scripts/python.exe -m pytest tests/test_auth.py -v
```
Expected: 5 tests pass.

- [ ] **Step 6: Commit**

```bash
git add tests/ requirements.txt
git commit -m "test: add pytest foundation with auth tests (5 passing)"
```

---

## Plan Complete

After all 8 tasks:
- App uses DATABASE_URL_TEST in development
- Real login required for all routes
- Flask-Migrate wired to TEST DB
- 5 auth tests passing
- Credentials secured in .gitignore

**Next plan:** `2026-06-28-p1-schema-migrations.md` — supplier FK linkage for inbound_hotel and inbound_meal.
