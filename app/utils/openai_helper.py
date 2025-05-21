import os
import json
import base64
from openai import OpenAI

# the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
# do not change this unless explicitly requested by the user
MODEL_NAME = "gpt-4o"

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

def analyze_flight_ticket(image_data):
    """
    Analyze a flight ticket image using OpenAI's vision capabilities.
    
    Args:
        image_data: Base64 encoded image data
        
    Returns:
        Dictionary containing extracted flight information
    """
    try:
        # Create a system prompt to guide the analysis
        system_prompt = """
        You are a flight ticket analyzer. Extract the following information from the flight ticket image:
        - Flight number (including airline code)
        - Airline name
        - Departure airport (city and code)
        - Arrival airport (city and code)
        - Departure date and time
        - Arrival date and time
        - Booking reference/PNR
        - Passenger name(s) if available
        - Ticket number(s) if available
        
        Respond with a JSON object ONLY with these keys (even if some fields are not found in the image):
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
        """
        
        # Call the OpenAI API with the image
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": [
                    {"type": "text", "text": "Extract flight details from this ticket."},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_data}"}}
                ]}
            ],
            response_format={"type": "json_object"},
            max_tokens=1000
        )
        
        # Parse the response
        result = json.loads(response.choices[0].message.content)
        return result
    
    except Exception as e:
        print(f"Error in OpenAI analysis: {str(e)}")
        return {
            "error": str(e),
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