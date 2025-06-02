"""
API routes for aviation data to support the flight confirmation form
"""
from flask import Blueprint, jsonify, request
from app.services.aviation_api import search_airlines, search_airports

api_bp = Blueprint('aviation_api', __name__, url_prefix='/api/aviation')

@api_bp.route('/airlines/search')
def airline_search():
    """Search for airlines by name or code"""
    query = request.args.get('q', '')
    if not query or len(query) < 2:
        return jsonify([])
    
    results = search_airlines(query)
    return jsonify(results)


@api_bp.route('/airports/search')
def airport_search():
    """Search for airports by name or code"""
    query = request.args.get('q', '')
    if not query or len(query) < 2:
        return jsonify([])
    
    results = search_airports(query)
    return jsonify(results)