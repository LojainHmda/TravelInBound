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

# Inbound API routes pattern
def is_inbound_api_route(path):
    """Check if the path is an inbound API route"""
    import re
    return bool(re.match(r'^/inbound/api/\d+/', path))

# Voucher generation routes - check for pattern matching
def is_voucher_route(path):
    """Check if the path is a voucher generation route"""
    import re
    return bool(re.match(r'^/booking/\d+/voucher(/test)?$', path))

def is_csrf_exempt(request):
    """Check if the current request path should be exempted from CSRF protection"""
    return (request.path in csrf_exempt_routes or 
            is_voucher_route(request.path) or 
            is_inbound_api_route(request.path))