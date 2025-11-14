from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from werkzeug.security import check_password_hash
from app import db
from app.models.user import User, create_test_data

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    # Authentication disabled - redirect to home page
    return redirect(url_for('main.index'))

@auth_bp.route('/logout')
def logout():
    # Authentication disabled - redirect to home page
    flash('Logout disabled - authentication removed', 'info')
    return redirect(url_for('main.index'))

@auth_bp.route('/admin/users')
def admin_users():
    # Authentication disabled - all users have admin access
    users = User.query.all()
    return render_template('auth/admin_users.html', users=users)

@auth_bp.route('/admin/users/new', methods=['GET', 'POST'])
def create_user():
    # Authentication disabled - all users have admin access
    
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
def toggle_user_status(user_id):
    # Authentication disabled - all users have admin access
    user = User.query.get_or_404(user_id)
    
    if user.id == 1:
        flash('You cannot deactivate the admin account', 'error')
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