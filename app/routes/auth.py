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
    
@auth_bp.route('/direct-finance')
def direct_finance():
    """Direct access to finance dashboard with auto-login"""
    from flask_login import login_user
    from app.models import User
    
    # Auto-login as testuser
    user = User.query.filter_by(username='testuser').first()
    if user:
        login_user(user)
        logger.debug("Auto-login as testuser for direct finance access")
        return redirect('/finance/')
    else:
        logger.error("Test user not found in database")
        flash('Demo user not found. Please check if test data was created.', 'danger')
        return redirect('/auth/')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Login page with auto-login for demo"""
    from flask import request
    from flask_login import login_user
    from app.models import User
    
    # If user is logged in, redirect to dashboard
    if current_user.is_authenticated:
        logger.debug(f"User {current_user.username} is logged in, redirecting to requested page")
        next_page = request.args.get('next')
        if next_page:
            logger.debug(f"Redirecting to next page: {next_page}")
            return redirect(next_page)
        return redirect('/dashboard')
    
    # For demo purposes, automatically log in as testuser
    user = User.query.filter_by(username='testuser').first()
    if user:
        login_user(user)
        logger.debug("Auto-login as testuser for demo")
        
        # Redirect to the requested page or default to dashboard
        next_page = request.args.get('next')
        if next_page:
            logger.debug(f"Redirecting to next page: {next_page}")
            return redirect(next_page)
        return redirect('/dashboard')
    else:
        logger.error("Test user not found in database")
        flash('Demo user not found. Please check if test data was created.', 'danger')
    
    return render_template('auth/login.html')