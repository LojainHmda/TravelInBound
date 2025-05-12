from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash
from app import db
from app.models import User

# Create blueprint for authentication
auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Handle user login"""
    # If user is already logged in, redirect to dashboard
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember = True if request.form.get('remember') else False
        
        # Use test account for development purposes
        # In a real app, you'd validate against stored credentials 
        if username == 'admin' and password == 'admin':
            user = User.query.filter_by(username='admin').first()
            if not user:
                # Create admin user if it doesn't exist
                user = User(username='admin', email='admin@example.com')
                # In a real app, you'd hash the password
                user.password_hash = 'admin' 
                db.session.add(user)
                db.session.commit()
            
            # Log in the user
            login_user(user, remember=remember)
            
            # Redirect to the requested page or default to dashboard
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            return redirect(url_for('main.dashboard'))
        else:
            flash('Please check your login details and try again.', 'danger')
            
    return render_template('auth/login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    """Handle user logout"""
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))