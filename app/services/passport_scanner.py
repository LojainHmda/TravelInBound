"""
Passport scanning service using OpenAI Vision API to extract customer information
"""
import base64
import os
import re
from datetime import datetime
from typing import Dict, Optional
import json

from openai import OpenAI

class PassportScanner:
    def __init__(self):
        self.client = OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))
    
    def extract_passport_data(self, image_path: str) -> Dict[str, Optional[str]]:
        """
        Extract passport information from an image using OpenAI Vision API
        
        Args:
            image_path: Path to the passport image file
            
        Returns:
            Dictionary containing extracted passport information
        """
        try:
            # Read and encode image
            with open(image_path, 'rb') as image_file:
                image_data = image_file.read()
                base64_image = base64.b64encode(image_data).decode('utf-8')
            
            # Prepare the prompt for passport data extraction
            prompt = """
            Analyze this passport image and extract the following information in JSON format:
            
            {
                "first_name": "Given name(s) from passport",
                "last_name": "Surname from passport", 
                "passport_number": "Passport number",
                "nationality": "Nationality",
                "date_of_birth": "Date of birth in YYYY-MM-DD format",
                "passport_expiry": "Passport expiry date in YYYY-MM-DD format",
                "place_of_birth": "Place of birth if available",
                "issuing_country": "Country that issued the passport"
            }
            
            Instructions:
            - Extract only the information that is clearly visible and readable
            - If a field is not clearly visible or readable, set it to null
            - For dates, convert to YYYY-MM-DD format
            - For names, extract exactly as written on the passport
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
                max_tokens=500
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
            print(f"Error extracting passport data: {e}")
            return self._empty_result()
    
    def _validate_and_clean_data(self, data: Dict) -> Dict[str, Optional[str]]:
        """
        Validate and clean the extracted passport data
        """
        cleaned_data = {}
        
        # Clean text fields
        text_fields = ['first_name', 'last_name', 'passport_number', 'nationality', 
                      'place_of_birth', 'issuing_country']
        
        for field in text_fields:
            value = data.get(field)
            if value and isinstance(value, str):
                # Clean up the text
                cleaned_value = value.strip().upper()
                cleaned_data[field] = cleaned_value if cleaned_value else None
            else:
                cleaned_data[field] = None
        
        # Validate and clean date fields
        date_fields = ['date_of_birth', 'passport_expiry']
        for field in date_fields:
            date_value = data.get(field)
            if date_value:
                cleaned_date = self._parse_date(date_value)
                cleaned_data[field] = cleaned_date
            else:
                cleaned_data[field] = None
        
        return cleaned_data
    
    def _parse_date(self, date_str: str) -> Optional[str]:
        """
        Parse and validate date strings, return in YYYY-MM-DD format
        """
        if not date_str:
            return None
            
        # Common date formats in passports
        date_patterns = [
            r'(\d{4})-(\d{2})-(\d{2})',  # YYYY-MM-DD
            r'(\d{2})/(\d{2})/(\d{4})',  # DD/MM/YYYY
            r'(\d{2})-(\d{2})-(\d{4})',  # DD-MM-YYYY
            r'(\d{2})\.(\d{2})\.(\d{4})', # DD.MM.YYYY
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, date_str)
            if match:
                groups = match.groups()
                try:
                    if len(groups[0]) == 4:  # YYYY-MM-DD format
                        year, month, day = groups
                    else:  # DD/MM/YYYY or similar formats
                        day, month, year = groups
                    
                    # Validate the date
                    datetime(int(year), int(month), int(day))
                    return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
                except ValueError:
                    continue
        
        return None
    
    def _empty_result(self) -> Dict[str, Optional[str]]:
        """
        Return empty result structure
        """
        return {
            'first_name': None,
            'last_name': None,
            'passport_number': None,
            'nationality': None,
            'date_of_birth': None,
            'passport_expiry': None,
            'place_of_birth': None,
            'issuing_country': None
        }