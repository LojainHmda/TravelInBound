import os
import logging

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from flask_wtf.csrf import CSRFProtect
from werkzeug.middleware.proxy_fix import ProxyFix

# Configure logging
logging.basicConfig(level=logging.DEBUG)

class Base(DeclarativeBase):
    pass

# Initialize extensions
db = SQLAlchemy(model_class=Base)
csrf = CSRFProtect()

def create_app():
    """Create and configure the Flask application"""
    app = Flask(__name__)
    
    # Apply proxy fix for proper URL generation
    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)
    
    # Configure the app
    app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key")
    
    # Configure the database
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///travel_booking.db")
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "pool_recycle": 300,
        "pool_pre_ping": True,
    }
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    
    # Initialize extensions with app
    db.init_app(app)
    csrf.init_app(app)
    
    with app.app_context():
        # Import models to ensure tables are created
        try:
            import models  # noqa: F401
            # Create all tables
            db.create_all()
        except Exception as e:
            app.logger.error(f"Error creating database tables: {e}")
    
    # Register blueprints
    try:
        from app.routes.voucher import voucher_bp
        from app.routes.booking import booking_bp
        from app.routes.api import api_bp
        from app.routes.inbound import inbound_bp
        app.register_blueprint(voucher_bp)
        app.register_blueprint(booking_bp, url_prefix='/booking')
        app.register_blueprint(api_bp)
        app.register_blueprint(inbound_bp, url_prefix='/inbound')
    except ImportError as e:
        app.logger.warning(f"Could not import some blueprints: {e}")
    
    # Import main routes
    try:
        with app.app_context():
            import routes  # noqa: F401
    except ImportError as e:
        app.logger.warning(f"Could not import main routes: {e}")
    
    return app
