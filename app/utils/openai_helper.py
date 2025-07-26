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
        "passenger_types": [],
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
        10. **PASSENGERS FOR THIS SEGMENT**: Names of passengers traveling on this specific flight
        11. **PASSENGER TYPES FOR THIS SEGMENT**: Age classification for each passenger (Adult/Child/Infant)
        12. **TICKET NUMBERS FOR THIS SEGMENT**: Ticket numbers for passengers on this specific flight

        SEGMENT-SPECIFIC PASSENGER ASSIGNMENT:
        **CRITICAL**: Passengers and ticket numbers must be assigned to EACH FLIGHT SEGMENT separately.
        Different passengers may travel on different flight segments. For example:
        - Segment 1 (AMM→DXB): John Smith, Jane Smith (traveling together)  
        - Segment 2 (DXB→IST): John Smith only (continuing alone)
        
        Look for passenger tables or lists that show which passengers are on which specific flights.
        If a passenger table shows all passengers for all flights, assign them to each segment.
        If document shows different passengers per segment, respect those assignments.

        PASSENGER & BOOKING INFO - CRITICAL PNR EXTRACTION:
        **HIGHEST PRIORITY**: Look VERY carefully for PNR/Booking Reference/Confirmation codes:
        - **Search patterns**: PNR, PN, Booking Reference, Confirmation Code, Record Locator, Reservation Code
        - **Format variations**: Usually 5-7 alphanumeric characters (e.g., "ABC123", "XVS04V", "PQRST1", "7G4HJ2")
        - **Common locations**: Header sections, passenger details area, booking summary, confirmation details
        - **Labels to look for**: "PNR:", "PN:", "Booking Ref:", "Confirmation:", "Record Locator:", "Reservation:"
        - **Arabic/multilingual**: May appear in Arabic or other languages alongside English
        - **CRITICAL**: Include PNR in BOTH the global booking_reference AND in each flight segment
        - **Segment-specific PNRs**: Each flight segment may have its own PNR (especially for connecting flights)
        - **PASSENGER TYPES**: Identify passenger age categories for each passenger:
          * **Adult**: Passengers 12+ years old, or if no age specified assume Adult
          * **Child**: Passengers 2-11 years old, look for "CHD", "Child", age indicators
          * **Infant**: Passengers under 2 years old, look for "INF", "Infant", "Baby"
          * **Default**: If no age information found, classify as "Adult"
          * **Sequential matching**: passenger_types array must match passenger_names order
        - Passenger names per flight segment (not just globally)
        - **CRITICAL: E-ticket numbers** - Look VERY carefully for ticket numbers throughout the document:
          * 13-digit numbers (e.g., 1572345678901, 2351234567890)
          * Numbers starting with airline code + digits (e.g., QR1234567890123, EK9876543210987)
          * May be labeled as "Ticket Number", "E-Ticket", "TKT", "Electronic Ticket", "Document Number"
          * **SEGMENT-LEVEL SEQUENTIAL MAPPING**: For EACH flight segment, ticket numbers MUST be mapped to passengers:
            - Assign ticket numbers to passengers per flight segment, not globally
            - Within each segment: First ticket → First passenger, Second ticket → Second passenger
            - If a passenger travels on multiple segments, they get different ticket numbers for each segment
            - When ticket numbers appear consecutively (e.g., 1762384500337, 1762384500338), assign them to passengers in that segment
          * Search in passenger tables, flight-specific sections, segment details, and barcode regions
          * Include ALL ticket numbers found and assign them to the correct flight segment
          * Example: 
            - Segment 1 passengers [John Smith, Jane Smith] → tickets [123456, 123457]
            - Segment 2 passengers [John Smith] → tickets [789012]
          * If numbers are sequential (e.g., 1572345678901, 1572345678902), include all of them
        - Travel class (Economy, Business, First)
        - Seat assignments if shown

        OUTPUT FORMAT - JSON ONLY:
        **CRITICAL**: For each segment, passenger_names, passenger_types, and ticket_numbers arrays MUST be in matching sequential order
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
                    "aircraft_type": "Boeing 777",
                    "pnr": "XVS04V",
                    "passenger_names": ["John Smith", "Jane Smith", "Baby Smith"],
                    "passenger_types": ["Adult", "Adult", "Infant"],
                    "ticket_numbers": ["1572345678901", "1572345678902", "1572345678903"]
                }
            ],
            "booking_reference": "ABC123",
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
        - **TICKET NUMBERS ARE THE TOP PRIORITY** - Look extremely carefully throughout the entire document:
          * Search EVERYWHERE: passenger details, ticket summary, confirmation details, barcode areas, itinerary sections
          * Look for ANY 10+ digit numbers that could be tickets (even if not explicitly labeled)
          * Check for patterns like consecutive numbers (1572345678901, 1572345678902, 1572345678903)
          * Include ALL ticket numbers found - do not skip any
          * **CRITICAL**: Order ticket numbers to match passenger order (first ticket for first passenger, etc.)
          * If you find ticket numbers but passenger names are unclear, still include all ticket numbers
        - If information is unclear, extract what you can confidently read
        - Ticket number extraction is more important than other details - prioritize finding these numbers
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
                        "passenger_types": result.get("passenger_types", []),
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
                        "passenger_types": [],
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
        "total_cost": "",
        "nights": "",
        "address": "",
        "phone": "",
        "room_count": 1,
        "rooms": [
            {
                "room_count": 1,
                "room_type": "",
                "board_basis": "Room Only",
                "adults": 2,
                "children": 0,
                "lead_passenger": ""
            }
        ]
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
        5. Individual room details (if multiple rooms are shown)
        6. Total cost/price (with currency if visible)
        7. Number of nights
        8. Hotel address (if visible)
        9. Hotel phone number (if visible)

        IMPORTANT: Pay attention to room quantity indicators like "03 Dbl" which means 3 double rooms.
        
        For room extraction:
        1. First identify the TOTAL NUMBER of rooms from quantity indicators (like "03 Dbl" = 3 rooms)
        2. Then extract room details for each room type, creating separate entries if multiple rooms of same type
        
        For each room, include:
        - Room count: Number of rooms of this specific type (e.g., if "03 Dbl" then room_count=3)
        - Room type: Extract the EXACT room type name as written (e.g., "STD ROOM", "Urban Deluxe Twin Bed", "Dbl", "Standard Double Room", etc.)
        - Board basis: Look for meal plan information and standardize it:
          * "Room Only" (if no meals mentioned)
          * "Bed & Breakfast" (if BB, breakfast, or similar mentioned)
          * "Half Board" (if HB, half board, or dinner+breakfast mentioned)
          * "Full Board" (if FB, full board, or all meals mentioned)
          * "All Inclusive" (if AI, ALL INCLUSIVE, ALL INCLSIVE, all inclusive, or similar mentioned)
          * "Ultra All Inclusive" (if ultra, premium all inclusive mentioned)
        - Number of adults per room
        - Number of children per room
        - Lead passenger/guest name for that room

        Return the results in JSON format with these exact keys:
        - hotel_name
        - checkin_date
        - checkout_date
        - confirmation_number
        - total_cost
        - nights
        - address
        - phone
        - room_count (total number of rooms as integer)
        - rooms (array of room objects with keys: room_count, room_type, board_basis, adults, children, lead_passenger)

        Example for multiple rooms:
        {
          "hotel_name": "PARKROYAL COLLECTION Kuala Lumpur",
          "checkin_date": "2025-06-06",
          "checkout_date": "2025-11-06",
          "confirmation_number": "18",
          "total_cost": "",
          "nights": 5,
          "address": "Jln Sultan Ismail, Bukit Bintang, 50250 Kuala Lumpur",
          "phone": "+60 3-2782 8388",
          "rooms": [
            {
              "room_type": "urban deluxe twin bed",
              "board_basis": "Bed & Breakfast (BB)",
              "adults": 2,
              "children": 0,
              "lead_passenger": "Mr. YOUSEF ABUSALEEM"
            },
            {
              "room_type": "urban deluxe twin bed",
              "board_basis": "Bed & Breakfast (BB)",
              "adults": 2,
              "children": 0,
              "lead_passenger": "Mr. Yazan Abdalnabi"
            },
            {
              "room_type": "urban deluxe twin bed",
              "board_basis": "Bed & Breakfast (BB)",
              "adults": 2,
              "children": 0,
              "lead_passenger": "Mr. Malik Abdalnabi"
            }
          ]
        }

        Focus on accuracy over completeness. If you cannot clearly read a field, leave it empty rather than guessing.
        """

        user_prompt = """Please analyze this hotel booking confirmation/voucher image and extract the hotel booking details in the requested JSON format.

IMPORTANT: If this is clearly a flight ticket or e-ticket instead of a hotel confirmation, respond with a JSON error like:
{"error": "This appears to be a flight ticket, not a hotel confirmation. Please upload a hotel booking confirmation."}

Otherwise, extract all the hotel details as requested, paying special attention to:
- ROOM COUNT: Look for quantity indicators like "03 Dbl" (meaning 3 double rooms) and create ONE room entry with room_count=3
- If you see "03 Dbl" create ONE room entry with room_count=3 and room_type "Double Room", NOT 3 separate entries
- Multiple rooms if shown in a table format
- Each room's lead passenger name (may be same person for multiple rooms)
- Room types exactly as written (like "STD ROOM", "urban deluxe twin bed", "Dbl", "Standard Room")
- Board basis - Look carefully for meal plan text that might be abbreviated or contain typos:
  * "ALL INCLUSIVE", "ALL INCLSIVE", "AI", "All Inc", "All-Inclusive" → use "All Inclusive"
  * "BB", "Breakfast", "B&B" → use "Bed & Breakfast"
  * "HB", "Half Board" → use "Half Board" 
  * "FB", "Full Board" → use "Full Board"
  * If no meal plan visible → use "Room Only"
- Guest counts (Adult, Child, Infant numbers) - distribute across rooms if total counts given
- Total guest count may need to be divided across multiple rooms

EXAMPLE: If you see "03 Dbl" with "6 adults, 1 child" total, create ONE room entry with room_count=3, room_type="Double Room", adults=2, children=0 (average per room).
"""

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
