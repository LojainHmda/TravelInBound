import os
import json
import base64
import logging
from openai import OpenAI
from pdf2image import convert_from_bytes
from PIL import Image
import io

# the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
MODEL_NAME = "gpt-4o"

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_empty_result_template(error_message=None):
    """Helper function to return a standardized empty result template"""
    result = {
        "flight_number": "",
        "airline": "",
        "departure_airport": "",
        "departure_code": "",
        "arrival_airport": "",
        "arrival_code": "",
        "departure_date": "",
        "departure_time": "",
        "arrival_date": "",
        "arrival_time": "",
        "booking_reference": "",
        "passenger_names": [],
        "ticket_numbers": []
    }

    if error_message:
        result["error"] = error_message

    return result

def convert_pdf_to_image(pdf_data):
    """
    Convert PDF to image for analysis.
    
    Args:
        pdf_data: Raw PDF file data (bytes)
        
    Returns:
        Base64 encoded image data of the first page
    """
    try:
        # Convert PDF to images (only first page)
        images = convert_from_bytes(pdf_data, first_page=1, last_page=1, dpi=200)
        
        if not images:
            logger.error("No pages found in PDF")
            return None
            
        # Convert PIL Image to base64
        img_buffer = io.BytesIO()
        images[0].save(img_buffer, format='PNG')
        img_data = base64.b64encode(img_buffer.getvalue()).decode('utf-8')
        
        logger.info(f"Successfully converted PDF to image, size: {len(img_data)}")
        return img_data
        
    except Exception as e:
        logger.error(f"Error converting PDF to image: {str(e)}")
        return None

def analyze_flight_ticket(image_data):
    """
    Analyze a flight ticket image using OpenAI's vision capabilities.

    Args:
        image_data: Base64 encoded image data

    Returns:
        Dictionary containing extracted flight information
    """
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        logger.error("OpenAI API key not found in environment variables")
        return get_empty_result_template("OpenAI API key not configured")

    client = OpenAI(api_key=api_key)

    try:
        system_prompt = """
        You are an expert airline ticket analyzer specializing in complex multi-leg and connecting flight itineraries. 
        Examine this airline ticket/e-ticket carefully and extract ALL flight information.

        CRITICAL: Look for ALL flight segments including:
        - Outbound flights (departure city to destination)
        - Return flights (destination back to origin)  
        - Connecting flights (intermediate stops)
        - Multi-city segments (different destinations)
        - Code-share flights (same journey operated by different airlines)

        AIRLINE TICKET PATTERNS TO RECOGNIZE:
        - Qatar Airways tickets often show connecting flights through Doha (DOH)
        - Emirates tickets may connect through Dubai (DXB)
        - Turkish Airlines connects through Istanbul (IST)
        - Look for flight tables, itinerary sections, or segment listings
        - Check for "via" or "connecting through" phrases
        - Identify layover times and connection airports

        For EACH flight segment found, extract:
        1. Flight number (e.g., 'QR 402', 'EK 903', 'TK 154')
        2. Airline name (Qatar Airways, Emirates, Turkish Airlines, etc.)
        3. Departure airport with city name and code (e.g., 'Amman Queen Alia (AMM)')
        4. Arrival airport with city name and code (e.g., 'Doha Hamad (DOH)')
        5. Flight date (YYYY-MM-DD format preferred)
        6. Departure time (HH:MM in 24-hour format)
        7. Arrival time (HH:MM in 24-hour format)
        8. Connection type ("direct", "connecting", "layover")
        9. Aircraft type if visible (e.g., "Boeing 777", "Airbus A350")

        PASSENGER & BOOKING INFO:
        - PNR/Booking reference (typically 5-6 alphanumeric characters)
        - All passenger names listed
        - E-ticket numbers (13-digit numbers starting with airline code)
        - Travel class (Economy, Business, First)
        - Seat assignments if shown

        OUTPUT FORMAT - JSON ONLY:
        {
            "flight_type": "one_way|round_trip|multi_city",
            "segments": [
                {
                    "flight_number": "QR 402",
                    "airline": "Qatar Airways", 
                    "departure_airport": "Amman Queen Alia Intl",
                    "departure_code": "AMM",
                    "arrival_airport": "Doha Hamad Intl",
                    "arrival_code": "DOH",
                    "flight_date": "2025-07-15",
                    "departure_time": "14:30",
                    "arrival_time": "16:45",
                    "duration": "2h 15m",
                    "connection_type": "connecting",
                    "aircraft_type": "Boeing 777"
                }
            ],
            "booking_reference": "ABC123",
            "passenger_names": ["John Smith", "Jane Smith"],
            "ticket_numbers": ["1572345678901", "1572345678902"],
            "travel_class": "Economy",
            "terminal": "Terminal 3",
            "baggage_allowance": "23kg",
            "seat_assignment": "12A, 12B"
        }

        IMPORTANT: 
        - Add ALL segments as separate objects in the segments array
        - For connecting flights, identify the connection airport correctly
        - If round-trip, ensure both outbound AND return segments are captured
        - For multi-city, capture each city-to-city segment
        - If information is unclear, extract what you can confidently read
        """

        logger.info(f"Sending request to OpenAI API with image of size {len(image_data)}")

        # Determine format based on base64 prefix
        image_format = "jpeg"
        if image_data.startswith("/9j/"):
            image_format = "jpeg"
        elif image_data.startswith("iVBOR"):
            image_format = "png"

        data_uri = f"data:image/{image_format};base64,{image_data}"

        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": [
                    {"type": "text", "text": "Please analyze this flight ticket and extract all available information."},
                    {"type": "image_url", "image_url": {"url": data_uri}}
                ]}
            ],
            response_format={"type": "json_object"},
            max_tokens=3000
        )

        content = response.choices[0].message.content
        if not content:
            logger.error("Empty response from OpenAI API")
            return get_empty_result_template("Empty response from OpenAI API")

        # Check if the response was truncated
        finish_reason = response.choices[0].finish_reason
        if finish_reason == 'length':
            logger.warning("OpenAI response was truncated due to token limit")
            
        logger.info(f"Raw response length: {len(content)} characters")
        logger.info(f"Finish reason: {finish_reason}")
        logger.info(f"Raw response: {content[:200]}...")

        try:
            # Handle potential markdown JSON formatting and truncation
            if content.startswith('```json'):
                content = content[7:-3].strip()
            elif content.startswith('```'):
                content = content[3:-3].strip()
            
            # If response was truncated, try to fix incomplete JSON
            if finish_reason == 'length' and not content.endswith('}'):
                logger.warning("Attempting to fix truncated JSON response")
                # Count open/close braces to try to balance them
                open_braces = content.count('{')
                close_braces = content.count('}')
                missing_braces = open_braces - close_braces
                content = content.rstrip(',') + '}' * missing_braces
            
            result = json.loads(content)
            logger.info("Successfully parsed OpenAI response")

            # Ensure the result has the new multi-segment format
            if 'segments' not in result:
                # Convert old format to new format
                if any(key in result for key in ["flight_number", "airline", "departure_airport"]):
                    segments = [{
                        "flight_number": result.get("flight_number", ""),
                        "airline": result.get("airline", ""),
                        "departure_airport": result.get("departure_airport", ""),
                        "departure_code": result.get("departure_code", ""),
                        "arrival_airport": result.get("arrival_airport", ""),
                        "arrival_code": result.get("arrival_code", ""),
                        "flight_date": result.get("departure_date", ""),
                        "departure_time": result.get("departure_time", ""),
                        "arrival_time": result.get("arrival_time", ""),
                        "duration": "",
                        "connection_type": "",
                        "aircraft_type": ""
                    }]
                    result = {
                        "flight_type": "one_way",
                        "segments": segments,
                        "booking_reference": result.get("booking_reference", ""),
                        "passenger_names": result.get("passenger_names", []),
                        "ticket_numbers": result.get("ticket_numbers", []),
                        "travel_class": "",
                        "terminal": "",
                        "baggage_allowance": "",
                        "seat_assignment": ""
                    }
                else:
                    # Empty result
                    result = {
                        "flight_type": "one_way",
                        "segments": [],
                        "booking_reference": "",
                        "passenger_names": [],
                        "ticket_numbers": [],
                        "travel_class": "",
                        "terminal": "",
                        "baggage_allowance": "",
                        "seat_assignment": ""
                    }

            # Ensure segments is a list
            if not isinstance(result.get('segments'), list):
                result['segments'] = []

            # Validate each segment has required keys
            for segment in result['segments']:
                segment_keys = [
                    "flight_number", "airline", "departure_airport", "departure_code",
                    "arrival_airport", "arrival_code", "flight_date", "departure_time",
                    "arrival_time", "duration", "connection_type", "aircraft_type"
                ]
                for key in segment_keys:
                    if key not in segment:
                        segment[key] = ""

            return result

        except json.JSONDecodeError as json_err:
            logger.error(f"Failed to parse JSON: {json_err}")
            logger.error(f"Raw content: {content}")
            return get_empty_result_template(f"Failed to parse response: {json_err}")

    except Exception as e:
        logger.error(f"Error in OpenAI analysis: {str(e)}")
        return get_empty_result_template(f"Error analyzing ticket: {str(e)}")

def analyze_document(file_data, filename):
    """
    Analyze a document (PDF or image) for travel information.
    
    Args:
        file_data: Raw file data (bytes)
        filename: Original filename to determine file type
        
    Returns:
        Dictionary containing extracted travel information
    """
    try:
        # Check if it's a PDF
        if filename.lower().endswith('.pdf'):
            logger.info(f"Processing PDF file: {filename}")
            image_data = convert_pdf_to_image(file_data)
            if not image_data:
                return get_empty_result_template("Failed to convert PDF to image")
        else:
            # It's an image file
            logger.info(f"Processing image file: {filename}")
            image_data = base64.b64encode(file_data).decode('utf-8')
            
        # Analyze with OpenAI
        return analyze_flight_ticket(image_data)
        
    except Exception as e:
        logger.error(f"Error analyzing document {filename}: {str(e)}")
        return get_empty_result_template(f"Error analyzing document: {str(e)}")

def get_empty_hotel_result_template(error_message=None):
    """Helper function to return a standardized empty hotel result template"""
    result = {
        "hotel_name": "",
        "checkin_date": "",
        "checkout_date": "",
        "confirmation_number": "",
        "room_type": "",
        "guests": "",
        "meal_plan": "",
        "total_cost": "",
        "nights": "",
        "guest_names": [],
        "address": "",
        "phone": ""
    }

    if error_message:
        result["error"] = error_message

    return result

def analyze_hotel_voucher(image_data):
    """
    Analyze a hotel voucher/booking confirmation image using OpenAI's vision capabilities.

    Args:
        image_data: Base64 encoded image data

    Returns:
        Dictionary containing extracted hotel information
    """
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        logger.error("OpenAI API key not found in environment variables")
        return get_empty_hotel_result_template("OpenAI API key not configured")

    client = OpenAI(api_key=api_key)

    try:
        system_prompt = """
        You are a hotel booking confirmation analyzer. Please carefully examine this hotel voucher/booking confirmation and extract the following key information:

        1. Hotel name (full hotel name)
        2. Check-in date (in format YYYY-MM-DD if possible)
        3. Check-out date (in format YYYY-MM-DD if possible)
        4. Confirmation number/booking reference
        5. Room type (e.g., Standard Double, Suite, etc.)
        6. Number of guests/occupancy
        7. Meal plan (Room Only, Breakfast, Half Board, Full Board, All Inclusive)
        8. Total cost/price (with currency if visible)
        9. Number of nights
        10. Guest names (if visible)
        11. Hotel address (if visible)
        12. Hotel phone number (if visible)

        If any information is unclear or not visible, extract what you can confidently identify.
        Return the results in JSON format with these exact keys:
        - hotel_name
        - checkin_date
        - checkout_date
        - confirmation_number
        - room_type
        - guests
        - meal_plan
        - total_cost
        - nights
        - guest_names (array)
        - address
        - phone

        Focus on accuracy over completeness. If you cannot clearly read a field, leave it empty rather than guessing.
        """

        user_prompt = "Please analyze this hotel booking confirmation/voucher image and extract the hotel booking details in the requested JSON format."

        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": user_prompt},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{image_data}"}
                        }
                    ]
                }
            ],
            max_tokens=1000,
            temperature=0.1
        )

        content = response.choices[0].message.content.strip()
        logger.info(f"OpenAI response for hotel voucher: {content}")

        # Try to parse JSON from the response
        try:
            # Look for JSON content
            if content.startswith('```json'):
                content = content[7:-3]  # Remove ```json and ```
            elif content.startswith('```'):
                content = content[3:-3]  # Remove ``` and ```
            
            result = json.loads(content)
            
            # Ensure all expected keys exist with default values
            template = get_empty_hotel_result_template()
            for key in template:
                if key not in result:
                    result[key] = template[key]
            
            return result
            
        except json.JSONDecodeError as json_err:
            logger.error(f"Failed to parse JSON: {json_err}")
            logger.error(f"Raw content: {content}")
            return get_empty_hotel_result_template(f"Failed to parse response: {json_err}")

    except Exception as e:
        logger.error(f"Error in OpenAI hotel voucher analysis: {str(e)}")
        return get_empty_hotel_result_template(f"Error analyzing hotel voucher: {str(e)}")
