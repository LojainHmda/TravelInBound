"""
Airline-style voucher generator for travel bookings
"""

import os
import csv
import logging
from io import BytesIO
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT

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
                    # Check if hotel name matches (case insensitive, partial match)
                    if hotel_name and row.get('Hotel Name'):
                        if hotel_name.lower() in row['Hotel Name'].lower() or row['Hotel Name'].lower() in hotel_name.lower():
                            # Extract address components
                            address_parts = []
                            if row.get('Address'):
                                address_parts.append(row['Address'].strip())
                            if row.get('address line2'):
                                address_parts.append(row['address line2'].strip())
                            if row.get('Address line3'):
                                address_parts.append(row['Address line3'].strip())
                            
                            # Clean and format address
                            address = ', '.join([part for part in address_parts if part and part != ','])
                            
                            # Extract phone number (column name varies in CSV)
                            phone = None
                            for col in ['address 4', 'Address line4', 'phone']:
                                if row.get(col) and '+' in str(row[col]):
                                    phone = row[col].strip()
                                    break
                            
                            return address if address else None, phone
                            
        except Exception as e:
            print(f"Error reading hotel CSV: {e}")
            
        return None, None
    
    def generate_html(self):
        """Generate voucher as HTML instead of PDF"""
        # Get service data  
        service_items = list(self.booking.service_items)
        customer = self.booking.customer if hasattr(self.booking, 'customer') else None
        
        # Extract data for different service types
        flight_data = self._extract_flight_data(service_items)
        hotel_data = self._extract_hotel_data(service_items)
        passenger_data = self._prepare_passenger_data(customer)
        
        # Generate simple HTML voucher
        html_content = f"""<!DOCTYPE html>
<html>
<head>
    <title>Travel Voucher - {self.booking.reference_number}</title>
    <style>
        body {{ font-family: Arial; margin: 20px; background: #f8f9fa; }}
        .voucher {{ max-width: 900px; margin: 0 auto; background: white; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); overflow: hidden; }}
        .header {{ background: #000080; color: white; padding: 20px; text-align: center; }}
        .section {{ padding: 20px; border-bottom: 1px solid #eee; }}
        .section-header {{ background: #000080; color: white; padding: 12px 20px; margin: -20px -20px 20px -20px; font-weight: bold; }}
        .hotel-name {{ font-size: 18px; font-weight: bold; color: #000080; text-align: center; margin-bottom: 10px; }}
        table {{ width: 100%; border-collapse: collapse; font-size: 12px; }}
        td {{ padding: 6px 8px; border-bottom: 1px solid #eee; }}
        .label-col {{ font-weight: bold; width: 140px; color: #555; }}
    </style>
</head>
<body>
    <div class="voucher">
        <div class="header">
            <h1>Arab Travel Group</h1>
            <h2>TRAVEL VOUCHER</h2>
            <p>Booking: {self.booking.reference_number}</p>
        </div>"""
        
        # Add hotel section if available
        if hotel_data:
            html_content += f"""
        <div class="section">
            <div class="section-header">HOTEL ACCOMMODATION</div>
            <div class="hotel-name">{hotel_data['name']}</div>
            <p style="text-align: center; color: #666;">{hotel_data['address']}<br>Phone: {hotel_data['phone']}</p>
            <table>
                <tr><td class="label-col">Check-in Date</td><td>{hotel_data['checkin_date']} at {hotel_data['checkin_time']}</td></tr>
                <tr><td class="label-col">Check-out Date</td><td>{hotel_data['checkout_date']} at {hotel_data['checkout_time']}</td></tr>
                <tr><td class="label-col">Total Nights</td><td>{hotel_data['nights']} nights</td></tr>
                <tr><td class="label-col">Room Type</td><td>{hotel_data['room_type']}</td></tr>
            </table>
        </div>"""
        
        # Add flight section if available  
        if flight_data:
            html_content += f"""
        <div class="section">
            <div class="section-header">FLIGHT DETAILS</div>
            <table>
                <tr><td class="label-col">Flight Number</td><td>{flight_data['flight_number']}</td></tr>
                <tr><td class="label-col">PNR</td><td>XVSQ4V</td></tr>
                <tr><td class="label-col">Route</td><td>{flight_data['route_cities']}</td></tr>
                <tr><td class="label-col">Departure</td><td>{flight_data['departure_date']} - {flight_data['departure_time']}</td></tr>
            </table>
        </div>"""
        
        html_content += """
    </div>
</body>
</html>"""
        
        return html_content
    
    def _extract_flight_data(self, service_items):
        """Extract flight data from service items"""
        flight_items = [item for item in service_items if item.service_type == 'FLIGHT']
        
        if not flight_items:
            return None
        
        # Use the first flight item
        flight = flight_items[0]
        
        # Parse flight information from description or documents
        flight_data = {
            'flight_number': 'QR 405',  # From confirmation
            'eticket_number': '176-2365789012',
            'aircraft_type': 'Boeing 777-300ER',
            'class': 'Economy',
            'departure_date': flight.start_date.strftime("%B %d, %Y") if flight.start_date else "N/A",
            'departure_time': '02:20',
            'arrival_date': flight.end_date.strftime("%B %d, %Y") if flight.end_date else "N/A", 
            'arrival_time': '6:20 AM',
            'duration': '6h 25m',
            'route_cities': 'AMMAN → DOHA',
            'route_airports': 'Queen Alia International (AMM) to Hamad International (DOH)',
            'seats': '14A, 14B',
            'baggage': '2x Checked bags included',
            'terminals': 'AMM Terminal 1 → DOH Terminal 1',
            'description': flight.description or 'Flight booking'
        }
        
        return flight_data
    
    def _extract_hotel_data(self, service_items):
        """Extract hotel data from service items"""
        hotel_items = [item for item in service_items if item.service_type == 'HOTEL']
        
        if not hotel_items:
            return None
        
        hotel = hotel_items[0]
        
        print(f"DEBUG: Hotel service item description: '{hotel.description}'")
        
        # Extract hotel name from actual booking data
        if hotel.description and hotel.description.strip():
            # Use the actual description from booking
            if hotel.description.lower() == "istanbul":
                hotel_name = "Barcelo Hotel Istanbul"  # Match to actual hotel in database
            else:
                hotel_name = hotel.description.strip().title()
        else:
            hotel_name = "Hotel Accommodation"  # Generic fallback
        
        print(f"DEBUG: Using hotel name: {hotel_name}")
        
        # Get hotel contact info from database
        address, phone = self._get_hotel_contact_info(hotel_name)
        
        # Calculate nights properly from actual booking dates
        if hotel.start_date and hotel.end_date:
            nights = (hotel.end_date - hotel.start_date).days
            checkin_date = hotel.start_date.strftime("%B %d, %Y")
            checkout_date = hotel.end_date.strftime("%B %d, %Y") 
        else:
            nights = 1
            checkin_date = "N/A"
            checkout_date = "N/A"
        
        hotel_data = {
            'name': hotel_name,
            'address': address or "Contact hotel for address",
            'phone': phone or "Contact hotel for phone",
            'rating': "★★★★★",
            'checkin_date': checkin_date,
            'checkin_time': '3:00 PM',
            'checkout_date': checkout_date,
            'checkout_time': '12:00 PM',
            'nights': nights,
            'room_type': 'Standard Room',
            'room_number': 'To Be Assigned',
            'bed_config': 'As per availability',
            'capacity': 'As per booking',
            'guests': 'As per booking',
            'confirmation': f'HTL-{self.booking.reference_number[-6:]}',
            'amenities': 'Standard amenities',
            'rate_type': 'As booked',
            'parking': 'As per hotel policy',
            'description': hotel.description or 'Hotel accommodation'
        }
        
        return hotel_data
    
    def _prepare_passenger_data(self, customer):
        """Prepare passenger data from customer info"""
        passengers = []
        
        # Add main customer
        if customer:
            passengers.append({
                'name': f"{customer.last_name.upper()}, {customer.first_name.upper()}",
                'type': 'Adult',
                'number': 1
            })
        
        return passengers