from flask import Blueprint, render_template, redirect, url_for
from app import db
from app.models.booking import Booking
from app.models import STATUS_REQUEST, STATUS_BOOKED, STATUS_IN_PROGRESS, STATUS_CONFIRMED
from app.models import ServiceItem, SERVICE_FLIGHT, SERVICE_HOTEL

# Create a blueprint for yellow dashboard
yellow_bp = Blueprint('yellow', __name__)

@yellow_bp.route('/')
def index():
    """Yellow dashboard with gradient cards"""
    # Get counts for each status
    request_count = Booking.query.filter_by(status=STATUS_REQUEST).count()
    booked_count = Booking.query.filter_by(status=STATUS_BOOKED).count()
    in_progress_count = Booking.query.filter_by(status=STATUS_IN_PROGRESS).count()
    completed_count = Booking.query.filter_by(status=STATUS_CONFIRMED).count()
    
    # Get service items for demo
    flight_items = ServiceItem.query.filter_by(service_type=SERVICE_FLIGHT).order_by(ServiceItem.created_at.desc()).limit(5).all()
    hotel_items = ServiceItem.query.filter_by(service_type=SERVICE_HOTEL).order_by(ServiceItem.created_at.desc()).limit(5).all()
    
    # Return the HTML directly to avoid template issues
    return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Yellow Gradient Dashboard</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css">
    <style>
        body {{
            font-family: Arial, sans-serif;
            background-color: #f5f5f5;
            margin: 0;
            padding: 20px;
        }}
        
        .container {{
            max-width: 1200px;
            margin: 0 auto;
        }}
        
        h1 {{
            color: #333;
            margin-bottom: 30px;
        }}
        
        /* Status Cards Row */
        .status-cards-row {{
            display: flex;
            flex-wrap: wrap;
            gap: 20px;
            margin-bottom: 40px;
        }}
        
        .status-card {{
            flex: 1;
            min-width: 200px;
            text-align: center;
            padding: 25px 15px;
            border-radius: 10px;
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        }}
        
        .status-title {{
            font-size: 18px;
            font-weight: 500;
            margin-bottom: 10px;
            color: #444;
        }}
        
        .status-count {{
            font-size: 42px;
            font-weight: 700;
            margin: 10px 0;
            color: #333;
        }}
        
        .status-icon {{
            font-size: 24px;
            margin-top: 10px;
            color: #555;
            opacity: 0.7;
        }}
        
        /* Yellow gradient variations */
        .card-requests {{
            background: linear-gradient(to bottom, #fff9e6, #ffe082);
        }}
        
        .card-booked {{
            background: linear-gradient(to bottom, #fff8dd, #ffd761);
        }}
        
        .card-in-progress {{
            background: linear-gradient(to bottom, #fff8d1, #ffcf3d);
        }}
        
        .card-fulfilled {{
            background: linear-gradient(to bottom, #f0f7d3, #cde58f);
        }}
        
        /* Tables */
        .card {{
            margin-bottom: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }}
        
        .card-header {{
            background-color: #f8f9fa;
            padding: 15px;
            border-bottom: 1px solid #e9ecef;
        }}
        
        .table {{
            margin-bottom: 0;
        }}
        
        .table th {{
            font-weight: 500;
            background-color: #f8f9fa;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Travel Booking Dashboard</h1>
        
        <!-- Yellow Gradient Status Cards -->
        <div class="status-cards-row">
            <!-- Requests Card -->
            <div class="status-card card-requests">
                <div class="status-title">Requests</div>
                <div class="status-count">{request_count}</div>
                <div class="status-icon">
                    <i class="fas fa-clipboard-list"></i>
                </div>
            </div>
            
            <!-- Booked Card -->
            <div class="status-card card-booked">
                <div class="status-title">Booked</div>
                <div class="status-count">{booked_count}</div>
                <div class="status-icon">
                    <i class="fas fa-bookmark"></i>
                </div>
            </div>
            
            <!-- In Progress Card -->
            <div class="status-card card-in-progress">
                <div class="status-title">In Progress</div>
                <div class="status-count">{in_progress_count}</div>
                <div class="status-icon">
                    <i class="fas fa-spinner"></i>
                </div>
            </div>
            
            <!-- Fulfilled Card -->
            <div class="status-card card-fulfilled">
                <div class="status-title">Fulfilled</div>
                <div class="status-count">{completed_count}</div>
                <div class="status-icon">
                    <i class="fas fa-check-circle"></i>
                </div>
            </div>
        </div>
        
        <div class="row">
            <div class="col-12">
                <a href="/dashboard" class="btn btn-primary mb-4">Back to Main Dashboard</a>
            </div>
        </div>
        
    </div>
</body>
</html>
    """