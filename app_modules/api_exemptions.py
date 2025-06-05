"""
CSRF exemptions for API endpoints
"""
from flask import Blueprint

# Create a list of API routes that should be exempted from CSRF protection
csrf_exempt_routes = [
    '/tools/analyze-ticket',  # Flight ticket scanner API endpoint
    '/booking/service_item',  # Service item operations including delete
]

def is_csrf_exempt(request):
    """Check if the current request path should be exempted from CSRF protection"""
    return request.path in csrf_exempt_routes