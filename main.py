# Temporary SQLite demo override
import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_wtf.csrf import CSRFProtect, generate_csrf
from werkzeug.security import check_password_hash

# Override database environment to force SQLite
for key in ['DATABASE_URL', 'PGPORT', 'PGUSER', 'PGPASSWORD', 'PGDATABASE', 'PGHOST']:
    os.environ.pop(key, None)

app = Flask(__name__, template_folder='app/templates', static_folder='app/static')
app.secret_key = "demo-secret-key-123"

# Initialize CSRF protection
csrf = CSRFProtect(app)

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Make csrf_token available in templates
@app.context_processor
def inject_csrf_token():
    return dict(csrf_token=generate_csrf)

class User(UserMixin):
    def __init__(self, id, username, email):
        self.id = id
        self.username = username
        self.email = email

@login_manager.user_loader
def load_user(user_id):
    try:
        conn = sqlite3.connect('travel_booking.db')
        cursor = conn.cursor()
        cursor.execute('SELECT id, username, email FROM user WHERE id = ?', (user_id,))
        user_data = cursor.fetchone()
        conn.close()
        
        if user_data:
            return User(user_data[0], user_data[1], user_data[2])
    except:
        pass
    return None

def get_user_by_username(username):
    try:
        conn = sqlite3.connect('travel_booking.db')
        cursor = conn.cursor()
        cursor.execute('SELECT id, username, email, password_hash FROM user WHERE username = ?', (username,))
        user_data = cursor.fetchone()
        conn.close()
        return user_data
    except:
        return None

def get_booking_details(booking_id):
    try:
        conn = sqlite3.connect('travel_booking.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT b.id, b.invoice_number, b.total_amount, b.total_currency, b.pax_count, b.status,
                   c.name as customer_name, c.company_name, c.customer_type
            FROM booking b
            LEFT JOIN customer c ON b.customer_id = c.id
            WHERE b.id = ?
        ''', (booking_id,))
        booking = cursor.fetchone()
        
        if not booking:
            conn.close()
            return None, []
        
        cursor.execute('''
            SELECT service_type, description, amount, start_date, status
            FROM service_item
            WHERE booking_id = ?
            ORDER BY start_date
        ''', (booking_id,))
        services = cursor.fetchall()
        
        conn.close()
        return booking, services
    except:
        return None, []

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('simple_login.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user_data = get_user_by_username(username)
        
        if user_data and check_password_hash(user_data[3], password):
            user = User(user_data[0], user_data[1], user_data[2])
            login_user(user)
            flash(f'Welcome back, {username}!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password', 'error')
    
    return render_template('simple_login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required  
def dashboard():
    return render_template('dashboard.html', user=current_user)

@app.route('/booking/<int:booking_id>')
@login_required
def booking_details(booking_id):
    booking, services = get_booking_details(booking_id)
    if not booking:
        flash('Booking not found', 'error')
        return redirect(url_for('dashboard'))
    
    return render_template('booking/booking_details.html', booking=booking, services=services)

@app.route('/booking/<int:booking_id>/invoice')
@login_required
def professional_invoice(booking_id):
    booking, services = get_booking_details(booking_id)
    if not booking:
        flash('Booking not found', 'error')
        return redirect(url_for('dashboard'))
    
    return render_template('booking/invoice_professional.html', booking=booking, services=services)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)