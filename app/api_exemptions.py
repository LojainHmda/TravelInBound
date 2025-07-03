"""
CSRF exemptions for API endpoints
"""
from flask import Blueprint

# Create a list of API routes that should be exempted from CSRF protection
csrf_exempt_routes = [
    '/tools/analyze-ticket',  # Flight ticket scanner API endpoint
    '/booking/service_item',  # Service item operations including delete
    '/customers/api/scan-passport',  # Passport scanner API endpoint
    '/booking/scan-flight-document',  # Multi-segment flight document scanner API endpoint
]

def is_csrf_exempt(request):
    """Check if the current request path should be exempted from CSRF protection"""
    return request.path in csrf_exempt_routes