"""
Voucher/Trip Plan Word Document Generator
Generates professional Word documents for trip itineraries/vouchers with day-by-day details
"""

from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
from datetime import datetime
import os


class VoucherTripPlanGenerator:
    """Generate Word documents for trip vouchers/itineraries"""
    
    def __init__(self):
        self.doc = Document()
        self._setup_styles()
    
    def _setup_styles(self):
        """Setup document styles"""
        style = self.doc.styles['Normal']
        font = style.font
        font.name = 'Arial'
        font.size = Pt(10)
    
    def _add_header(self, company_name="Arabi Travel", company_address="Amman, Jordan"):
        """Add company header"""
        header = self.doc.add_paragraph()
        header.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = header.add_run(company_name)
        run.bold = True
        run.font.size = Pt(18)
        run.font.color.rgb = RGBColor(139, 115, 85)
        
        address = self.doc.add_paragraph()
        address.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = address.add_run(company_address)
        run.font.size = Pt(10)
        run.font.color.rgb = RGBColor(107, 114, 128)
        
        self.doc.add_paragraph()
    
    def _add_title(self, voucher_number, voucher_date):
        """Add voucher title"""
        title = self.doc.add_paragraph()
        title.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = title.add_run('TRIP VOUCHER')
        run.bold = True
        run.font.size = Pt(16)
        run.font.color.rgb = RGBColor(31, 41, 55)
        
        details = self.doc.add_paragraph()
        details.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = details.add_run(f'Voucher No: {voucher_number}')
        run.font.size = Pt(11)
        details.add_run('\n')
        run = details.add_run(f'Date: {voucher_date}')
        run.font.size = Pt(11)
        
        self.doc.add_paragraph()
    
    def _add_tour_summary(self, tour_data):
        """Add tour summary section"""
        heading = self.doc.add_paragraph()
        run = heading.add_run('Tour Information')
        run.bold = True
        run.font.size = Pt(14)
        run.font.color.rgb = RGBColor(31, 41, 55)
        
        # Create table for tour info
        table = self.doc.add_table(rows=0, cols=2)
        table.style = 'Light Grid Accent 1'
        
        # Add tour details
        details = [
            ('Tour Reference', tour_data.get('reference', 'N/A')),
            ('Guest Name', tour_data.get('guest_name', 'N/A')),
            ('Nationality', tour_data.get('nationality', 'N/A')),
            ('Number of Passengers', str(tour_data.get('pax', 'N/A'))),
            ('Tour Duration', f"{tour_data.get('from_date', '')} to {tour_data.get('to_date', '')}"),
            ('Number of Days', str(tour_data.get('no_of_days', 'N/A'))),
        ]
        
        if tour_data.get('agent_ref'):
            details.append(('Agent Reference', tour_data.get('agent_ref')))
        
        for label, value in details:
            row = table.add_row()
            row.cells[0].text = label
            row.cells[0].paragraphs[0].runs[0].bold = True
            row.cells[0].width = Inches(2.0)
            row.cells[1].text = value
            row.cells[1].width = Inches(4.5)
        
        self.doc.add_paragraph()
    
    def _add_hotel_details(self, hotels_data):
        """Add hotel accommodation details"""
        if not hotels_data:
            return
        
        heading = self.doc.add_paragraph()
        run = heading.add_run('Hotel Accommodations')
        run.bold = True
        run.font.size = Pt(14)
        run.font.color.rgb = RGBColor(31, 41, 55)
        
        for hotel in hotels_data:
            # Hotel name and dates
            hotel_para = self.doc.add_paragraph()
            run = hotel_para.add_run(f"🏨 {hotel.get('name', 'Hotel TBA')}")
            run.bold = True
            run.font.size = Pt(11)
            
            hotel_para.add_run(f"\nCheck-in: {hotel.get('check_in', 'TBA')} | Check-out: {hotel.get('check_out', 'TBA')}")
            hotel_para.add_run(f"\nLocation: {hotel.get('location', 'TBA')}")
            
            # Room configuration
            if hotel.get('rooms'):
                hotel_para.add_run(f"\nRooms: {hotel['rooms']}")
            
            if hotel.get('board_basis'):
                hotel_para.add_run(f"\nBoard Basis: {hotel['board_basis']}")
        
        self.doc.add_paragraph()
    
    def _add_day_by_day_itinerary(self, itinerary_days):
        """Add day-by-day itinerary"""
        heading = self.doc.add_paragraph()
        run = heading.add_run('Day-by-Day Itinerary')
        run.bold = True
        run.font.size = Pt(14)
        run.font.color.rgb = RGBColor(31, 41, 55)
        
        for day in itinerary_days:
            # Day header
            day_para = self.doc.add_paragraph()
            day_para.paragraph_format.space_before = Pt(12)
            day_para.paragraph_format.space_after = Pt(6)
            
            run = day_para.add_run(f"Day {day.get('day_number', '')} - {day.get('date', '')}")
            run.bold = True
            run.font.size = Pt(12)
            run.font.color.rgb = RGBColor(31, 41, 55)
            
            # Day description
            if day.get('description'):
                desc_para = self.doc.add_paragraph(day['description'])
                desc_para.paragraph_format.left_indent = Inches(0.25)
            
            # Services for the day
            services = day.get('services', [])
            if services:
                for service in services:
                    service_para = self.doc.add_paragraph(style='List Bullet')
                    service_para.paragraph_format.left_indent = Inches(0.5)
                    
                    service_type = service.get('type', '')
                    service_desc = service.get('description', '')
                    
                    icon = ''
                    if service_type == 'HOTEL':
                        icon = '🏨'
                    elif service_type == 'TRANSPORT':
                        icon = '🚗'
                    elif service_type == 'MEAL':
                        icon = '🍽️'
                    elif service_type == 'GUIDE':
                        icon = '👤'
                    
                    service_para.add_run(f"{icon} {service_type}: {service_desc}")
        
        self.doc.add_paragraph()
    
    def _add_footer_notes(self):
        """Add footer with important notes"""
        self.doc.add_paragraph()
        
        terms_heading = self.doc.add_paragraph()
        run = terms_heading.add_run('Important Notes:')
        run.bold = True
        run.font.size = Pt(11)
        
        notes = [
            'Please carry this voucher with you during your trip.',
            'Contact numbers will be provided upon confirmation.',
            'Check-in time is typically 2:00 PM, check-out is 12:00 PM.',
            'Please arrive at pickup locations 10 minutes early.',
            'Any changes to the itinerary should be coordinated with our office.'
        ]
        
        for note in notes:
            p = self.doc.add_paragraph(note, style='List Bullet')
            p.paragraph_format.left_indent = Inches(0.25)
            for run in p.runs:
                run.font.size = Pt(9)
                run.font.color.rgb = RGBColor(107, 114, 128)
        
        self.doc.add_paragraph()
        
        thank_you = self.doc.add_paragraph()
        thank_you.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = thank_you.add_run('Have a wonderful trip!')
        run.italic = True
        run.font.size = Pt(11)
        run.font.color.rgb = RGBColor(139, 115, 85)
    
    def generate_voucher(self, voucher_data, output_path=None):
        """
        Generate a trip voucher/itinerary Word document
        
        Args:
            voucher_data (dict): Dictionary containing:
                - voucher_number: Voucher/booking reference number
                - voucher_date: Date of voucher generation
                - tour: Tour info dict (reference, guest_name, nationality, pax, from_date, to_date, no_of_days, agent_ref)
                - hotels: List of hotel details
                - itinerary_days: List of day-by-day itinerary items
            output_path (str): Optional path to save document
        
        Returns:
            str: Path to generated document
        """
        # Add header
        self._add_header(
            company_name=voucher_data.get('company_name', 'Arabi Travel'),
            company_address=voucher_data.get('company_address', 'Amman, Jordan')
        )
        
        # Add title
        self._add_title(
            voucher_number=voucher_data.get('voucher_number', 'DRAFT'),
            voucher_date=voucher_data.get('voucher_date', datetime.now().strftime('%d %b %Y'))
        )
        
        # Add tour summary
        if voucher_data.get('tour'):
            self._add_tour_summary(voucher_data['tour'])
        
        # Add hotel details
        if voucher_data.get('hotels'):
            self._add_hotel_details(voucher_data['hotels'])
        
        # Add day-by-day itinerary
        if voucher_data.get('itinerary_days'):
            self._add_day_by_day_itinerary(voucher_data['itinerary_days'])
        
        # Add footer
        self._add_footer_notes()
        
        # Save document
        if not output_path:
            output_dir = os.path.join(os.getcwd(), 'generated_vouchers')
            os.makedirs(output_dir, exist_ok=True)
            output_path = os.path.join(
                output_dir,
                f"Voucher_{voucher_data.get('voucher_number', 'DRAFT')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.docx"
            )
        
        self.doc.save(output_path)
        return output_path
