"""
Ticket scanning service using OpenAI Vision API to extract flight ticket information
"""
import base64
import os
import re
from datetime import datetime
from typing import Dict, Optional, List
import json

from openai import OpenAI

class TicketScanner:
    def __init__(self):
        self.client = OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))
    
    def extract_ticket_data(self, image_path: str) -> Dict[str, Optional[str]]:
        """
        Extract flight ticket information from an image using OpenAI Vision API
        
        Args:
            image_path: Path to the ticket image file
            
        Returns:
            Dictionary containing extracted ticket information
        """
        try:
            # Read and encode image
            with open(image_path, 'rb') as image_file:
                image_data = image_file.read()
                base64_image = base64.b64encode(image_data).decode('utf-8')
            
            # Prepare the prompt for ticket data extraction
            prompt = """
            Analyze this flight ticket/e-ticket image and extract the following information in JSON format:
            
            {
                "airline": "Airline name",
                "flight_number": "Flight number (e.g., EK905)",
                "departure_airport": "Departure airport code and city",
                "arrival_airport": "Arrival airport code and city",
                "departure_date": "Departure date in YYYY-MM-DD format",
                "departure_time": "Departure time in HH:MM format",
                "arrival_date": "Arrival date in YYYY-MM-DD format", 
                "arrival_time": "Arrival time in HH:MM format",
                "passenger_name": "Passenger name exactly as shown",
                "ticket_number": "Ticket/E-ticket number",
                "confirmation_code": "Booking reference/confirmation code",
                "seat_number": "Seat number if available",
                "travel_class": "Travel class (Economy, Business, First)",
                "baggage_allowance": "Baggage allowance if mentioned",
                "gate": "Gate number if available",
                "terminal": "Terminal if available"
            }
            
            Instructions:
            - Extract only information that is clearly visible and readable
            - If a field is not visible or readable, set it to null
            - For dates, convert to YYYY-MM-DD format
            - For times, use 24-hour format HH:MM
            - Extract passenger name exactly as written on ticket
            - Return only the JSON object, no additional text
            """
            
            # Call OpenAI Vision API
            response = self.client.chat.completions.create(
                model="gpt-4o",  # Latest OpenAI model with vision capabilities
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": prompt
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                response_format={"type": "json_object"},
                max_tokens=800
            )
            
            # Parse the response
            content = response.choices[0].message.content
            if content:
                result = json.loads(content)
            else:
                result = {}
            
            # Validate and clean the extracted data
            return self._validate_and_clean_data(result)
            
        except Exception as e:
            print(f"Error extracting ticket data: {e}")
            return self._empty_result()
    
    def _validate_and_clean_data(self, data: Dict) -> Dict[str, Optional[str]]:
        """
        Validate and clean the extracted ticket data
        """
        cleaned_data = {}
        
        # Clean text fields
        text_fields = [
            'airline', 'flight_number', 'departure_airport', 'arrival_airport',
            'passenger_name', 'ticket_number', 'confirmation_code', 'seat_number',
            'travel_class', 'baggage_allowance', 'gate', 'terminal'
        ]
        
        for field in text_fields:
            value = data.get(field)
            if value and isinstance(value, str):
                cleaned_value = value.strip()
                # Keep passenger name in original case, uppercase others
                if field == 'passenger_name':
                    cleaned_data[field] = cleaned_value if cleaned_value else None
                else:
                    cleaned_data[field] = cleaned_value.upper() if cleaned_value else None
            else:
                cleaned_data[field] = None
        
        # Validate and clean date fields
        date_fields = ['departure_date', 'arrival_date']
        for field in date_fields:
            date_value = data.get(field)
            if date_value:
                cleaned_date = self._parse_date(date_value)
                cleaned_data[field] = cleaned_date
            else:
                cleaned_data[field] = None
        
        # Validate and clean time fields
        time_fields = ['departure_time', 'arrival_time']
        for field in time_fields:
            time_value = data.get(field)
            if time_value:
                cleaned_time = self._parse_time(time_value)
                cleaned_data[field] = cleaned_time
            else:
                cleaned_data[field] = None
        
        return cleaned_data
    
    def _parse_date(self, date_str: str) -> Optional[str]:
        """
        Parse and validate date strings, return in YYYY-MM-DD format
        """
        if not date_str:
            return None
            
        # Common date formats in tickets
        date_patterns = [
            r'(\d{4})-(\d{2})-(\d{2})',  # YYYY-MM-DD
            r'(\d{2})/(\d{2})/(\d{4})',  # DD/MM/YYYY
            r'(\d{2})-(\d{2})-(\d{4})',  # DD-MM-YYYY
            r'(\d{2})\.(\d{2})\.(\d{4})', # DD.MM.YYYY
            r'(\d{1,2})\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{4})', # DD MMM YYYY
        ]
        
        months = {
            'JAN': '01', 'FEB': '02', 'MAR': '03', 'APR': '04',
            'MAY': '05', 'JUN': '06', 'JUL': '07', 'AUG': '08',
            'SEP': '09', 'OCT': '10', 'NOV': '11', 'DEC': '12'
        }
        
        for pattern in date_patterns:
            match = re.search(pattern, date_str.upper())
            if match:
                groups = match.groups()
                try:
                    if len(groups) == 3 and groups[1] in months:  # DD MMM YYYY format
                        day, month_str, year = groups
                        month = months[month_str]
                    elif len(groups[0]) == 4:  # YYYY-MM-DD format
                        year, month, day = groups
                    else:  # DD/MM/YYYY or similar formats
                        day, month, year = groups
                    
                    # Validate the date
                    datetime(int(year), int(month), int(day))
                    return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
                except ValueError:
                    continue
        
        return None
    
    def _parse_time(self, time_str: str) -> Optional[str]:
        """
        Parse and validate time strings, return in HH:MM format
        """
        if not time_str:
            return None
        
        # Remove common time indicators
        time_str = time_str.replace('hrs', '').replace('h', '').strip()
        
        # Common time formats
        time_patterns = [
            r'(\d{1,2}):(\d{2})',  # HH:MM or H:MM
            r'(\d{1,2})\.(\d{2})',  # HH.MM or H.MM
            r'(\d{1,2})(\d{2})',   # HHMM
        ]
        
        for pattern in time_patterns:
            match = re.search(pattern, time_str)
            if match:
                groups = match.groups()
                try:
                    hour = int(groups[0])
                    minute = int(groups[1]) if len(groups) > 1 else 0
                    
                    # Validate time
                    if 0 <= hour <= 23 and 0 <= minute <= 59:
                        return f"{hour:02d}:{minute:02d}"
                except ValueError:
                    continue
        
        return None
    
    def _empty_result(self) -> Dict[str, Optional[str]]:
        """
        Return empty result structure
        """
        return {
            'airline': None,
            'flight_number': None,
            'departure_airport': None,
            'arrival_airport': None,
            'departure_date': None,
            'departure_time': None,
            'arrival_date': None,
            'arrival_time': None,
            'passenger_name': None,
            'ticket_number': None,
            'confirmation_code': None,
            'seat_number': None,
            'travel_class': None,
            'baggage_allowance': None,
            'gate': None,
            'terminal': None
        }