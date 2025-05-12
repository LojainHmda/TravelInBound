from flask import Blueprint, redirect, url_for, flash
from flask_login import current_user
from replit_auth import make_replit_blueprint, login_required

# Create Replit Auth blueprint
replit_bp = make_replit_blueprint()

# Create auth blueprint
auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/')
def index():
    # If user is logged in, show a welcome message
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    # Otherwise redirect to login
    return redirect(url_for('replit_auth.login'))

@auth_bp.route('/profile')
@login_required
def profile():
    """User profile page"""
    return redirect(url_for('main.dashboard'))

# For backward compatibility with the existing auth routes
@auth_bp.route('/login')
def login():
    """Redirect login to Replit Auth"""
    if current_user.is_authenticated:
        flash('You are already logged in.', 'info')
        return redirect(url_for('main.dashboard'))
    return redirect(url_for('replit_auth.login'))