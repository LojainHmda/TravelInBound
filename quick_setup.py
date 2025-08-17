#!/usr/bin/env python3
"""
Quick setup script to create SQLite database and users
"""
import os
import sqlite3
from werkzeug.security import generate_password_hash

def main():
    # Remove old database
    if os.path.exists('travel_booking.db'):
        os.remove('travel_booking.db')
    
    # Create new SQLite database
    conn = sqlite3.connect('travel_booking.db')
    cursor = conn.cursor()
    
    # Create basic user table
    cursor.execute('''
        CREATE TABLE user (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username VARCHAR(64) UNIQUE NOT NULL,
            email VARCHAR(120) UNIQUE NOT NULL,
            password_hash VARCHAR(256)
        )
    ''')
    
    # Create customer table for demo
    cursor.execute('''
        CREATE TABLE customer (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name VARCHAR(100) NOT NULL,
            email VARCHAR(120),
            phone VARCHAR(20),
            company_name VARCHAR(100),
            customer_type VARCHAR(20) DEFAULT 'INDIVIDUAL',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create booking table for demo  
    cursor.execute('''
        CREATE TABLE booking (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER,
            invoice_number VARCHAR(20),
            total_amount DECIMAL(10,2) DEFAULT 0.00,
            total_currency VARCHAR(3) DEFAULT 'USD',
            pax_count INTEGER DEFAULT 1,
            status VARCHAR(20) DEFAULT 'REQUEST',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (customer_id) REFERENCES customer (id)
        )
    ''')
    
    # Create service_items table for demo
    cursor.execute('''
        CREATE TABLE service_item (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            booking_id INTEGER NOT NULL,
            service_type VARCHAR(50) NOT NULL,
            description TEXT,
            amount DECIMAL(10,2) DEFAULT 0.00,
            start_date DATE,
            status VARCHAR(20) DEFAULT 'PENDING',
            FOREIGN KEY (booking_id) REFERENCES booking (id)
        )
    ''')
    
    # Create users
    users = [
        ('admin', 'admin@windowsofjordan.com', 'admin123'),
        ('user', 'user@windowsofjordan.com', 'user123'),
        ('manager', 'manager@windowsofjordan.com', 'manager123')
    ]
    
    for username, email, password in users:
        password_hash = generate_password_hash(password)
        cursor.execute('''
            INSERT INTO user (username, email, password_hash)
            VALUES (?, ?, ?)
        ''', (username, email, password_hash))
    
    # Create sample customer
    cursor.execute('''
        INSERT INTO customer (name, email, phone, company_name, customer_type)
        VALUES (?, ?, ?, ?, ?)
    ''', ('Expert Travel', 'contact@experttravel.com', '+962123456789', 'Expert Travel Agency', 'AGENCY'))
    
    # Create sample booking with invoice
    cursor.execute('''
        INSERT INTO booking (customer_id, invoice_number, total_amount, pax_count, status)
        VALUES (?, ?, ?, ?, ?)
    ''', (1, 'WJ-25061004', 1500.00, 3, 'CONFIRMED'))
    
    # Create sample service items
    cursor.execute('''
        INSERT INTO service_item (booking_id, service_type, description, amount, start_date)
        VALUES (?, ?, ?, ?, ?)
    ''', (1, 'HOTEL', '3 nights accommodation in Amman', 450.00, '2025-08-20'))
    
    cursor.execute('''
        INSERT INTO service_item (booking_id, service_type, description, amount, start_date)
        VALUES (?, ?, ?, ?, ?)
    ''', (1, 'TRANSPORT', 'Airport transfer and city tours', 300.00, '2025-08-20'))
    
    cursor.execute('''
        INSERT INTO service_item (booking_id, service_type, description, amount, start_date)
        VALUES (?, ?, ?, ?, ?)
    ''', (1, 'FLIGHT', 'Round trip flights to Jordan', 750.00, '2025-08-20'))
    
    conn.commit()
    conn.close()
    
    print("Database created successfully!")
    print("\nLogin credentials:")
    print("Username: admin / Password: admin123")
    print("Username: user / Password: user123")
    print("Username: manager / Password: manager123")
    print("\nSample data:")
    print("- Booking #151 with invoice WJ-25061004")
    print("- Customer: Expert Travel Agency")
    print("- Professional invoice ready for testing")

if __name__ == "__main__":
    main()