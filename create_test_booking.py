#!/usr/bin/env python3

import sqlite3
from datetime import datetime, date

# Connect to database and create comprehensive test data
conn = sqlite3.connect('instance/app.db')
cursor = conn.cursor()

# Create a complete test booking for the workflow
ref_number = f'TEST-{datetime.now().strftime("%H%M%S")}'

# Get or create test user
cursor.execute('SELECT id FROM user LIMIT 1')
user = cursor.fetchone()
user_id = user[0] if user else 1

# Get or create test customer  
cursor.execute('SELECT id FROM customer LIMIT 1')
customer = cursor.fetchone()
if customer:
    customer_id = customer[0]
else:
    cursor.execute('''
        INSERT INTO customer (first_name, last_name, email, phone, created_at, updated_at) 
        VALUES ('Test', 'Customer', 'test@example.com', '+1234567890', ?, ?)
    ''', (datetime.now(), datetime.now()))
    customer_id = cursor.lastrowid

# Create test booking in REQUEST status
cursor.execute('''
    INSERT INTO booking (reference_number, user_id, customer_id, status, created_at, updated_at, total_amount) 
    VALUES (?, ?, ?, 'REQUEST', ?, ?, 0.0)
''', (ref_number, user_id, customer_id, datetime.now(), datetime.now()))
booking_id = cursor.lastrowid

# Create multiple service items for comprehensive testing
services = [
    ('FLIGHT', 'Round-trip flight London to Dubai', 1200.00),
    ('HOTEL', 'Hotel accommodation Dubai - 7 nights', 850.00),
    ('TRANSPORT', 'Airport transfers and city tours', 200.00),
    ('VISA', 'UAE tourist visa processing', 150.00)
]

for service_type, description, amount in services:
    cursor.execute('''
        INSERT INTO service_item 
        (booking_id, service_type, description, amount, start_date, end_date, status, created_at, updated_at) 
        VALUES (?, ?, ?, ?, ?, ?, 'REQUEST', ?, ?)
    ''', (
        booking_id, service_type, description, amount,
        date(2025, 8, 15), date(2025, 8, 22),
        datetime.now(), datetime.now()
    ))

conn.commit()
conn.close()

print(f'Complete test booking created:')
print(f'Reference: {ref_number}')
print(f'Booking ID: {booking_id}')
print(f'Services: {len(services)} items')
print(f'Total Value: ${sum(s[2] for s in services)}')
print(f'')
print(f'TEST WORKFLOW:')
print(f'1. Go to /booking/{booking_id}')
print(f'2. Update status to IN_PROGRESS')
print(f'3. Test popup confirmation on services')
print(f'4. Generate invoice')
print(f'5. Issue voucher')
print(f'6. Check finance dashboard')