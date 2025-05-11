import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect

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
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///app.db"
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "pool_recycle": 300,
        "pool_pre_ping": True,
    }
    
    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
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
        
        # Register supplier and customer blueprints
        from app.routes.supplier import supplier_bp
        app.register_blueprint(supplier_bp)
        
        from app.routes.customer import customer_bp
        app.register_blueprint(customer_bp)
        
        # Register confirmation blueprint
        from app.routes.confirmation import confirmation_bp
        app.register_blueprint(confirmation_bp)
        
        # Register API blueprint
        from app.routes.api import api_bp
        app.register_blueprint(api_bp)
        
        # Set up login manager
        from app.models import User
        @login_manager.user_loader
        def load_user(user_id):
            return User.query.get(int(user_id))
        
        # Create database tables
        db.create_all()
        
        # Create test data if needed
        from app.models.user import create_test_data
        create_test_data()
        
    return app