from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash

from app.extensions import db
from app.models.user import User, create_test_data

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        if not username or not password:
            flash('Username and password are required.', 'error')
            return render_template('auth/login.html')

        user = User.query.filter_by(username=username).first()

        if user is None or not user.check_password(password):
            flash('Invalid username or password.', 'error')
            return render_template('auth/login.html')

        if not user.active:
            flash('Your account is disabled. Contact admin.', 'error')
            return render_template('auth/login.html')

        login_user(user, remember=False)
        next_page = request.args.get('next')
        return redirect(next_page or url_for('main.index'))

    return render_template('auth/login.html')


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))


@auth_bp.route('/admin/users')
@login_required
def admin_users():
    if not current_user.is_admin():
        flash('Admin access required.', 'error')
        return redirect(url_for('main.index'))
    users = User.query.order_by(User.username).all()
    return render_template('auth/admin_users.html', users=users)


@auth_bp.route('/admin/users/new', methods=['GET', 'POST'])
@login_required
def create_user():
    if not current_user.is_admin():
        flash('Admin access required.', 'error')
        return redirect(url_for('main.index'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        first_name = request.form.get('first_name', '').strip()
        last_name = request.form.get('last_name', '').strip()
        role = request.form.get('role', '').strip()
        password = request.form.get('password', '')

        if not all([username, email, password, role]):
            flash('All required fields must be filled.', 'error')
            return render_template('auth/create_user.html')

        if User.query.filter_by(username=username).first():
            flash('Username already exists.', 'error')
            return render_template('auth/create_user.html')

        if User.query.filter_by(email=email).first():
            flash('Email already exists.', 'error')
            return render_template('auth/create_user.html')

        user = User(username=username, email=email, first_name=first_name,
                    last_name=last_name, role=role)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        flash(f'User {username} created successfully.', 'success')
        return redirect(url_for('auth.admin_users'))

    return render_template('auth/create_user.html')


@auth_bp.route('/admin/users/<int:user_id>/toggle-status', methods=['POST'])
@login_required
def toggle_user_status(user_id):
    if not current_user.is_admin():
        flash('Admin access required.', 'error')
        return redirect(url_for('main.index'))

    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash('You cannot deactivate your own account.', 'error')
        return redirect(url_for('auth.admin_users'))

    user.active = not user.active
    db.session.commit()
    flash(f'User {user.username} {"activated" if user.active else "deactivated"}.', 'success')
    return redirect(url_for('auth.admin_users'))


@auth_bp.route('/init-data')
def init_data():
    """Seed admin user — callable only if no users exist yet."""
    if User.query.count() > 0:
        flash('Data already initialized.', 'info')
        return redirect(url_for('auth.login'))
    try:
        create_test_data()
        flash('Admin user created. Username: admin / Password: admin123', 'success')
    except Exception as e:
        flash(f'Error: {e}', 'error')
    return redirect(url_for('auth.login'))
