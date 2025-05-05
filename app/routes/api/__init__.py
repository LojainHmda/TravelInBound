from flask import Blueprint

api_bp = Blueprint('api', __name__, url_prefix='/api')

# Import API routes
from app.routes.api import booking
from app.routes.api import service

# Register sub-blueprints
api_bp.register_blueprint(booking.booking_api_bp)
api_bp.register_blueprint(service.service_api_bp)