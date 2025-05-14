from flask import Blueprint, redirect, url_for, flash, render_template
from flask_login import current_user, login_required
import logging

logger = logging.getLogger(__name__)

# Create auth blueprint
auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/')
def index():
    # If user is logged in, show a welcome message
    if current_user.is_authenticated:
        logger.debug(f"User {current_user.username} is logged in, redirecting to dashboard")
        return redirect('/dashboard')
    # Otherwise show login link
    logger.debug("No authenticated user, showing login page")
    return render_template('auth/login.html')

@auth_bp.route('/profile')
@login_required
def profile():
    """User profile page"""
    return redirect('/dashboard')

@auth_bp.route('/login')
def login():
    """Login page with Replit Auth option"""
    if current_user.is_authenticated:
        flash('You are already logged in.', 'info')
        return redirect(url_for('dashboard'))
    return render_template('auth/login.html')