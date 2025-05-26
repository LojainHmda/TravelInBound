"""
AI Chat Service for Travel Booking Platform
Uses OpenAI to provide intelligent booking assistance
"""

import os
import json
from openai import OpenAI
from sqlalchemy import or_, and_, func
from datetime import datetime, date, timedelta
from app import db
from app.models.booking import Booking
from app.models.customer import Customer
from app.models import ServiceItem, Payment

class TravelAIAssistant:
    def __init__(self):
        # the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
        # do not change this unless explicitly requested by the user
        self.client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        self.model = "gpt-4o"
        
    def process_query(self, user_query, user_context=None):
        """Process user query and return intelligent response with booking data"""
        
        # First, analyze the query to understand what the user wants
        intent = self._analyze_query_intent(user_query)
        
        # Get relevant booking data based on the intent
        booking_data = self._fetch_relevant_data(intent, user_query)
        
        # Generate AI response with the data
        response = self._generate_ai_response(user_query, intent, booking_data, user_context)
        
        return response
    
    def _analyze_query_intent(self, query):
        """Analyze user query to understand intent and extract entities"""
        
        system_prompt = """
        You are an AI assistant for a travel booking platform. Analyze the user's query and extract:
        1. Intent (search_booking, booking_status, customer_info, financial_info, general_help)
        2. Entities (booking reference, customer name, dates, destinations, etc.)
        
        Respond with JSON format:
        {
            "intent": "search_booking",
            "entities": {
                "booking_reference": "IR-12345",
                "customer_name": "John Smith",
                "destination": "Paris",
                "date_range": "2024-01-01 to 2024-01-31"
            },
            "confidence": 0.9
        }
        """
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": query}
                ],
                response_format={"type": "json_object"}
            )
            
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            return {
                "intent": "general_help",
                "entities": {},
                "confidence": 0.5,
                "error": str(e)
            }
    
    def _fetch_relevant_data(self, intent, query):
        """Fetch relevant booking data based on the analyzed intent"""
        
        data = {
            "bookings": [],
            "customers": [],
            "stats": {},
            "error": None
        }
        
        try:
            entities = intent.get("entities", {})
            
            # Build query based on extracted entities
            booking_query = Booking.query
            
            # Filter by booking reference
            if entities.get("booking_reference"):
                ref = entities["booking_reference"]
                booking_query = booking_query.filter(
                    Booking.reference_number.ilike(f"%{ref}%")
                )
            
            # Filter by customer name
            if entities.get("customer_name"):
                name_parts = entities["customer_name"].split()
                if len(name_parts) >= 1:
                    first_name = name_parts[0]
                    last_name = " ".join(name_parts[1:]) if len(name_parts) > 1 else ""
                    
                    # Join with User table to search by name
                    booking_query = booking_query.join(Booking.requester).filter(
                        or_(
                            func.lower(Booking.requester.has(first_name__ilike=f"%{first_name}%")),
                            func.lower(Booking.requester.has(last_name__ilike=f"%{last_name}%"))
                        )
                    )
            
            # Filter by destination (search in service items)
            if entities.get("destination"):
                destination = entities["destination"]
                booking_query = booking_query.join(ServiceItem).filter(
                    ServiceItem.description.ilike(f"%{destination}%")
                )
            
            # Get bookings
            bookings = booking_query.limit(10).all()
            
            # Format booking data
            for booking in bookings:
                booking_info = {
                    "id": booking.id,
                    "reference_number": booking.reference_number,
                    "status": booking.status,
                    "total_amount": float(booking.total_amount or 0),
                    "created_at": booking.created_at.strftime("%Y-%m-%d") if booking.created_at else None,
                    "customer_name": f"{booking.requester.first_name} {booking.requester.last_name}" if booking.requester else "Unknown",
                    "service_items": []
                }
                
                # Add service items
                for item in booking.service_items:
                    booking_info["service_items"].append({
                        "type": item.service_type,
                        "description": item.description,
                        "amount": float(item.amount or 0),
                        "status": item.status,
                        "start_date": item.start_date.strftime("%Y-%m-%d") if item.start_date else None,
                        "end_date": item.end_date.strftime("%Y-%m-%d") if item.end_date else None
                    })
                
                data["bookings"].append(booking_info)
            
            # Get basic stats
            data["stats"] = {
                "total_bookings": Booking.query.count(),
                "recent_bookings": Booking.query.filter(
                    Booking.created_at >= datetime.now() - timedelta(days=30)
                ).count()
            }
            
        except Exception as e:
            data["error"] = str(e)
        
        return data
    
    def _generate_ai_response(self, user_query, intent, booking_data, user_context):
        """Generate intelligent AI response using the fetched data"""
        
        system_prompt = f"""
        You are a helpful AI assistant for a travel booking platform. 
        
        User Query: "{user_query}"
        
        Query Analysis: {json.dumps(intent)}
        
        Available Booking Data: {json.dumps(booking_data, indent=2)}
        
        Instructions:
        1. Provide a helpful, conversational response
        2. Include relevant booking information when available
        3. If no specific data found, offer to help with alternative searches
        4. Use a friendly, professional tone
        5. Include booking references, amounts, and key details
        6. Suggest next actions when appropriate
        7. If there are errors, explain them politely
        
        Format your response in a clear, easy-to-read manner with bullet points when listing multiple items.
        """
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_query}
                ],
                max_tokens=800,
                temperature=0.7
            )
            
            ai_response = response.choices[0].message.content
            
            return {
                "response": ai_response,
                "booking_data": booking_data,
                "intent": intent,
                "success": True
            }
            
        except Exception as e:
            return {
                "response": f"I apologize, but I'm having trouble processing your request right now. Error: {str(e)}",
                "booking_data": booking_data,
                "intent": intent,
                "success": False,
                "error": str(e)
            }
    
    def get_booking_summary(self, booking_id):
        """Get detailed summary of a specific booking"""
        try:
            booking = Booking.query.get(booking_id)
            if not booking:
                return {"error": "Booking not found"}
            
            summary_query = f"Provide a detailed summary of booking {booking.reference_number}"
            
            booking_data = {
                "bookings": [self._format_booking_detail(booking)],
                "stats": {}
            }
            
            return self._generate_ai_response(
                summary_query,
                {"intent": "booking_details", "entities": {"booking_id": booking_id}},
                booking_data,
                None
            )
        except Exception as e:
            return {"error": str(e), "success": False}
    
    def _format_booking_detail(self, booking):
        """Format booking with full details"""
        return {
            "id": booking.id,
            "reference_number": booking.reference_number,
            "status": booking.status,
            "total_amount": float(booking.total_amount or 0),
            "created_at": booking.created_at.strftime("%Y-%m-%d %H:%M") if booking.created_at else None,
            "customer": {
                "name": f"{booking.requester.first_name} {booking.requester.last_name}" if booking.requester else "Unknown",
                "email": booking.requester.email if booking.requester else None
            },
            "service_items": [
                {
                    "type": item.service_type,
                    "description": item.description,
                    "amount": float(item.amount or 0),
                    "status": item.status,
                    "dates": f"{item.start_date} to {item.end_date}" if item.start_date and item.end_date else None
                }
                for item in booking.service_items
            ],
            "payments": [
                {
                    "amount": float(payment.amount),
                    "date": payment.payment_date.strftime("%Y-%m-%d") if payment.payment_date else None,
                    "method": payment.payment_method
                }
                for payment in booking.payments
            ]
        }

# Global instance
travel_ai = TravelAIAssistant()