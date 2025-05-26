#!/usr/bin/env python3
"""
Performance analysis script for the travel booking platform
Analyzes database queries, code efficiency, and identifies bottlenecks
"""

import os
import time
import sqlite3
from sqlalchemy import create_engine, text
from app import db, app
from app.models import *
import psutil
from datetime import datetime

def analyze_database_performance():
    """Analyze database performance issues"""
    print("🔍 Analyzing Database Performance...")
    
    with app.app_context():
        try:
            # Check for missing indexes
            print("\n📊 Database Schema Analysis:")
            
            # Check table sizes
            tables_info = []
            for table in ['booking', 'service_item', 'payment', 'supplier_payment', 'user']:
                try:
                    count = db.session.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
                    tables_info.append((table, count))
                    print(f"  • {table}: {count} records")
                except Exception as e:
                    print(f"  • {table}: Error - {e}")
            
            # Check for slow queries
            print("\n⚡ Potential Performance Issues:")
            
            # Large bookings without proper indexing
            booking_count = db.session.query(Booking).count()
            if booking_count > 1000:
                print(f"  ⚠️  Large booking table ({booking_count} records) - consider indexing")
            
            # Check for N+1 query patterns
            print("\n🔍 N+1 Query Analysis:")
            bookings = db.session.query(Booking).limit(5).all()
            for booking in bookings:
                # This could cause N+1 if not properly loaded
                service_count = len(booking.service_items)
                payment_count = len(booking.payments)
                print(f"  • Booking {booking.reference_number}: {service_count} services, {payment_count} payments")
            
            # Check for complex financial calculations
            print("\n💰 Financial Query Performance:")
            start_time = time.time()
            
            # This is a complex query from your finance module
            total_revenue = db.session.query(func.sum(Payment.amount)).scalar() or 0
            total_expenses = db.session.query(func.sum(SupplierPayment.amount)).scalar() or 0
            
            query_time = (time.time() - start_time) * 1000
            print(f"  • Financial summary query: {query_time:.2f}ms")
            print(f"  • Total Revenue: ${total_revenue:,.2f}")
            print(f"  • Total Expenses: ${total_expenses:,.2f}")
            
            if query_time > 100:
                print("  ⚠️  Slow financial queries detected!")
            
        except Exception as e:
            print(f"Database analysis error: {e}")

def analyze_code_performance():
    """Analyze code performance issues"""
    print("\n🚀 Code Performance Analysis:")
    
    # Check for large route files
    route_files = [
        'app/routes/main.py',
        'app/routes/booking.py', 
        'app/routes/finance.py',
        'routes.py'
    ]
    
    for route_file in route_files:
        if os.path.exists(route_file):
            size = os.path.getsize(route_file)
            lines = 0
            try:
                with open(route_file, 'r') as f:
                    lines = len(f.readlines())
                print(f"  • {route_file}: {lines} lines ({size} bytes)")
                if lines > 500:
                    print(f"    ⚠️  Large route file - consider splitting")
            except:
                pass

def analyze_memory_usage():
    """Analyze current memory usage"""
    print("\n🧠 Memory Usage Analysis:")
    
    process = psutil.Process()
    memory_info = process.memory_info()
    memory_percent = process.memory_percent()
    
    print(f"  • RSS Memory: {memory_info.rss / 1024 / 1024:.1f} MB")
    print(f"  • VMS Memory: {memory_info.vms / 1024 / 1024:.1f} MB")
    print(f"  • Memory Percentage: {memory_percent:.1f}%")
    
    if memory_percent > 70:
        print("  ⚠️  High memory usage detected!")

def check_database_connections():
    """Check database connection efficiency"""
    print("\n🔗 Database Connection Analysis:")
    
    with app.app_context():
        try:
            # Test connection speed
            start_time = time.time()
            db.session.execute(text("SELECT 1")).scalar()
            connection_time = (time.time() - start_time) * 1000
            
            print(f"  • Connection test: {connection_time:.2f}ms")
            
            if connection_time > 50:
                print("  ⚠️  Slow database connection!")
                
        except Exception as e:
            print(f"  ❌ Connection error: {e}")

def generate_performance_recommendations():
    """Generate specific performance recommendations"""
    print("\n🎯 Performance Optimization Recommendations:")
    
    recommendations = [
        "Add database indexes on frequently queried columns:",
        "  - booking.reference_number (if not already indexed)",
        "  - service_item.booking_id",
        "  - payment.booking_id",
        "  - supplier_payment.payment_date",
        "",
        "Optimize database queries:",
        "  - Use eager loading for booking.service_items relationships",
        "  - Add pagination to large data displays",
        "  - Cache frequently accessed data (customers, suppliers)",
        "",
        "Code optimizations:",
        "  - Implement Redis caching for dashboard data",
        "  - Use database aggregation instead of Python calculations",
        "  - Optimize the finance module's monthly calculations",
        "",
        "Infrastructure improvements:",
        "  - Enable database connection pooling",
        "  - Configure proper database timeouts",
        "  - Monitor and limit concurrent connections"
    ]
    
    for rec in recommendations:
        print(f"  {rec}")

def main():
    """Run comprehensive performance analysis"""
    print("🚀 Travel Platform Performance Analysis")
    print("=" * 50)
    
    analyze_memory_usage()
    check_database_connections()
    analyze_database_performance()
    analyze_code_performance()
    generate_performance_recommendations()
    
    print("\n✅ Performance analysis complete!")
    print(f"📊 View detailed monitoring at: http://localhost:9000")

if __name__ == '__main__':
    main()