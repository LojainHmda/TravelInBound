"""
CSRF exemptions for API endpoints - ensures production matches local behavior.
All API routes used by fetch() must be exempt since they don't use form CSRF tokens.
"""
import re

# Exact routes that need exemption
csrf_exempt_routes = [
    '/tools/analyze-ticket',
    '/booking/service_item',
    '/booking/scan-flight-document',
]

def is_api_route(path):
    """Exempt all API paths - /inbound/api/*, /booking/api/*, /customers/api/*, /api/*"""
    return bool(re.match(r'^/(inbound/api/|booking/api/|customers/api/|api/)', path))

def is_voucher_route(path):
    """Exempt voucher generation routes"""
    return bool(re.match(r'^/booking/\d+/voucher(/test)?$', path))

def is_csrf_exempt(request):
    """Check if the current request path should be exempted from CSRF protection"""
    return (request.path in csrf_exempt_routes or
            is_api_route(request.path) or
            is_voucher_route(request.path))