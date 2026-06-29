#!/usr/bin/env python3
"""
Initialize users in the database
"""
import os
import sys

# Add the project root to Python path
sys.path.insert(0, '/home/runner/workspace')

from app import create_app, db
from app.models.user import User, Agent

def init_users():
    app = create_app()
    with app.app_context():
        try:
            # Check if users already exist
            existing_users = User.query.count()
            print(f"Found {existing_users} existing users")
            
            if existing_users > 0:
                users = User.query.all()
                for user in users:
                    print(f"Existing user: {user.username} (role: {user.role})")
                return
            
            # Create admin user
            admin_user = User()
            admin_user.username = 'admin'
            admin_user.email = 'admin@arabtravelgroup.com'
            admin_user.first_name = 'Admin'
            admin_user.last_name = 'User'
            admin_user.role = 'admin'
            admin_user.set_password('admin123')
            admin_user.active = True
            
            # Create ops manager user
            ops_user = User()
            ops_user.username = 'opsmanager'
            ops_user.email = 'ops@arabtravelgroup.com'
            ops_user.first_name = 'Operations'
            ops_user.last_name = 'Manager'
            ops_user.role = 'ops_manager'
            ops_user.set_password('ops123')
            ops_user.active = True
            
            # Create agents
            flight_agent = Agent()
            flight_agent.name = 'Flight Specialist'
            flight_agent.email = 'flights@example.com'
            flight_agent.specialty = 'FLIGHT'
            
            hotel_agent = Agent()
            hotel_agent.name = 'Hotel Specialist'
            hotel_agent.email = 'hotels@example.com'
            hotel_agent.specialty = 'HOTEL'
            
            transport_agent = Agent()
            transport_agent.name = 'Transport Specialist'
            transport_agent.email = 'transport@example.com'
            transport_agent.specialty = 'TRANSPORT'
            
            visa_agent = Agent()
            visa_agent.name = 'Visa Specialist'
            visa_agent.email = 'visa@example.com'
            visa_agent.specialty = 'VISA'
            
            insurance_agent = Agent()
            insurance_agent.name = 'Insurance Specialist'
            insurance_agent.email = 'insurance@example.com'
            insurance_agent.specialty = 'INSURANCE'
            
            # Add all users and agents to session
            db.session.add_all([
                admin_user, ops_user,
                flight_agent, hotel_agent, transport_agent, visa_agent, insurance_agent
            ])
            
            # Commit the transaction
            db.session.commit()
            
            print("Successfully created users:")
            print("- admin / admin123 (Admin)")
            print("- opsmanager / ops123 (Operations Manager)")
            print("- 5 travel agents")
            
        except Exception as e:
            print(f"Error creating users: {e}")
            db.session.rollback()

if __name__ == '__main__':
    init_users()