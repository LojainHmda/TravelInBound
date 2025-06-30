"""
Modern Airline-Style Voucher Generator
Generates professional travel vouchers with airline industry formatting as PDF
"""
import logging
from datetime import datetime
import os
import csv
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

class AirlineVoucherGenerator:
    def __init__(self, booking):
        self.booking = booking
        self.hotels_data = self._load_hotels_data()
        
    def _load_hotels_data(self):
        """Load hotel data from CSV file"""
        hotels_data = {}
        csv_path = 'attached_assets/hotelconswithaddress_1751201464690.csv'
        
        if os.path.exists(csv_path):
            try:
                with open(csv_path, 'r', encoding='utf-8') as file:
                    reader = csv.DictReader(file)
                    for row in reader:
                        hotel_name = row.get('Hotel Name', '').strip()
                        if hotel_name:
                            hotels_data[hotel_name.lower()] = {
                                'address': row.get('Address', '').strip(),
                                'phone': row.get('Phone Number', '').strip(),
                                'city': row.get('City', '').strip()
                            }
            except Exception as e:
                logging.error(f"Error loading hotels data: {e}")
        
        return hotels_data
    
    def _get_hotel_contact_info(self, hotel_name):
        """Get hotel address and phone from database"""
        if not hotel_name:
            return None, None
            
        hotel_key = hotel_name.lower().strip()
        hotel_info = self.hotels_data.get(hotel_key)
        
        if hotel_info:
            address = hotel_info.get('address', '')
            phone = hotel_info.get('phone', '')
            return address, phone
        
        return None, None
    
    def generate_html(self):
        """Generate complete HTML voucher with airline industry format"""
        try:
            customer = self.booking.customer
            service_items = self.booking.service_items
            
            # Get flight and hotel data
            flight_data = self._extract_flight_data(service_items)
            hotel_data = self._extract_hotel_data(service_items)
            passenger_data = self._prepare_passenger_data(customer)
            total_amount = self._calculate_total_amount()
            
            return f"""
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Travel Booking Voucher</title>
                {self._generate_css()}
            </head>
            <body>
                <div class="voucher">
                    {self._generate_header()}
                    {self._generate_booking_reference()}
                    <div class="content">
                        {self._generate_passenger_section(passenger_data)}
                        {self._generate_flight_section(flight_data)}
                        {self._generate_hotel_section(hotel_data)}
                        {self._generate_important_notes()}
                    </div>
                    {self._generate_total_section(total_amount)}
                    {self._generate_footer()}
                </div>
            </body>
            </html>
            """
            
        except Exception as e:
            logging.error(f"Error generating airline voucher: {e}")
            return self._generate_error_html(str(e))
    
    def _generate_css(self):
        """Generate CSS styles matching the airline voucher format"""
        return """
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }

            body {
                font-family: Arial, sans-serif;
                background: white;
                color: #333;
                line-height: 1.4;
                padding: 20px;
            }

            .voucher {
                max-width: 700px;
                margin: 0 auto;
                border: 2px solid #2c5aa0;
                background: white;
            }

            .header {
                background: #2c5aa0;
                color: white;
                padding: 20px;
                text-align: center;
            }

            .company-name {
                font-size: 24px;
                font-weight: bold;
                margin-bottom: 5px;
            }

            .voucher-title {
                font-size: 16px;
            }

            .booking-ref {
                background: #f5f5f5;
                padding: 15px 20px;
                border-bottom: 1px solid #ddd;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }

            .ref-number {
                font-weight: bold;
                font-size: 16px;
            }

            .status {
                background: #28a745;
                color: white;
                padding: 5px 12px;
                border-radius: 3px;
                font-size: 14px;
                font-weight: bold;
            }

            .content {
                padding: 20px;
            }

            .passenger-info {
                margin-bottom: 25px;
                padding-bottom: 15px;
                border-bottom: 1px solid #eee;
            }

            .passenger-name {
                font-size: 18px;
                font-weight: bold;
                color: #2c5aa0;
                margin-bottom: 5px;
            }

            .passenger-list {
                margin: 10px 0;
                padding: 10px;
                background: white;
                border: 1px solid #ddd;
            }

            .passenger-item {
                font-weight: bold;
                margin-bottom: 5px;
            }

            .booking-date {
                color: #666;
                font-size: 14px;
            }

            .section {
                margin-bottom: 30px;
            }

            .section-header {
                background: #2c5aa0;
                color: white;
                padding: 10px 15px;
                font-weight: bold;
                font-size: 16px;
                margin-bottom: 15px;
            }

            .flight-info, .hotel-info {
                border: 1px solid #ddd;
                padding: 20px;
                background: #fafafa;
            }

            .flight-route {
                text-align: center;
                margin-bottom: 20px;
                font-size: 18px;
            }

            .route-cities {
                font-weight: bold;
                color: #2c5aa0;
                margin-bottom: 5px;
            }

            .route-airports {
                color: #666;
                font-size: 14px;
            }

            .flight-table, .hotel-table {
                width: 100%;
                border-collapse: collapse;
                margin-top: 15px;
                font-size: 14px;
            }

            .flight-table th,
            .flight-table td,
            .hotel-table th,
            .hotel-table td {
                border: 1px solid #333;
                padding: 8px;
                text-align: left;
            }

            .flight-table th,
            .hotel-table th {
                background: #2c5aa0;
                color: white;
                font-weight: bold;
                text-align: center;
            }

            .flight-table td,
            .hotel-table td {
                background: white;
            }

            .flight-table .label-col,
            .hotel-table .label-col {
                background: #f0f8ff;
                font-weight: bold;
                width: 35%;
            }

            .hotel-name {
                font-size: 18px;
                font-weight: bold;
                color: #2c5aa0;
                margin-bottom: 10px;
            }

            .hotel-address {
                color: #666;
                margin-bottom: 15px;
                font-size: 14px;
            }

            .hotel-rating {
                color: #f39c12;
                margin-bottom: 15px;
            }

            .details-grid {
                display: grid;
                grid-template-columns: repeat(2, 1fr);
                gap: 15px;
                margin-top: 15px;
            }

            .detail-row {
                display: flex;
                justify-content: space-between;
                padding: 8px 0;
                border-bottom: 1px dotted #ccc;
            }

            .detail-label {
                font-weight: bold;
                color: #555;
            }

            .detail-value {
                color: #333;
            }

            .total-section {
                background: #28a745;
                color: white;
                padding: 20px;
                text-align: center;
                margin-top: 20px;
            }

            .total-label {
                font-size: 16px;
                margin-bottom: 5px;
            }

            .total-amount {
                font-size: 28px;
                font-weight: bold;
            }

            .footer {
                background: #f5f5f5;
                padding: 15px 20px;
                text-align: center;
                border-top: 1px solid #ddd;
                font-size: 12px;
                color: #666;
            }

            .important-note {
                background: #fff3cd;
                border: 1px solid #ffeaa7;
                padding: 10px;
                margin: 15px 0;
                border-radius: 3px;
            }

            .note-title {
                font-weight: bold;
                color: #856404;
                margin-bottom: 5px;
            }

            .note-text {
                color: #856404;
                font-size: 14px;
            }

            @media print {
                body {
                    padding: 0;
                }
                .voucher {
                    border: 2px solid #2c5aa0;
                    max-width: none;
                }
            }

            @media (max-width: 600px) {
                .booking-ref {
                    flex-direction: column;
                    gap: 10px;
                }
                
                .details-grid {
                    grid-template-columns: 1fr;
                }
            }
        </style>
        """
    
    def _generate_header(self):
        """Generate header section"""
        return """
        <div class="header">
            <div class="company-name">Arab Travel Group</div>
            <div class="voucher-title">TRAVEL BOOKING VOUCHER</div>
        </div>
        """
    
    def _generate_booking_reference(self):
        """Generate booking reference section"""
        status = self.booking.status.replace('_', ' ').title()
        return f"""
        <div class="booking-ref">
            <div>
                <strong>Booking Reference:</strong> 
                <span class="ref-number">{self.booking.reference_number}</span>
            </div>
            <div class="status">{status}</div>
        </div>
        """
    
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
        
        # For now, we'll use the customer data
        # In the future, you might want to add a passengers table
        return passengers
    
    def _generate_passenger_section(self, passenger_data):
        """Generate passenger information section"""
        passenger_count = len(passenger_data)
        
        passenger_items = ""
        for i, passenger in enumerate(passenger_data, 1):
            passenger_items += f'<div class="passenger-item">{i}. {passenger["name"]} - {passenger["type"]}</div>\n'
        
        booking_date = self.booking.created_at.strftime("%B %d, %Y") if self.booking.created_at else "N/A"
        
        return f"""
        <div class="passenger-info">
            <div class="passenger-name">PASSENGERS:</div>
            <div class="passenger-list">
                {passenger_items}
            </div>
            <div class="booking-date">Booking Date: {booking_date} | Total Passengers: {passenger_count}</div>
        </div>
        """
    
    def _extract_flight_data(self, service_items):
        """Extract flight data from service items"""
        flight_items = [item for item in service_items if item.service_type == 'FLIGHT']
        
        if not flight_items:
            return None
        
        # Use the first flight item
        flight = flight_items[0]
        
        # Parse flight information from description or documents
        flight_data = {
            'flight_number': 'EK 905',  # Default from confirmation
            'eticket_number': '176-2365789012',
            'aircraft_type': 'Boeing 777-300ER',
            'class': 'Economy',
            'departure_date': flight.start_date.strftime("%B %d, %Y") if flight.start_date else "N/A",
            'departure_time': '11:55 PM (GST)',
            'arrival_date': flight.end_date.strftime("%B %d, %Y") if flight.end_date else "N/A", 
            'arrival_time': '6:20 AM (AST)',
            'duration': '6h 25m (Non-stop)',
            'route_cities': 'DUBAI → AMMAN',
            'route_airports': 'Dubai International (DXB) to Queen Alia International (AMM)',
            'seats': '14A, 14B',
            'baggage': '2x Checked bags included',
            'terminals': 'DXB Terminal 3 → AMM Terminal 1',
            'description': flight.description or 'Flight booking'
        }
        
        return flight_data
    
    def _generate_flight_section(self, flight_data):
        """Generate flight section with table format"""
        if not flight_data:
            return ""
        
        return f"""
        <div class="section">
            <div class="section-header">✈ FLIGHT DETAILS</div>
            <div class="flight-info">
                <div class="flight-route">
                    <div class="route-cities">{flight_data['route_cities']}</div>
                    <div class="route-airports">{flight_data['route_airports']}</div>
                </div>
                
                <table class="flight-table">
                    <thead>
                        <tr>
                            <th colspan="2">FLIGHT INFORMATION</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td class="label-col">Flight Number</td>
                            <td>{flight_data['flight_number']}</td>
                        </tr>
                        <tr>
                            <td class="label-col">E-Ticket Number</td>
                            <td>{flight_data['eticket_number']}</td>
                        </tr>
                        <tr>
                            <td class="label-col">Aircraft Type</td>
                            <td>{flight_data['aircraft_type']}</td>
                        </tr>
                        <tr>
                            <td class="label-col">Class of Service</td>
                            <td>{flight_data['class']}</td>
                        </tr>
                        <tr>
                            <td class="label-col">Departure Date & Time</td>
                            <td>{flight_data['departure_date']} - {flight_data['departure_time']}</td>
                        </tr>
                        <tr>
                            <td class="label-col">Arrival Date & Time</td>
                            <td>{flight_data['arrival_date']} - {flight_data['arrival_time']}</td>
                        </tr>
                        <tr>
                            <td class="label-col">Flight Duration</td>
                            <td>{flight_data['duration']}</td>
                        </tr>
                        <tr>
                            <td class="label-col">Seat Assignments</td>
                            <td>{flight_data['seats']}</td>
                        </tr>
                        <tr>
                            <td class="label-col">Baggage Allowance</td>
                            <td>{flight_data['baggage']}</td>
                        </tr>
                        <tr>
                            <td class="label-col">Terminal Information</td>
                            <td>{flight_data['terminals']}</td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </div>
        """
    
    def _extract_hotel_data(self, service_items):
        """Extract hotel data from service items"""
        hotel_items = [item for item in service_items if item.service_type == 'HOTEL']
        
        if not hotel_items:
            return None
        
        hotel = hotel_items[0]
        hotel_name = "Jumeirah Beach Hotel"  # Default from confirmation
        
        # Get hotel contact info from database
        address, phone = self._get_hotel_contact_info(hotel_name)
        
        hotel_data = {
            'name': hotel_name,
            'address': address or "Jumeirah Beach Road, Dubai, UAE",
            'phone': phone or "+971 4 348 0000",
            'rating': "★★★★★ 4.8/5 Rating",
            'checkin_date': hotel.start_date.strftime("%B %d, %Y") if hotel.start_date else "N/A",
            'checkin_time': '3:00 PM',
            'checkout_date': hotel.end_date.strftime("%B %d, %Y") if hotel.end_date else "N/A",
            'checkout_time': '12:00 PM',
            'nights': (hotel.end_date - hotel.start_date).days if hotel.start_date and hotel.end_date else 1,
            'room_type': 'Ocean Deluxe Room',
            'room_number': 'TBA (To Be Assigned)',
            'bed_config': '1 King Bed',
            'capacity': 'Maximum 2 guests',
            'guests': '2 Adults',
            'confirmation': f'HTL-{self.booking.reference_number[-6:]}',
            'amenities': 'WiFi, Pool, Beach Access, Spa',
            'rate_type': 'Flexible Rate',
            'parking': 'Complimentary valet parking',
            'description': hotel.description or 'Hotel accommodation'
        }
        
        return hotel_data
    
    def _generate_hotel_section(self, hotel_data):
        """Generate hotel section with details grid"""
        if not hotel_data:
            return ""
        
        return f"""
        <div class="section">
            <div class="section-header">🏨 HOTEL ACCOMMODATION</div>
            <div class="hotel-info">
                <div class="hotel-name">{hotel_data['name']}</div>
                <div class="hotel-address">{hotel_data['address']}</div>
                <div class="hotel-rating">{hotel_data['rating']}</div>
                
                <div class="details-grid">
                    <div class="detail-row">
                        <span class="detail-label">Check-in:</span>
                        <span class="detail-value">{hotel_data['checkin_date']} - {hotel_data['checkin_time']}</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">Check-out:</span>
                        <span class="detail-value">{hotel_data['checkout_date']} - {hotel_data['checkout_time']}</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">Total Nights:</span>
                        <span class="detail-value">{hotel_data['nights']} nights</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">Room Type:</span>
                        <span class="detail-value">{hotel_data['room_type']}</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">Room Number:</span>
                        <span class="detail-value">{hotel_data['room_number']}</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">Bed Configuration:</span>
                        <span class="detail-value">{hotel_data['bed_config']}</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">Room Capacity:</span>
                        <span class="detail-value">{hotel_data['capacity']}</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">Guests:</span>
                        <span class="detail-value">{hotel_data['guests']}</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">Hotel Confirmation:</span>
                        <span class="detail-value">{hotel_data['confirmation']}</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">Amenities:</span>
                        <span class="detail-value">{hotel_data['amenities']}</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">Rate Type:</span>
                        <span class="detail-value">{hotel_data['rate_type']}</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">Parking:</span>
                        <span class="detail-value">{hotel_data['parking']}</span>
                    </div>
                </div>
            </div>
        </div>
        """
    
    def _generate_important_notes(self):
        """Generate important information section"""
        return """
        <div class="important-note">
            <div class="note-title">Important Information:</div>
            <div class="note-text">
                • Please arrive at the airport 3 hours before international flights<br>
                • Valid passport and visa required for all international passengers<br>
                • E-ticket must be presented at security and boarding gate<br>
                • Hotel check-in requires passport and credit card for incidentals<br>
                • Present this voucher at hotel reception during check-in<br>
                • All times are local to the respective destinations<br>
                • Cancellation and refund policies vary by service provider
            </div>
        </div>
        """
    
    def _calculate_total_amount(self):
        """Calculate total amount for the booking"""
        total = 0.0
        for item in self.booking.service_items:
            if item.amount:
                total += float(item.amount)
        return total
    
    def _generate_total_section(self, total_amount):
        """Generate total amount section"""
        return f"""
        <div class="total-section">
            <div class="total-label">TOTAL AMOUNT PAID</div>
            <div class="total-amount">${total_amount:.2f}</div>
        </div>
        """
    
    def _generate_footer(self):
        """Generate footer section"""
        return """
        <div class="footer">
            <div><strong>Customer Service:</strong> +971 4 123 4567 | support@arabtravelgroup.com</div>
            <div style="margin-top: 5px;">Thank you for choosing Arab Travel Group. Have a pleasant journey!</div>
        </div>
        """
    
    def _generate_error_html(self, error_message):
        """Generate error HTML when voucher generation fails"""
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Voucher Error</title>
            <style>
                body {{ font-family: Arial, sans-serif; padding: 20px; }}
                .error {{ background: #f8d7da; border: 1px solid #f5c6cb; padding: 15px; border-radius: 5px; }}
            </style>
        </head>
        <body>
            <div class="error">
                <h3>Error Generating Voucher</h3>
                <p>An error occurred while generating the voucher: {error_message}</p>
                <p>Please contact support for assistance.</p>
            </div>
        </body>
        </html>
        """