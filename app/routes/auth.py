from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash
from app import db
from app.models.user import User, create_test_data

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if not username or not password:
            flash('Please enter both username and password', 'error')
            return render_template('auth/login.html')
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            if user.active:
                login_user(user, remember=True)
                next_page = request.args.get('next')
                
                # Redirect to home page for all users
                if next_page:
                    return redirect(next_page)
                else:
                    return redirect(url_for('main.index'))
            else:
                flash('Your account has been deactivated. Please contact an administrator.', 'error')
        else:
            flash('Invalid username or password', 'error')
    
    return render_template('auth/login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out successfully', 'success')
    return redirect(url_for('auth.login'))

@auth_bp.route('/admin/users')
@login_required
def admin_users():
    if not current_user.is_admin():
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('main.dashboard'))
    
    users = User.query.all()
    return render_template('auth/admin_users.html', users=users)

@auth_bp.route('/admin/users/new', methods=['GET', 'POST'])
@login_required
def create_user():
    if not current_user.is_admin():
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('main.dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        role = request.form.get('role')
        password = request.form.get('password')
        
        # Validate required fields
        if not username or not email or not password or not role:
            flash('Please fill in all required fields', 'error')
            return render_template('auth/create_user.html')
        
        # Check if username already exists
        if User.query.filter_by(username=username).first():
            flash('Username already exists', 'error')
            return render_template('auth/create_user.html')
        
        # Check if email already exists
        if User.query.filter_by(email=email).first():
            flash('Email already exists', 'error')
            return render_template('auth/create_user.html')
        
        # Create new user
        user = User(
            username=username,
            email=email,
            first_name=first_name,
            last_name=last_name,
            role=role
        )
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        flash(f'User {username} created successfully', 'success')
        return redirect(url_for('auth.admin_users'))
    
    return render_template('auth/create_user.html')

@auth_bp.route('/admin/users/<int:user_id>/toggle-status')
@login_required
def toggle_user_status(user_id):
    if not current_user.is_admin():
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('main.dashboard'))
    
    user = User.query.get_or_404(user_id)
    
    if user.id == current_user.id:
        flash('You cannot deactivate your own account', 'error')
        return redirect(url_for('auth.admin_users'))
    
    user.active = not user.active
    db.session.commit()
    
    status = 'activated' if user.active else 'deactivated'
    flash(f'User {user.username} has been {status}', 'success')
    
    return redirect(url_for('auth.admin_users'))

@auth_bp.route('/init-data')
def init_data():
    """Initialize test data - remove in production"""
    try:
        create_test_data()
        flash('Test data initialized successfully', 'success')
    except Exception as e:
        flash(f'Error initializing data: {str(e)}', 'error')
    
    return redirect(url_for('auth.login'))