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
    # Create the Flask app
    app = Flask(__name__)
    
    # Configure secret key and database URI
    app.secret_key = os.environ.get("SESSION_SECRET", "dev-key-for-testing")
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///app.db")
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "pool_recycle": 300,
        "pool_pre_ping": True,
    }
    
    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page'
    login_manager.login_message_category = 'warning'
    
    # Initialize CSRF protection
    csrf.init_app(app)
    
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
    
    with app.app_context():
        # Import models to ensure they are registered with SQLAlchemy
        from app.models import User
        
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
        
        # Register API blueprint (only once)
        try:
            from app.routes.api import api_bp
            app.register_blueprint(api_bp)
            
            # Register individual API modules with proper URL prefixes
            from app.routes.api.search import search_api
            app.register_blueprint(search_api, url_prefix='')
            
            from app.routes.api.chat import chat_api
            app.register_blueprint(chat_api, url_prefix='')
            
            from app.routes.api.invoice import invoice_api
            app.register_blueprint(invoice_api, url_prefix='')
        except Exception as e:
            app.logger.error(f"Could not register API blueprints: {str(e)}")
        
        # Register finance blueprint
        from app.routes.finance import finance
        app.register_blueprint(finance)
        
        # Register auth blueprint
        from app.routes.auth import auth_bp
        app.register_blueprint(auth_bp, url_prefix='/auth')
        
        # Register tools blueprint
        from app.routes.tools import tools_bp
        app.register_blueprint(tools_bp)
        
        # Set up login manager
        from app.models import User
        @login_manager.user_loader
        def load_user(user_id):
            return User.query.get(int(user_id))
        
        # Create database tables
        try:
            db.create_all()
        except Exception as e:
            app.logger.error(f"Database table creation error: {e}")
        
        # Test data creation moved to separate initialization script
        # Run `python init_db.py` manually if needed
        
    return app