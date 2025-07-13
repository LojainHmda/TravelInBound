"""
Airline-style voucher generator matching the exact template provided
"""

import os
import csv
import logging
from datetime import datetime
from io import BytesIO
import base64

class AirlineVoucherGenerator:
    def __init__(self, booking):
        self.booking = booking
        self.hotels_data = self._load_hotels_data()
    
    def _load_hotels_data(self):
        """Load hotels data from CSV"""
        hotels_data = {}
        try:
            csv_path = os.path.join(os.path.dirname(__file__), '../../attached_assets/hotelconswithaddress_1751201464690.csv')
            if os.path.exists(csv_path):
                with open(csv_path, 'r', encoding='utf-8') as file:
                    reader = csv.DictReader(file)
                    for row in reader:
                        hotel_name = row.get('Hotel Name', '').lower().strip()
                        if hotel_name:
                            hotels_data[hotel_name] = {
                                'address': row.get('Address', ''),
                                'phone': row.get('address 4', '') or row.get('Address line4', '') or row.get('phone', '')
                            }
        except Exception as e:
            logging.error(f"Error loading hotels data: {e}")
        
        return hotels_data
    
    def _get_logo_path(self):
        """Get the correct logo path for PDF generation"""
        logo_path = os.path.abspath('static/arab_travel_logo.png')
        return f"file:///{logo_path}"
    
    def generate_html(self):
        """Generate voucher HTML matching the exact template layout"""
        service_items = list(self.booking.service_items)
        customer = self.booking.customer if hasattr(self.booking, 'customer') else None
        
        # Extract actual booking data
        flight_data = self._extract_flight_data(service_items)
        hotel_data = self._extract_hotel_data(service_items)
        passenger_data = self._prepare_passenger_data(customer)
        logo_url = self._get_logo_path()
        
        # Generate HTML exactly matching the template
        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Travel Voucher - {self.booking.reference_number}</title>
    <style>
        body {{
            font-family: 'Georgia', serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
            color: #333;
        }}
        .voucher-container {{
            max-width: 900px;
            margin: 0 auto;
            background: white;
            border: 1px solid #ddd;
        }}
        .company-header {{
            background: #ffffff;
            padding: 20px;
            color: #2c3e50;
            display: flex;
            align-items: center;
            justify-content: space-between;
            border-bottom: 3px solid #2E5A87;
        }}
        .company-logo {{
            height: 120px;
            width: auto;
        }}
        .company-info {{
            text-align: center;
            flex-grow: 1;
        }}
        .company-name {{
            font-size: 26px;
            font-weight: 600;
            margin: 0;
            font-family: 'Segoe UI', 'Helvetica Neue', Arial, sans-serif;
            color: #2E5A87;
            display: inline-block;
        }}
        .company-tagline {{
            font-size: 14px;
            margin: 8px 0 0 0;
            font-family: 'Segoe UI', 'Helvetica Neue', Arial, sans-serif;
            color: #2E5A87;
            font-weight: 600;
            display: block;
            text-align: center;
        }}
        .tagline-underline {{
            width: 200px;
            height: 3px;
            background: linear-gradient(135deg, #FFD700, #FFA500);
            margin: 5px auto 0 auto;
            border-radius: 2px;
        }}
        .section {{
            padding: 20px;
        }}
        .section-title {{
            font-size: 10px;
            font-weight: bold;
            color: #2E5A87;
            margin-bottom: 15px;
            border-bottom: 1px solid #ddd;
            padding-bottom: 5px;
            font-family: 'Georgia', serif;
        }}
        .info-table {{
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 20px;
            font-family: 'Georgia', serif;
        }}
        .info-table td {{
            padding: 8px 10px;
            border-bottom: 1px solid #eee;
            font-size: 10px;
        }}
        .info-table .label {{
            font-weight: bold;
            width: 150px;
            background-color: #f8f9fa;
        }}
        .passenger-table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 5px;
            border: 1px solid #ddd;
        }}
        .passenger-table th {{
            background-color: #f8f9fa;
            padding: 6px 8px;
            text-align: left;
            font-weight: bold;
            border: 1px solid #ddd;
            font-size: 10px;
        }}
        .passenger-table td {{
            padding: 5px 8px;
            border: 1px solid #ddd;
            text-align: left;
            font-size: 10px;
        }}
        .flight-segment {{
            border: 1px solid #ddd;
            margin: 5px 0;
            padding: 8px;
            background-color: #f9f9f9;
        }}
        .passenger-ticket-info {{
            margin-top: 6px;
            padding: 4px 0;
            border-top: 1px solid #e0e0e0;
            background-color: #fff;
            border-radius: 3px;
        }}
        .passenger-trip-row {{
            display: flex;
            align-items: flex-start;
            gap: 20px;
        }}
        .trip-info-left {{
            color: #000;
            font-size: 11px;
            margin-bottom: 3px;
            font-family: 'Georgia', serif;
            flex: 1;
        }}
        .passenger-details-right {{
            flex: 1;
        }}
        .passenger-names {{
            color: #2E5A87;
            font-size: 10px;
            margin-bottom: 2px;
            font-family: 'Georgia', serif;
        }}
        .pnr-number {{
            color: #2E5A87;
            font-size: 10px;
            margin-bottom: 2px;
            background-color: #F0F8FF;
            padding: 1px 3px;
            border-radius: 2px;
            display: inline-block;
            font-family: 'Georgia', serif;
        }}
        .eticket-number {{
            color: #FFD700;
            background-color: #2E5A87;
            padding: 1px 3px;
            border-radius: 2px;
            font-size: 10px;
            display: inline-block;
            font-family: 'Georgia', serif;
        }}

        .flight-details {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            background-color: white;
            padding: 10px;
            border-radius: 4px;
        }}
        .departure-section, .arrival-section {{
            flex: 1;
            text-align: center;
        }}
        .flight-middle {{
            flex: 1;
            text-align: center;
            padding: 0 10px;
        }}
        .section-label {{
            font-weight: bold;
            color: #666;
            margin-bottom: 3px;
            font-size: 10px;
            font-family: 'Georgia', serif;
        }}
        .airport-time {{
            font-size: 10px;
            font-weight: bold;
            margin-bottom: 3px;
            font-family: 'Georgia', serif;
        }}
        .flight-date {{
            color: #666;
            margin-bottom: 3px;
            font-size: 10px;
            font-family: 'Georgia', serif;
        }}
        .airport-code {{
            color: #666;
            font-size: 10px;
            font-family: 'Georgia', serif;
        }}
        .flight-type {{
            font-weight: bold;
            margin-bottom: 5px;
            font-size: 10px;
            font-family: 'Georgia', serif;
        }}
        .aircraft-icon {{
            font-size: 18px;
            margin: 10px 0;
        }}
        .baggage {{
            background-color: #333;
            color: white;
            padding: 5px 10px;
            border-radius: 3px;
            font-size: 10px;
            font-family: 'Georgia', serif;
        }}
        .hotel-header {{
            background-color: #f8f9fa;
            padding: 15px;
            border-radius: 5px;
            margin-bottom: 15px;
            border-left: 4px solid #2E5A87;
        }}
        .hotel-main-name {{
            font-size: 11px;
            font-weight: bold;
            color: #2E5A87;
            margin-bottom: 5px;
            font-family: 'Georgia', serif;
        }}
        .hotel-main-address {{
            font-size: 14px;
            color: #2E5A87;
            margin-bottom: 3px;
            font-family: 'Georgia', serif;
        }}
        .hotel-main-phone {{
            font-size: 12px;
            color: #666;
            font-family: 'Georgia', serif;
        }}
        .hotel-details-table {{
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 20px;
            font-family: 'Georgia', serif;
        }}
        .hotel-details-table th, .hotel-details-table td {{
            border: 1px solid #ddd;
            padding: 8px;
            text-align: left;
            font-size: 12px;
            font-family: 'Georgia', serif;
        }}
        .hotel-details-table th {{
            background-color: #f5f5f5;
            font-weight: bold;
            font-size: 12px;
        }}
        .footer {{
            text-align: center;
            padding: 8px;
            background-color: #f8f9fa;
            border-top: 1px solid #ddd;
            font-family: 'Georgia', serif;
            font-size: 10px;
        }}
        .footer-title {{
            font-weight: bold;
            color: #2E5A87;
            margin-bottom: 5px;
            font-family: 'Georgia', serif;
            font-size: 12px;
        }}
        @media print {{
            body {{ background: white; padding: 0; }}
            .voucher-container {{ border: none; }}
        }}
    </style>
</head>
<body>
    <div class="voucher-container">
        <!-- Company Header with Arab Travel Group Branding -->
        <div class="company-header">
            <img src="{logo_url}" alt="Arabi Travel" class="company-logo">
            <div class="company-info">
                <h1 class="company-name">ARABI TRAVEL</h1>
                <p class="company-tagline">Travel Voucher</p>
                <div class="tagline-underline"></div>
            </div>
            <div style="width: 50px;"></div> <!-- Spacer for balance -->
        </div>
        
        <!-- Compact Booking Information Header -->
        <div style="background-color: #f8f9fa; padding: 8px; border: 1px solid #ddd; margin-bottom: 10px; font-size: 9px; font-family: 'Georgia', serif; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap;">
            <span><strong>ID:</strong> {self.booking.reference_number}</span>
            <span><strong>Date:</strong> {self.booking.created_at.strftime('%d-%m-%Y') if self.booking.created_at else 'N/A'}</span>
            <span><strong>PNR:</strong> XVSQ4V</span>
            <span><strong>Tel:</strong> {customer.phone if customer and customer.phone else '+97022956640'}</span>
            <span><strong>Email:</strong> {customer.email if customer and customer.email else 'info@arabtravel.ps'}</span>
        </div>
        
        <!-- Passenger List Section -->
        <div class="section">
            <div class="section-title">Passenger List</div>
            <table class="passenger-table">
                <thead>
                    <tr>
                        <th>Name</th>
                        <th>Type</th>
                        <th>Ticket No</th>
                    </tr>
                </thead>
                <tbody>"""
        
        # Add passenger rows using real data from confirmations
        if passenger_data:
            for i, passenger in enumerate(passenger_data):
                html_content += f"""
                    <tr>
                        <td>{passenger['name']}</td>
                        <td>{passenger['type']}</td>
                        <td>{passenger.get('ticket_number', 'TBD')}</td>
                    </tr>"""
        else:
            html_content += """
                    <tr>
                        <td>No passenger data available</td>
                        <td>-</td>
                        <td>-</td>
                    </tr>"""
        
        html_content += """
                </tbody>
            </table>
        </div>"""
        
        # Flights Section (if flight data exists)
        if flight_data:
            html_content += f"""
        <div class="section">
            <div class="section-title">Flights</div>"""
            
            # Handle multi-segment flight data with the new format
            if 'segments' in flight_data and flight_data['segments']:
                # Process each flight segment in the reference format
                for i, segment in enumerate(flight_data['segments']):
                    trip_number = i + 1
                    # Extract and ensure we have valid airport data
                    departure_airport = str(segment.get('departure_airport', '')).strip()
                    arrival_airport = str(segment.get('arrival_airport', '')).strip()
                    pnr = str(segment.get('pnr', '')).strip()
                    airline = str(segment.get('airline', '')).strip()
                    flight_number = str(segment.get('flight_number', '')).strip()
                    flight_date = str(segment.get('flight_date', '')).strip()
                    departure_time = str(segment.get('departure_time', '')).strip()
                    arrival_time = str(segment.get('arrival_time', '')).strip()
                    
                    # Get airport codes for display - extract 3-letter codes properly
                    dep_code = ''
                    arr_code = ''
                    
                    # For departure airport
                    if 'Queen Alia' in departure_airport:
                        dep_code = 'AMM'
                    elif 'Abu Dhabi' in departure_airport or 'Dhabi' in departure_airport:
                        dep_code = 'AUH'
                    elif 'Doha' in departure_airport or 'Hamad' in departure_airport:
                        dep_code = 'DOH'
                    elif 'Dubai' in departure_airport:
                        dep_code = 'DXB'
                    elif 'Cairo' in departure_airport:
                        dep_code = 'CAI'
                    elif 'Istanbul' in departure_airport:
                        dep_code = 'IST'
                    elif 'London' in departure_airport:
                        dep_code = 'LHR'
                    else:
                        # Fallback: look for 3-letter uppercase codes in the text
                        import re
                        codes = re.findall(r'\b[A-Z]{3}\b', departure_airport)
                        dep_code = codes[0] if codes else departure_airport[:3].upper()
                    
                    # For arrival airport
                    if 'Queen Alia' in arrival_airport:
                        arr_code = 'AMM'
                    elif 'Abu Dhabi' in arrival_airport or 'Dhabi' in arrival_airport:
                        arr_code = 'AUH'
                    elif 'Doha' in arrival_airport or 'Hamad' in arrival_airport:
                        arr_code = 'DOH'
                    elif 'Dubai' in arrival_airport:
                        arr_code = 'DXB'
                    elif 'Cairo' in arrival_airport:
                        arr_code = 'CAI'
                    elif 'Istanbul' in arrival_airport:
                        arr_code = 'IST'
                    elif 'London' in arrival_airport:
                        arr_code = 'LHR'
                    else:
                        # Fallback: look for 3-letter uppercase codes in the text
                        import re
                        codes = re.findall(r'\b[A-Z]{3}\b', arrival_airport)
                        arr_code = codes[0] if codes else arrival_airport[:3].upper()
                    
                    # Get passenger names, ticket numbers array, and PNR for this specific segment
                    segment_passengers = segment.get('passenger_names', [])
                    segment_ticket_numbers = segment.get('ticket_numbers', [])
                    segment_pnr = segment.get('pnr', '')
                    
                    # Build passenger and ticket info display with trip information on the left
                    passenger_ticket_info = ""
                    if segment_passengers or segment_ticket_numbers or segment_pnr:
                        passenger_ticket_info = '<div class="passenger-ticket-info">'
                        
                        # Create a row with trip info on left and passenger details on right
                        passenger_ticket_info += '<div class="passenger-trip-row">'
                        
                        # Left side: Trip information in black with full airport names
                        passenger_ticket_info += f'<div class="trip-info-left"><strong>Trip {trip_number}</strong> ({departure_airport} to {arrival_airport}), {airline} {flight_number}</div>'
                        
                        # Right side: Passenger details
                        passenger_ticket_info += '<div class="passenger-details-right">'
                        
                        # Display passengers with their individual ticket numbers lined up
                        if segment_passengers:
                            passenger_ticket_info += '<div class="passenger-names"><strong>Passengers:</strong><br>'
                            for i, passenger_name in enumerate(segment_passengers):
                                # Get corresponding ticket number for this passenger
                                ticket_number = ''
                                if i < len(segment_ticket_numbers) and segment_ticket_numbers[i]:
                                    ticket_number = f' (Ticket: {segment_ticket_numbers[i]})'
                                passenger_ticket_info += f'• {passenger_name}{ticket_number}<br>'
                            passenger_ticket_info += '</div>'
                        
                        # Display PNR in bold
                        if segment_pnr:
                            passenger_ticket_info += f'<div class="pnr-number"><strong>PNR: {segment_pnr}</strong></div>'
                        
                        passenger_ticket_info += '</div></div></div>'
                    
                    html_content += f"""
            <div class="flight-segment">
                <div class="flight-details">
                    <div class="departure-section">
                        <div class="section-label">Departure</div>
                        <div class="airport-time">{dep_code} | {departure_time}</div>
                        <div class="flight-date">{flight_date}</div>
                        <div class="airport-code">{dep_code}</div>
                    </div>
                    <div class="flight-middle">
                        <div class="flight-type">Non Stop</div>
                        <div class="aircraft-icon">✈</div>
                        <div class="baggage">25</div>
                    </div>
                    <div class="arrival-section">
                        <div class="section-label">Arrival</div>
                        <div class="airport-time">{arr_code} | {arrival_time}</div>
                        <div class="flight-date">{flight_date}</div>
                        <div class="airport-code">{arr_code}</div>
                    </div>
                </div>
                {passenger_ticket_info}
            </div>"""
            
            html_content += """
        </div>"""
        
        # Hotels Section (if hotel data exists)
        if hotel_data:
            html_content += f"""
        <div class="section">
            <div class="section-title">Hotels</div>
            <div class="hotel-header">
                <div class="hotel-main-name">{hotel_data.get('name', 'Hotel Name')}</div>
                <div class="hotel-main-address">{hotel_data.get('address', 'Hotel Address')}</div>
                <div class="hotel-main-phone">Phone: {hotel_data.get('phone', 'N/A')}</div>
            </div>
            <table class="hotel-details-table">
                <thead>
                    <tr>
                        <th>Check-In</th>
                        <th>Check-Out</th>
                        <th>Nights</th>
                        <th>Room Type</th>
                        <th>Board Basis</th>
                        <th>Lead Guest</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td>{hotel_data.get('checkin_date', 'N/A')}</td>
                        <td>{hotel_data.get('checkout_date', 'N/A')}</td>
                        <td>{hotel_data.get('nights', 'N/A')}</td>
                        <td>{hotel_data.get('room_type', 'Standard Room')}</td>
                        <td>{hotel_data.get('meal_plan', 'Room Only')}</td>
                        <td>{hotel_data.get('primary_guest', customer.first_name + ' ' + customer.last_name if customer else 'Guest')}</td>
                    </tr>
                </tbody>
            </table>
        </div>"""
        
        # Footer
        html_content += """
        <div class="footer">
            <div style="margin-bottom: 5px; font-size: 10px;">
                <strong>Banking:</strong> Arabi Travel Bank USD: 9070-142464-510 | Bank Of Palestine: 0458/2220908/001/3000/000 | Arab Bank: 142464
            </div>
            <div style="font-size: 10px;">
                <strong>Contact:</strong> sales@arabtravel.ps | www.arabtravel.ps | +97022956640 | Alersal St, zakat Bld, Ramallah, P.O.BOX: 27
            </div>
        </div>
    </div>
</body>
</html>"""
        
        return html_content
    
    def _extract_flight_data(self, service_items):
        """Extract flight data from service items and confirmation documents"""
        flight_items = [item for item in service_items if item.service_type == 'FLIGHT']
        
        if not flight_items:
            return None
        
        # Initialize flight data with segments array
        flight_data = {
            'segments': [],
            'passenger_names': [],
            'ticket_numbers': []
        }
        
        # Process ALL flight items and their confirmation documents
        for flight_item in flight_items:
            for document in flight_item.documents:
                if document.document_type == 'CONFIRMATION' and document.notes:
                    try:
                        import json
                        parsed_data = json.loads(document.notes)

                        
                        # Handle multi-segment flights
                        if 'segments' in parsed_data and parsed_data['segments']:

                            for i, segment in enumerate(parsed_data['segments']):
                                if segment.get('airline') and segment.get('flight_number'):
                                    # Copy segment data and add document-level PNR/ticket info if missing
                                    segment_with_pnr = segment.copy()
                                    if not segment_with_pnr.get('pnr') and parsed_data.get('pnr'):
                                        segment_with_pnr['pnr'] = parsed_data['pnr']
                                    if not segment_with_pnr.get('ticket_number') and parsed_data.get('ticket_number'):
                                        segment_with_pnr['ticket_number'] = parsed_data['ticket_number']
                                    if not segment_with_pnr.get('travel_class') and parsed_data.get('travel_class'):
                                        segment_with_pnr['travel_class'] = parsed_data['travel_class']
                                    
                                    flight_data['segments'].append(segment_with_pnr)

                        else:
                            # Handle single flight format - convert to segment
                            if parsed_data.get('airline') and parsed_data.get('flight_number'):
                                single_segment = {
                                    'airline': parsed_data.get('airline', ''),
                                    'flight_number': parsed_data.get('flight_number', ''),
                                    'departure_airport': parsed_data.get('departure_airport', ''),
                                    'arrival_airport': parsed_data.get('arrival_airport', ''),
                                    'flight_date': parsed_data.get('flight_date', ''),
                                    'departure_time': parsed_data.get('flight_time', ''),
                                    'arrival_time': parsed_data.get('arrival_time', ''),
                                    'duration': parsed_data.get('duration', ''),
                                    'connection_type': parsed_data.get('connection_type', ''),
                                    'aircraft_type': parsed_data.get('aircraft_type', ''),
                                    'pnr': parsed_data.get('pnr', ''),
                                    'ticket_number': parsed_data.get('ticket_number', ''),
                                    'travel_class': parsed_data.get('travel_class', ''),
                                }
                                flight_data['segments'].append(single_segment)

                        
                        # Collect passenger names and ticket numbers ONLY for the current document/flight
                        # Don't mix passenger names between different flight confirmations
                        if 'passenger_names' in parsed_data and parsed_data['passenger_names']:
                            # For multi-segment flights, assign passengers to the current segments only
                            current_doc_passengers = parsed_data['passenger_names']
                            current_doc_tickets = parsed_data.get('ticket_numbers', [])
                            segment_start_index = len(flight_data['segments']) - len(parsed_data.get('segments', [1]))
                            
                            # Assign passengers to segments from this document only
                            if 'segments' in parsed_data and parsed_data['segments']:
                                for i, segment in enumerate(parsed_data['segments']):
                                    segment_index = segment_start_index + i
                                    if segment_index < len(flight_data['segments']):
                                        # Store passenger names and ticket numbers for this specific segment
                                        flight_data['segments'][segment_index]['passenger_names'] = current_doc_passengers
                                        flight_data['segments'][segment_index]['ticket_numbers'] = current_doc_tickets
                            else:
                                # Single flight - assign to the last segment
                                if flight_data['segments']:
                                    flight_data['segments'][-1]['passenger_names'] = current_doc_passengers
                                    flight_data['segments'][-1]['ticket_numbers'] = current_doc_tickets
                            
                            # Also keep global passenger list for backward compatibility
                            if not flight_data['passenger_names']:  # Only if empty
                                flight_data['passenger_names'] = current_doc_passengers
                                flight_data['ticket_numbers'] = current_doc_tickets
                        
                        # Store segment-specific data without mixing between flights
                        # Each segment should keep its own PNR, ticket number, etc.
                        if 'segments' in parsed_data and parsed_data['segments']:
                            # For multi-segment format, data is already in segments
                            pass
                        else:
                            # For single flight, add the specific data to the segment we just created
                            if flight_data['segments']:
                                last_segment = flight_data['segments'][-1]
                                last_segment['pnr'] = parsed_data.get('pnr', '')
                                last_segment['ticket_number'] = parsed_data.get('ticket_number', '')
                                last_segment['travel_class'] = parsed_data.get('travel_class', '')
                                last_segment['terminal'] = parsed_data.get('terminal', '')
                        
                        # Only set global values if not already set (from first document)
                        if not flight_data.get('travel_class'):
                            flight_data['travel_class'] = parsed_data.get('travel_class', '')
                        if not flight_data.get('baggage_allowance'):
                            flight_data['baggage_allowance'] = parsed_data.get('baggage_allowance', '')
                        if not flight_data.get('seat_assignment'):
                            flight_data['seat_assignment'] = parsed_data.get('seat_assignment', '')
                        
                    except (json.JSONDecodeError, TypeError) as e:

                        pass
        
        # Remove duplicate passenger names
        if flight_data['passenger_names']:
            flight_data['passenger_names'] = list(dict.fromkeys(flight_data['passenger_names']))
        

        
        return flight_data if flight_data['segments'] else None
    
    def _extract_hotel_data(self, service_items):
        """Extract hotel data from service items and confirmation documents"""
        hotel_items = [item for item in service_items if item.service_type == 'HOTEL']
        
        if not hotel_items:
            return None
        
        hotel = hotel_items[0]
        
        # Initialize with defaults - DO NOT use hotel.description as it may be wrong
        hotel_data = {
            'name': 'Hotel Accommodation',  # Will be overridden by confirmation data
            'address': 'Hotel Address',
            'phone': 'N/A',
            'checkin_date': hotel.start_date.strftime("%d-%b-%Y") if hotel.start_date else "N/A",
            'checkout_date': hotel.end_date.strftime("%d-%b-%Y") if hotel.end_date else "N/A",
            'nights': (hotel.end_date - hotel.start_date).days if hotel.start_date and hotel.end_date else 1,
            'room_type': 'Standard Room',
            'meal_plan': 'Room Only',  # Will be overridden by confirmation data
            'description': hotel.description or 'Hotel accommodation'
        }
        
        print(f"DEBUG: Hotel description from ServiceItem: {hotel.description}")
        print(f"DEBUG: Number of documents for hotel: {len(hotel.documents)}")
        
        # Extract real data from confirmation documents  
        for document in hotel.documents:
            print(f"DEBUG: Checking document ID {document.id}")
            print(f"DEBUG: Document type: {document.document_type}")
            print(f"DEBUG: Document notes length: {len(document.notes) if document.notes else 0}")
            
            if document.document_type == 'CONFIRMATION' and document.notes:
                try:
                    # Parse JSON notes for confirmation details (this is where the real data is!)
                    import json
                    parsed_data = json.loads(document.notes)
                    print(f"DEBUG: Successfully parsed JSON from notes")
                    print(f"DEBUG: Parsed data keys: {list(parsed_data.keys())}")
                    print(f"DEBUG: Hotel name in parsed_data: '{parsed_data.get('hotel_name', 'NOT FOUND')}'")
                    
                    # Use real hotel name from confirmation
                    if 'hotel_name' in parsed_data and parsed_data['hotel_name']:
                        hotel_data['name'] = parsed_data['hotel_name']
                        print(f"DEBUG: Set hotel name to: '{hotel_data['name']}'")
                        
                    # Use real dates from confirmation
                    if 'from_date' in parsed_data and parsed_data['from_date']:
                        try:
                            from datetime import datetime
                            from_date = datetime.strptime(parsed_data['from_date'], '%Y-%m-%d')
                            hotel_data['checkin_date'] = from_date.strftime("%d-%b-%Y")
                        except:
                            hotel_data['checkin_date'] = parsed_data['from_date']
                    
                    if 'to_date' in parsed_data and parsed_data['to_date']:
                        try:
                            from datetime import datetime
                            to_date = datetime.strptime(parsed_data['to_date'], '%Y-%m-%d')
                            hotel_data['checkout_date'] = to_date.strftime("%d-%b-%Y")
                            
                            # Calculate real nights from confirmation dates
                            if 'from_date' in parsed_data:
                                from_date = datetime.strptime(parsed_data['from_date'], '%Y-%m-%d')
                                hotel_data['nights'] = (to_date - from_date).days
                        except:
                            hotel_data['checkout_date'] = parsed_data['to_date']
                    
                    # Extract room information
                    if 'rooms' in parsed_data and parsed_data['rooms']:
                        rooms_data = parsed_data['rooms']
                        # Handle new room array format with lead passenger names
                        if isinstance(rooms_data, list) and len(rooms_data) > 0:
                            # Extract lead passenger names from room array
                            lead_passengers = []
                            for room in rooms_data:
                                if 'lead_passenger' in room and room['lead_passenger']:
                                    lead_passengers.append(room['lead_passenger'])
                                # Also get room type from first room
                                if 'room_type' in room and room['room_type']:
                                    hotel_data['room_type'] = room['room_type']
                                if 'board_basis' in room and room['board_basis']:
                                    hotel_data['board_basis'] = room['board_basis']
                            
                            # Store lead passenger names for voucher display
                            if lead_passengers:
                                hotel_data['lead_passengers'] = lead_passengers
                                # Use first lead passenger for the main display
                                hotel_data['primary_guest'] = lead_passengers[0]
                        elif isinstance(rooms_data, dict):
                            # Handle legacy room format
                            # Convert string numbers to integers for comparison
                            single_count = int(rooms_data.get('single', 0))
                            double_count = int(rooms_data.get('double', 0))
                            twin_count = int(rooms_data.get('twin', 0))
                            triple_count = int(rooms_data.get('triple', 0))
                            
                            if single_count > 0:
                                hotel_data['room_type'] = 'Single Room'
                            elif double_count > 0:
                                hotel_data['room_type'] = 'Double Room'
                            elif twin_count > 0:
                                hotel_data['room_type'] = 'Twin Room'
                            elif triple_count > 0:
                                hotel_data['room_type'] = 'Triple Room'
                            elif rooms_data.get('other'):
                                hotel_data['room_type'] = rooms_data['other']
                    
                    # Extract meal plan from confirmation
                    if 'meal_plan' in parsed_data and parsed_data['meal_plan']:
                        hotel_data['meal_plan'] = parsed_data['meal_plan']
                                
                except (json.JSONDecodeError, TypeError) as e:
                    print(f"DEBUG: Failed to parse JSON from notes: {e}")
                    # If not JSON, treat as plain text
                    pass

        
        # Get hotel contact info from database using the real hotel name
        address, phone = self._get_hotel_contact_info(hotel_data['name'])
        if address:
            hotel_data['address'] = address
        if phone:
            hotel_data['phone'] = phone
        
        return hotel_data
    
    def _get_hotel_contact_info(self, hotel_name):
        """Look up hotel address and phone from CSV database"""
        if not hotel_name:
            return None, None
            
        try:
            csv_path = os.path.join(os.path.dirname(__file__), '../../attached_assets/hotelconswithaddress_1751201464690.csv')
            
            if not os.path.exists(csv_path):
                return None, None
                
            with open(csv_path, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    if hotel_name and row.get('Hotel Name'):
                        # Exact match for Barcelo Hotel Istanbul
                        if hotel_name.strip().lower() == row['Hotel Name'].strip().lower():
                            # Get full address from the CSV
                            address_parts = []
                            if row.get('Address'):
                                address_parts.append(row['Address'].strip())
                            if row.get('address line2') and row['address line2'].strip():
                                address_parts.append(row['address line2'].strip())
                            if row.get('Address line3') and row['Address line3'].strip():
                                address_parts.append(row['Address line3'].strip())
                            
                            # Join address parts properly
                            address = ', '.join([part for part in address_parts if part and part.strip() and part != ','])
                            
                            # Get phone number from address 4 column
                            phone = row.get('address 4', '').strip()
                            if not phone or '+' not in phone:
                                # Try other phone columns if available
                                phone = row.get('Address line4', '').strip()
                            
                            return address if address else None, phone if phone else None
                            
        except Exception as e:
            logging.error(f"Error reading hotel CSV: {e}")
            
        return None, None
    
    def generate_pdf(self):
        """Generate PDF from HTML content using weasyprint"""
        try:
            # Import weasyprint for HTML to PDF conversion
            from weasyprint import HTML
            
            # Generate the HTML content
            html_content = self.generate_html()
            
            # Create PDF from HTML with proper encoding
            html_doc = HTML(string=html_content, encoding='utf-8')
            
            # Generate PDF and return as BytesIO
            pdf_buffer = BytesIO()
            html_doc.write_pdf(pdf_buffer)
            pdf_buffer.seek(0)
            
            return pdf_buffer
            
        except ImportError as e:
            logging.error(f"Weasyprint not available: {e}")
            # Fallback: use reportlab for basic PDF generation
            return self._generate_pdf_reportlab()
        except Exception as e:
            logging.error(f"Error generating PDF with weasyprint: {e}")
            # Fallback to reportlab
            return self._generate_pdf_reportlab()
    
    def _generate_pdf_reportlab(self):
        """Fallback PDF generation using reportlab"""
        from reportlab.lib.pagesizes import A4
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.lib import colors
        from reportlab.lib.enums import TA_CENTER, TA_LEFT
        
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=18)
        
        # Get styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            textColor=colors.HexColor('#2E5A87'),
            alignment=TA_CENTER,
            spaceAfter=20
        )
        
        # Build content
        content = []
        
        # Header
        content.append(Paragraph("Arab Travel Group", title_style))
        content.append(Paragraph(f"Travel Voucher - {self.booking.reference_number}", styles['Heading2']))
        content.append(Spacer(1, 20))
        
        # Customer info
        if hasattr(self.booking, 'customer') and self.booking.customer:
            customer = self.booking.customer
            content.append(Paragraph(f"<b>Customer:</b> {customer.first_name} {customer.last_name}", styles['Normal']))
            if customer.email:
                content.append(Paragraph(f"<b>Email:</b> {customer.email}", styles['Normal']))
            if customer.phone:
                content.append(Paragraph(f"<b>Phone:</b> {customer.phone}", styles['Normal']))
            content.append(Spacer(1, 20))
        
        # Services
        for service in self.booking.service_items:
            if service.status == 'CONFIRMED':
                content.append(Paragraph(f"<b>{service.service_type}:</b> {service.description}", styles['Normal']))
                content.append(Paragraph(f"Dates: {service.start_date} to {service.end_date}", styles['Normal']))
                content.append(Spacer(1, 10))
        
        # Footer
        content.append(Spacer(1, 30))
        content.append(Paragraph("Arab Travel Group - Professional Travel Services", styles['Normal']))
        content.append(Paragraph("sales@arabtravel.ps | www.arabtravel.ps | +97022956640", styles['Normal']))
        
        # Build PDF
        doc.build(content)
        buffer.seek(0)
        return buffer
    
    def _prepare_passenger_data(self, customer):
        """Prepare passenger data from ALL flight segments to show complete passenger list with ticket numbers"""
        passengers = []
        added_passengers = set()  # Track unique passengers to avoid duplicates
        
        # Get flight data using the same logic as the voucher
        flight_data = self._extract_flight_data(self.booking.service_items)
        
        if flight_data and flight_data.get('segments'):
            # First, try to get passenger data from the most complete confirmation
            best_passenger_names = []
            best_ticket_numbers = []
            
            # Look for confirmations with both passenger names and ticket numbers
            for segment in flight_data['segments']:
                if 'passenger_names' in segment and segment['passenger_names']:
                    segment_passenger_names = segment['passenger_names']
                    segment_ticket_numbers = segment.get('ticket_numbers', [])
                    
                    # Use this segment if it has more complete data
                    if len(segment_passenger_names) > len(best_passenger_names):
                        best_passenger_names = segment_passenger_names
                        best_ticket_numbers = segment_ticket_numbers
            
            # If no segment-specific data, try global flight data
            if not best_passenger_names and flight_data.get('passenger_names'):
                best_passenger_names = flight_data['passenger_names']
                best_ticket_numbers = flight_data.get('ticket_numbers', [])
            
            # Create passenger list with sequential ticket assignment
            if best_passenger_names:
                for i, name in enumerate(best_passenger_names):
                    if name not in added_passengers:
                        # Get ticket number for this passenger (sequential assignment)
                        ticket_number = ''
                        if i < len(best_ticket_numbers) and best_ticket_numbers[i]:
                            ticket_number = best_ticket_numbers[i]
                        
                        passengers.append({
                            'name': name,
                            'type': 'Adult',
                            'ticket_number': ticket_number
                        })
                        added_passengers.add(name)
                
                return passengers
        
        # Final fallback to customer data if no confirmation passenger data
        if customer:
            full_name = f"Mr. {customer.first_name} {customer.last_name}" if customer.first_name and customer.last_name else "Passenger"
            passengers.append({
                'name': full_name,
                'type': 'Adult',
                'ticket_number': ''
            })
        
        return passengers