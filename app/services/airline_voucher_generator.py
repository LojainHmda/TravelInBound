"""
Airline-style voucher generator matching the exact template provided
"""

import os
import csv
import logging
from datetime import datetime

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
    
    def generate_html(self):
        """Generate voucher HTML matching the exact template layout"""
        service_items = list(self.booking.service_items)
        customer = self.booking.customer if hasattr(self.booking, 'customer') else None
        
        # Extract actual booking data
        flight_data = self._extract_flight_data(service_items)
        hotel_data = self._extract_hotel_data(service_items)
        passenger_data = self._prepare_passenger_data(customer)
        
        # Generate HTML exactly matching the template
        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Travel Voucher - {self.booking.reference_number}</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
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
        .orange-header {{
            background-color: #FFA500;
            height: 20px;
            width: 100%;
        }}
        .section {{
            padding: 20px;
        }}
        .section-title {{
            font-size: 16px;
            font-weight: bold;
            color: #2E5A87;
            margin-bottom: 15px;
            border-bottom: 1px solid #ddd;
            padding-bottom: 5px;
        }}
        .info-table {{
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 20px;
        }}
        .info-table td {{
            padding: 8px 10px;
            border-bottom: 1px solid #eee;
            font-size: 14px;
        }}
        .info-table .label {{
            font-weight: bold;
            width: 150px;
            background-color: #f8f9fa;
        }}
        .passenger-table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 10px;
            border: 1px solid #ddd;
        }}
        .passenger-table th {{
            background-color: #f8f9fa;
            padding: 10px;
            text-align: left;
            font-weight: bold;
            border: 1px solid #ddd;
        }}
        .passenger-table td {{
            padding: 10px;
            border: 1px solid #ddd;
            text-align: left;
        }}
        .flight-table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 10px;
            border: 1px solid #ddd;
        }}
        .flight-table th {{
            background-color: #f8f9fa;
            padding: 8px;
            text-align: center;
            font-weight: bold;
            border: 1px solid #ddd;
            font-size: 12px;
        }}
        .flight-table td {{
            padding: 8px;
            border: 1px solid #ddd;
            text-align: center;
            font-size: 12px;
        }}
        .hotel-table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 10px;
            border: 1px solid #ddd;
        }}
        .hotel-table th {{
            background-color: #f8f9fa;
            padding: 8px;
            text-align: center;
            font-weight: bold;
            border: 1px solid #ddd;
            font-size: 12px;
        }}
        .hotel-table td {{
            padding: 8px;
            border: 1px solid #ddd;
            text-align: left;
            font-size: 12px;
        }}
        .footer {{
            text-align: center;
            padding: 15px;
            background-color: #f8f9fa;
            border-top: 1px solid #ddd;
        }}
        .footer-title {{
            font-weight: bold;
            color: #2E5A87;
            margin-bottom: 5px;
        }}
        @media print {{
            body {{ background: white; padding: 0; }}
            .voucher-container {{ border: none; }}
        }}
    </style>
</head>
<body>
    <div class="voucher-container">
        <div class="orange-header"></div>
        
        <!-- Booking Information Section -->
        <div class="section">
            <div class="section-title">Booking Information</div>
            <table class="info-table">
                <tr>
                    <td class="label">Booking ID</td>
                    <td>{self.booking.reference_number}</td>
                </tr>
                <tr>
                    <td class="label">Booking Date</td>
                    <td>{self.booking.created_at.strftime('%d-%m-%Y (%A)') if self.booking.created_at else 'N/A'}</td>
                </tr>
                <tr>
                    <td class="label">GDS PNR</td>
                    <td>XVSQ4V</td>
                </tr>
                <tr>
                    <td class="label">Contact Tel</td>
                    <td>{customer.phone if customer and customer.phone else '+97022956640'}</td>
                </tr>
                <tr>
                    <td class="label">Email</td>
                    <td>{customer.email if customer and customer.email else 'info@arabtravel.ps'}</td>
                </tr>
            </table>
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
            <div class="section-title">Flights</div>
            <table class="flight-table">
                <thead>
                    <tr>
                        <th>Trip</th>
                        <th>Flight</th>
                        <th>From</th>
                        <th>To</th>
                        <th>Date</th>
                        <th>Departure</th>
                        <th>Arrival</th>
                        <th>Duration</th>
                        <th>Aircraft</th>
                        <th>Connection</th>
                        <th>Class</th>
                        <th>Baggage</th>
                        <th>PNR</th>
                        <th>Ticket No</th>
                    </tr>
                </thead>
                <tbody>"""
            
            # Handle multi-segment flight data
            if 'segments' in flight_data and flight_data['segments']:
                # Process each flight segment
                for i, segment in enumerate(flight_data['segments']):
                    trip_number = i + 1
                    departure_airport = segment.get('departure_airport', '')
                    arrival_airport = segment.get('arrival_airport', '')
                    pnr = segment.get('pnr', '')
                    print(f"DEBUG: Rendering segment {i}: airline={segment.get('airline')}, departure={departure_airport}, arrival={arrival_airport}, pnr={pnr}")
                    print(f"DEBUG: HTML values - departure='{departure_airport}', arrival='{arrival_airport}', pnr='{pnr}'")
                    html_content += f"""
                    <tr>
                        <td>{trip_number}</td>
                        <td>{segment.get('airline', '')} {segment.get('flight_number', '')}</td>
                        <td>{departure_airport}</td>
                        <td>{arrival_airport}</td>
                        <td>{segment.get('flight_date', '')}</td>
                        <td>{segment.get('departure_time', '')}</td>
                        <td>{segment.get('arrival_time', '')}</td>
                        <td>{segment.get('duration', '')}</td>
                        <td>{segment.get('aircraft_type', '')}</td>
                        <td>{segment.get('connection_type', '')}</td>
                        <td>{segment.get('travel_class', flight_data.get('travel_class', ''))}</td>
                        <td>{flight_data.get('baggage_allowance', '')}</td>
                        <td>{pnr}</td>
                        <td>{segment.get('ticket_number', '')}</td>
                    </tr>"""
            else:
                # Fallback to single flight format for backward compatibility
                html_content += f"""
                    <tr>
                        <td>1</td>
                        <td>{flight_data.get('airline', '')} {flight_data.get('flight_number', '')}</td>
                        <td>{flight_data.get('departure_airport', '')}</td>
                        <td>{flight_data.get('arrival_airport', '')}</td>
                        <td>{flight_data.get('flight_date', '')}</td>
                        <td>{flight_data.get('flight_time', '')}</td>
                        <td>{flight_data.get('arrival_time', '')}</td>
                        <td>{flight_data.get('duration', '')}</td>
                        <td>{flight_data.get('aircraft_type', '')}</td>
                        <td>{flight_data.get('connection_type', '')}</td>
                        <td>{flight_data.get('travel_class', '')}</td>
                        <td>{flight_data.get('baggage_allowance', '')}</td>
                        <td>{flight_data.get('pnr', '')}</td>
                        <td>{flight_data.get('ticket_number', '')}</td>
                    </tr>"""
            
            html_content += """
                </tbody>
            </table>
        </div>"""
        
        # Hotels Section (if hotel data exists)
        if hotel_data:
            html_content += f"""
        <div class="section">
            <div class="section-title">Hotels</div>
            <table class="hotel-table">
                <thead>
                    <tr>
                        <th>Hotel</th>
                        <th>Address</th>
                        <th>Check-In</th>
                        <th>Check-Out</th>
                        <th>Nights</th>
                        <th>Rooms</th>
                        <th>Room Type</th>
                        <th>Board</th>
                        <th>Lead Guest</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td style="font-weight: bold;">{hotel_data.get('name', 'Hotel Name')}</td>
                        <td>{hotel_data.get('address', 'Hotel Address')}<br>Phone: {hotel_data.get('phone', 'N/A')}</td>
                        <td>{hotel_data.get('checkin_date', 'N/A')}</td>
                        <td>{hotel_data.get('checkout_date', 'N/A')}</td>
                        <td>{hotel_data.get('nights', 'N/A')}</td>
                        <td>1</td>
                        <td>{hotel_data.get('room_type', 'Standard Room')}</td>
                        <td>{hotel_data.get('meal_plan', 'Room Only')}</td>
                        <td>{customer.first_name + ' ' + customer.last_name if customer else 'Guest'}</td>
                    </tr>
                </tbody>
            </table>
        </div>"""
        
        # Footer
        html_content += """
        <div class="footer">
            <div class="footer-title">ARABI TRAVEL</div>
            <div>Banking Information</div>
            <div>Arabi Travel, Ramallah, Palestine. PO Box 224146 S19</div>
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
            'passenger_names': []
        }
        
        # Process ALL flight items and their confirmation documents
        for flight_item in flight_items:
            for document in flight_item.documents:
                if document.document_type == 'CONFIRMATION' and document.notes:
                    try:
                        import json
                        parsed_data = json.loads(document.notes)
                        print(f"DEBUG: Processing flight document {document.id} with keys: {list(parsed_data.keys())}")
                        
                        # Handle multi-segment flights
                        if 'segments' in parsed_data and parsed_data['segments']:
                            print(f"DEBUG: Found {len(parsed_data['segments'])} segments in document {document.id}")
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
                                    print(f"DEBUG: Added segment {i}: {segment['airline']} {segment['flight_number']} with PNR {segment_with_pnr.get('pnr', 'NONE')}")
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
                                print(f"DEBUG: Converted single flight to segment: {single_segment['airline']} {single_segment['flight_number']}")
                        
                        # Collect passenger names from all documents (combine them)
                        if 'passenger_names' in parsed_data and parsed_data['passenger_names']:
                            flight_data['passenger_names'].extend(parsed_data['passenger_names'])
                        
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
                        print(f"DEBUG: Failed to parse flight JSON from document {document.id}: {e}")
                        pass
        
        # Remove duplicate passenger names
        if flight_data['passenger_names']:
            flight_data['passenger_names'] = list(dict.fromkeys(flight_data['passenger_names']))
        
        print(f"DEBUG: Final flight_data has {len(flight_data['segments'])} total segments and {len(flight_data['passenger_names'])} passengers")
        
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
                        if isinstance(rooms_data, dict):
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
    
    def _prepare_passenger_data(self, customer):
        """Prepare passenger data from confirmation documents and customer info"""
        passengers = []
        
        # First try to get passenger data from confirmation documents
        service_items = list(self.booking.service_items)
        for item in service_items:
            for document in item.documents:
                if document.document_type == 'CONFIRMATION' and document.notes:
                    try:
                        import json
                        parsed_data = json.loads(document.notes)
                        if 'passenger_names' in parsed_data and parsed_data['passenger_names']:
                            # Use real passenger names from confirmation
                            ticket_number = parsed_data.get('ticket_number', '')
                            for i, name in enumerate(parsed_data['passenger_names']):
                                passengers.append({
                                    'name': name,
                                    'type': 'Adult',
                                    'ticket_number': ticket_number
                                })
                            return passengers
                    except (json.JSONDecodeError, TypeError):
                        pass
        
        # Fallback to customer data if no confirmation passenger data
        if customer:
            full_name = f"Mr. {customer.first_name} {customer.last_name}" if customer.first_name and customer.last_name else "Passenger"
            passengers.append({
                'name': full_name,
                'type': 'Adult',
                'ticket_number': ''
            })
        
        return passengers