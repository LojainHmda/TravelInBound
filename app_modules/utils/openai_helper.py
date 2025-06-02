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
        You are a flight ticket analyzer. Please carefully examine this airline ticket and extract the following key information:

        1. Flight number (including airline code like 'RJ 502')
        2. Airline name (e.g., 'Royal Jordanian')
        3. Departure airport (city and code, e.g., 'Cairo (CAI)')
        4. Arrival airport (city and code, e.g., 'Amman (AMM)')
        5. Departure date (in format DD-MM-YYYY if possible)
        6. Departure time
        7. Arrival date (if different from departure)
        8. Arrival time
        9. Booking reference/PNR (usually 5-6 alphanumeric characters)
        10. Passenger name(s)
        11. Ticket number(s) (usually 13-14 digits)

        If the ticket is partially visible or any information is unclear, extract what you can confidently identify.

        Respond with a JSON object ONLY with these exact keys:
        {
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

        If you cannot find a particular piece of information, leave its value as an empty string or empty array.
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
            max_tokens=1000
        )

        content = response.choices[0].message.content
        if not content:
            logger.error("Empty response from OpenAI API")
            return get_empty_result_template("Empty response from OpenAI API")

        logger.info(f"Raw response: {content[:100]}...")

        try:
            result = json.loads(content)
            logger.info("Successfully parsed OpenAI response")

            expected_keys = [
                "flight_number", "airline", "departure_airport", "departure_code",
                "arrival_airport", "arrival_code", "departure_date", "departure_time",
                "arrival_date", "arrival_time", "booking_reference",
                "passenger_names", "ticket_numbers"
            ]

            for key in expected_keys:
                if key not in result:
                    result[key] = "" if key not in ["passenger_names", "ticket_numbers"] else []

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
