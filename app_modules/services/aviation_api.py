"""
Aviation API service for fetching airline and airport data from public sources
"""
import requests
import json
from typing import List, Dict, Any
import os
from flask import current_app
import logging

# Cache the API responses to avoid unnecessary requests
AIRLINES_CACHE = None
AIRPORTS_CACHE = None

def get_airlines() -> List[Dict[str, str]]:
    """
    Fetch list of airlines with their IATA codes from a public dataset
    Returns a list of dictionaries with name and code
    """
    global AIRLINES_CACHE
    
    # If we already have the data cached, return it
    if AIRLINES_CACHE is not None:
        return AIRLINES_CACHE
    
    try:
        # Use a public dataset without API key requirements
        response = requests.get(
            "https://raw.githubusercontent.com/mwgg/Airports/master/airlines.json"
        )
        
        if response.status_code == 200:
            airlines_data = response.json()
            
            # Process the data into a simple format
            formatted_airlines = []
            for code, airline_info in airlines_data.items():
                if code and airline_info.get('name'):
                    formatted_airlines.append({
                        'code': code,
                        'name': airline_info.get('name')
                    })
            
            # Sort by airline name
            formatted_airlines.sort(key=lambda x: x['name'])
            
            # Cache the result
            AIRLINES_CACHE = formatted_airlines
            return formatted_airlines
        else:
            # If API request fails, use fallback data
            logging.error(f"Failed to fetch airlines data: {response.status_code}")
            return _get_fallback_airlines()
    
    except Exception as e:
        logging.error(f"Exception when fetching airlines data: {str(e)}")
        return _get_fallback_airlines()

def get_airports() -> List[Dict[str, str]]:
    """
    Fetch list of airports with their IATA codes from a public dataset
    Returns a list of dictionaries with name and code
    """
    global AIRPORTS_CACHE
    
    # If we already have the data cached, return it
    if AIRPORTS_CACHE is not None:
        return AIRPORTS_CACHE
    
    try:
        # Use a public dataset without API key requirements
        response = requests.get(
            "https://raw.githubusercontent.com/mwgg/Airports/master/airports.json"
        )
        
        if response.status_code == 200:
            airports_data = response.json()
            
            # Process the data into a simple format
            formatted_airports = []
            for airport in airports_data:
                if airport.get('iata') and airport.get('name'):
                    location = []
                    if airport.get('city'):
                        location.append(airport.get('city'))
                    if airport.get('country'):
                        location.append(airport.get('country'))
                    
                    location_str = f"({', '.join(location)})" if location else ""
                    
                    formatted_airports.append({
                        'code': airport.get('iata'),
                        'name': f"{airport.get('name')} {location_str}".strip()
                    })
            
            # Sort by airport code
            formatted_airports.sort(key=lambda x: x['code'])
            
            # Cache the result - only use the first 1000 most common airports to avoid performance issues
            AIRPORTS_CACHE = formatted_airports[:1000]
            return AIRPORTS_CACHE
        else:
            # If API request fails, use fallback data
            logging.error(f"Failed to fetch airports data: {response.status_code}")
            return _get_fallback_airports()
    
    except Exception as e:
        logging.error(f"Exception when fetching airports data: {str(e)}")
        return _get_fallback_airports()

def search_airlines(query: str) -> List[Dict[str, str]]:
    """
    Search airlines by name or code
    """
    airlines = get_airlines()
    query = query.lower()
    
    # Filter airlines that match the query
    results = [
        airline for airline in airlines
        if query in airline['name'].lower() or query in airline['code'].lower()
    ]
    
    # Limit results to avoid overwhelming the UI
    return results[:15]

def search_airports(query: str) -> List[Dict[str, str]]:
    """
    Search airports by name or code
    """
    airports = get_airports()
    query = query.lower()
    
    # Filter airports that match the query
    results = [
        airport for airport in airports
        if query in airport['name'].lower() or query in airport['code'].lower()
    ]
    
    # Limit results to avoid overwhelming the UI
    return results[:15]

def _get_fallback_airlines() -> List[Dict[str, str]]:
    """
    Return a small list of major airlines as fallback
    """
    return [
        {"code": "AA", "name": "American Airlines"},
        {"code": "BA", "name": "British Airways"},
        {"code": "DL", "name": "Delta Air Lines"},
        {"code": "EK", "name": "Emirates"},
        {"code": "LH", "name": "Lufthansa"},
        {"code": "SQ", "name": "Singapore Airlines"},
        {"code": "UA", "name": "United Airlines"},
        {"code": "QF", "name": "Qantas"},
        {"code": "AF", "name": "Air France"},
        {"code": "KL", "name": "KLM Royal Dutch Airlines"}
    ]

def _get_fallback_airports() -> List[Dict[str, str]]:
    """
    Return a small list of major airports as fallback
    """
    return [
        {"code": "JFK", "name": "John F. Kennedy International Airport (New York, USA)"},
        {"code": "LHR", "name": "London Heathrow Airport (London, UK)"},
        {"code": "CDG", "name": "Charles de Gaulle Airport (Paris, France)"},
        {"code": "DXB", "name": "Dubai International Airport (Dubai, UAE)"},
        {"code": "LAX", "name": "Los Angeles International Airport (Los Angeles, USA)"},
        {"code": "SIN", "name": "Singapore Changi Airport (Singapore)"},
        {"code": "HKG", "name": "Hong Kong International Airport (Hong Kong)"},
        {"code": "FRA", "name": "Frankfurt Airport (Frankfurt, Germany)"},
        {"code": "SYD", "name": "Sydney Airport (Sydney, Australia)"},
        {"code": "AMS", "name": "Amsterdam Airport Schiphol (Amsterdam, Netherlands)"}
    ]