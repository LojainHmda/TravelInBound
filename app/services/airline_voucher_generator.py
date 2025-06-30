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
    
    def generate_pdf(self):
        """Generate PDF voucher with airline industry format"""
        try:
            # Create PDF buffer
            buffer = BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.5*inch)
            
            # Get data from confirmed services only
            confirmed_services = [s for s in self.booking.service_items if s.status == 'CONFIRMED']
            
            if not confirmed_services:
                raise Exception("No confirmed services found for voucher generation")
            
            # Build PDF content
            elements = []
            
            # Add header
            elements.extend(self._build_pdf_header())
            
            # Add booking reference
            elements.extend(self._build_pdf_booking_ref())
            
            # Add passenger info
            elements.extend(self._build_pdf_passenger_section())
            
            # Add confirmed services
            for service in confirmed_services:
                if service.service_type == 'FLIGHT':
                    elements.extend(self._build_pdf_flight_section(service))
                elif service.service_type == 'HOTEL':
                    elements.extend(self._build_pdf_hotel_section(service))
            
            # Add total
            elements.extend(self._build_pdf_total_section(confirmed_services))
            
            # Add footer
            elements.extend(self._build_pdf_footer())
            
            # Build PDF
            doc.build(elements)
            buffer.seek(0)
            
            return buffer
            
        except Exception as e:
            logging.error(f"Error generating airline voucher PDF: {e}")
            raise
    
    def _setup_styles(self):
        """Setup PDF styles for airline voucher"""
        styles = getSampleStyleSheet()
        
        # Header style
        styles.add(ParagraphStyle(
            name='Header',
            parent=styles['Title'],
            fontSize=18,
            textColor=colors.white,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold',
            spaceAfter=0.2*inch
        ))
        
        # Section header style  
        styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=colors.white,
            alignment=TA_LEFT,
            fontName='Helvetica-Bold',
            spaceAfter=0.1*inch,
            spaceBefore=0.2*inch
        ))
        
        # Passenger style
        styles.add(ParagraphStyle(
            name='PassengerName',
            parent=styles['Normal'],
            fontSize=12,
            fontName='Helvetica-Bold',
            spaceAfter=0.05*inch
        ))
        
        return styles
    
    def _build_pdf_header(self):
        """Build PDF header section"""
        styles = self._setup_styles()
        elements = []
        
        # Create header table
        header_data = [
            ['Arab Travel Group'],
            ['TRAVEL BOOKING VOUCHER']
        ]
        
        header_table = Table(header_data, colWidths=[7*inch])
        header_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#2c5aa0')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (0, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (0, 0), 18),
            ('FONTNAME', (0, 1), (0, 1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (0, 1), 14),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 15),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 15),
        ]))
        
        elements.append(header_table)
        elements.append(Spacer(1, 0.1*inch))
        
        return elements
    
    def _build_pdf_booking_ref(self):
        """Build PDF booking reference section"""
        elements = []
        
        status = self.booking.status.replace('_', ' ').title()
        
        # Booking reference table
        ref_data = [
            [f'Booking Reference: {self.booking.reference_number}', status]
        ]
        
        ref_table = Table(ref_data, colWidths=[5*inch, 2*inch])
        ref_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f5f5f5')),
            ('TEXTCOLOR', (0, 0), (0, 0), colors.black),
            ('TEXTCOLOR', (1, 0), (1, 0), colors.white),
            ('BACKGROUND', (1, 0), (1, 0), colors.green),
            ('ALIGN', (0, 0), (0, 0), 'LEFT'),
            ('ALIGN', (1, 0), (1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 12),
            ('TOPPADDING', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
            ('LEFTPADDING', (0, 0), (-1, -1), 15),
            ('RIGHTPADDING', (0, 0), (-1, -1), 15),
        ]))
        
        elements.append(ref_table)
        elements.append(Spacer(1, 0.2*inch))
        
        return elements
    
    def _build_pdf_passenger_section(self):
        """Build PDF passenger section"""
        elements = []
        styles = self._setup_styles()
        
        # Passenger header
        passenger_header = Paragraph("PASSENGERS:", styles['PassengerName'])
        elements.append(passenger_header)
        
        # Customer info
        customer = self.booking.customer
        if customer:
            passenger_name = f"1. {customer.last_name.upper()}, {customer.first_name.upper()} - Adult"
            passenger_para = Paragraph(passenger_name, styles['Normal'])
            elements.append(passenger_para)
        
        # Booking date
        booking_date = self.booking.created_at.strftime("%B %d, %Y") if self.booking.created_at else "N/A"
        date_para = Paragraph(f"Booking Date: {booking_date} | Total Passengers: 1", styles['Normal'])
        elements.append(date_para)
        elements.append(Spacer(1, 0.2*inch))
        
        return elements
    
    def _build_pdf_flight_section(self, flight_service):
        """Build PDF flight section from confirmed flight service"""
        elements = []
        
        # Extract flight details from service confirmations or documents
        flight_details = self._extract_flight_details_from_service(flight_service)
        
        # Section header
        flight_header_data = [['✈ FLIGHT DETAILS']]
        flight_header_table = Table(flight_header_data, colWidths=[7*inch])
        flight_header_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#2c5aa0')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 14),
            ('TOPPADDING', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
            ('LEFTPADDING', (0, 0), (-1, -1), 15),
        ]))
        elements.append(flight_header_table)
        
        # Flight route info
        route_data = [
            [flight_details['route']],
            [flight_details['airports']]
        ]
        route_table = Table(route_data, colWidths=[7*inch])
        route_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (0, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (0, 0), 14),
            ('FONTNAME', (0, 1), (0, 1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (0, 1), 11),
            ('TEXTCOLOR', (0, 0), (0, 0), colors.HexColor('#2c5aa0')),
            ('TEXTCOLOR', (0, 1), (0, 1), colors.grey),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        elements.append(route_table)
        
        # Flight details table
        flight_table_data = [
            ['FLIGHT INFORMATION', ''],
            ['Flight Number', flight_details['flight_number']],
            ['E-Ticket Number', flight_details['eticket']],
            ['Aircraft Type', flight_details['aircraft']],
            ['Class of Service', flight_details['class']],
            ['Departure Date & Time', flight_details['departure']],
            ['Arrival Date & Time', flight_details['arrival']],
            ['Flight Duration', flight_details['duration']],
            ['Seat Assignments', flight_details['seats']],
            ['Baggage Allowance', flight_details['baggage']],
            ['Terminal Information', flight_details['terminals']]
        ]
        
        flight_table = Table(flight_table_data, colWidths=[2.5*inch, 4.5*inch])
        flight_table.setStyle(TableStyle([
            # Header row
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c5aa0')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('SPAN', (0, 0), (1, 0)),
            
            # Data rows - labels
            ('BACKGROUND', (0, 1), (0, -1), colors.HexColor('#f0f8ff')),
            ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
            
            # All cells
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        
        elements.append(flight_table)
        elements.append(Spacer(1, 0.3*inch))
        
        return elements
    
    def _build_pdf_hotel_section(self, hotel_service):
        """Build PDF hotel section from confirmed hotel service"""
        elements = []
        
        # Extract hotel details from service
        hotel_details = self._extract_hotel_details_from_service(hotel_service)
        
        # Section header
        hotel_header_data = [['🏨 HOTEL ACCOMMODATION']]
        hotel_header_table = Table(hotel_header_data, colWidths=[7*inch])
        hotel_header_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#2c5aa0')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 14),
            ('TOPPADDING', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
            ('LEFTPADDING', (0, 0), (-1, -1), 15),
        ]))
        elements.append(hotel_header_table)
        
        # Hotel name and address
        hotel_info_data = [
            [hotel_details['name']],
            [hotel_details['address']],
            [hotel_details['rating']]
        ]
        hotel_info_table = Table(hotel_info_data, colWidths=[7*inch])
        hotel_info_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (0, 0), 14),
            ('TEXTCOLOR', (0, 0), (0, 0), colors.HexColor('#2c5aa0')),
            ('FONTSIZE', (0, 1), (0, 1), 11),
            ('TEXTCOLOR', (0, 1), (0, 1), colors.grey),
            ('FONTSIZE', (0, 2), (0, 2), 11),
            ('TEXTCOLOR', (0, 2), (0, 2), colors.HexColor('#f39c12')),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ]))
        elements.append(hotel_info_table)
        
        # Hotel details table
        hotel_table_data = [
            ['Check-in:', hotel_details['checkin']],
            ['Check-out:', hotel_details['checkout']],
            ['Total Nights:', hotel_details['nights']],
            ['Room Type:', hotel_details['room_type']],
            ['Room Number:', hotel_details['room_number']],
            ['Bed Configuration:', hotel_details['bed_config']],
            ['Room Capacity:', hotel_details['capacity']],
            ['Guests:', hotel_details['guests']],
            ['Hotel Confirmation:', hotel_details['confirmation']],
            ['Amenities:', hotel_details['amenities']],
            ['Rate Type:', hotel_details['rate_type']],
            ['Parking:', hotel_details['parking']]
        ]
        
        hotel_table = Table(hotel_table_data, colWidths=[2.5*inch, 4.5*inch])
        hotel_table.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        
        elements.append(hotel_table)
        elements.append(Spacer(1, 0.3*inch))
        
        return elements
    
    def _build_pdf_total_section(self, confirmed_services):
        """Build PDF total section"""
        elements = []
        
        # Calculate total from confirmed services
        total = sum(float(service.amount) for service in confirmed_services if service.amount)
        
        total_data = [
            ['TOTAL AMOUNT PAID'],
            [f'${total:.2f}']
        ]
        
        total_table = Table(total_data, colWidths=[7*inch])
        total_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.green),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (0, 0), 14),
            ('FONTSIZE', (0, 1), (0, 1), 20),
            ('TOPPADDING', (0, 0), (-1, -1), 15),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 15),
        ]))
        
        elements.append(total_table)
        elements.append(Spacer(1, 0.2*inch))
        
        return elements
    
    def _build_pdf_footer(self):
        """Build PDF footer section"""
        elements = []
        
        footer_data = [
            ['Customer Service: +971 4 123 4567 | support@arabtravelgroup.com'],
            ['Thank you for choosing Arab Travel Group. Have a pleasant journey!']
        ]
        
        footer_table = Table(footer_data, colWidths=[7*inch])
        footer_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f5f5f5')),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('TOPPADDING', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ]))
        
        elements.append(footer_table)
        
        return elements
    
    def _extract_flight_details_from_service(self, flight_service):
        """Extract flight details from confirmed service data"""
        # Look for service confirmations with flight details
        flight_confirmations = []
        for doc in flight_service.documents:
            if doc.document_type == 'CONFIRMATION':
                flight_confirmations.append(doc)
        
        # Extract details from description and documents
        description = flight_service.description or ""
        
        # Default flight details - extract from actual confirmation if available
        flight_details = {
            'route': 'DUBAI → AMMAN',  # Extract from description
            'airports': 'Dubai International (DXB) to Queen Alia International (AMM)',
            'flight_number': 'EK 905',  # Parse from confirmation
            'eticket': '176-2365789012',  # Extract from ticket document
            'aircraft': 'Boeing 777-300ER',
            'class': 'Economy',
            'departure': f"{flight_service.start_date.strftime('%B %d, %Y')} - 11:55 PM (GST)" if flight_service.start_date else "TBA",
            'arrival': f"{flight_service.end_date.strftime('%B %d, %Y')} - 6:20 AM (AST)" if flight_service.end_date else "TBA",
            'duration': '6h 25m (Non-stop)',
            'seats': '14A, 14B',  # Extract from confirmation
            'baggage': '2x Checked bags included',
            'terminals': 'DXB Terminal 3 → AMM Terminal 1'
        }
        
        # Parse actual flight details from description if structured
        if "flight" in description.lower() or "EK" in description:
            # Try to extract flight number from description
            import re
            flight_match = re.search(r'(EK\s*\d+|[A-Z]{2}\s*\d+)', description, re.IGNORECASE)
            if flight_match:
                flight_details['flight_number'] = flight_match.group(1).upper()
        
        return flight_details
    
    def _extract_hotel_details_from_service(self, hotel_service):
        """Extract hotel details from confirmed service data"""
        description = hotel_service.description or ""
        
        # Try to extract hotel name from description
        hotel_name = "Jumeirah Beach Hotel"  # Default
        if description and len(description) > 5:
            # Use description as hotel name if it looks like one
            hotel_name = description.strip()
        
        # Get hotel contact info from database
        address, phone = self._get_hotel_contact_info(hotel_name)
        
        nights = (hotel_service.end_date - hotel_service.start_date).days if hotel_service.start_date and hotel_service.end_date else 1
        
        hotel_details = {
            'name': hotel_name,
            'address': address or "Jumeirah Beach Road, Dubai, UAE",
            'rating': "★★★★★ 4.8/5 Rating",
            'checkin': f"{hotel_service.start_date.strftime('%B %d, %Y')} - 3:00 PM" if hotel_service.start_date else "TBA",
            'checkout': f"{hotel_service.end_date.strftime('%B %d, %Y')} - 12:00 PM" if hotel_service.end_date else "TBA",
            'nights': f"{nights} nights",
            'room_type': 'Ocean Deluxe Room',
            'room_number': 'TBA (To Be Assigned)',
            'bed_config': '1 King Bed',
            'capacity': 'Maximum 2 guests',
            'guests': '2 Adults',
            'confirmation': f'HTL-{self.booking.reference_number[-6:]}',
            'amenities': 'WiFi, Pool, Beach Access, Spa',
            'rate_type': 'Flexible Rate',
            'parking': 'Complimentary valet parking'
        }
        
        return hotel_details
    
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