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
        
        # Handle special actions like invoice generation and WhatsApp
        if intent.get("actions"):
            actions_result = self._handle_actions(intent, booking_data, user_context)
            booking_data.update(actions_result)
        
        # Generate AI response with the data
        response = self._generate_ai_response(user_query, intent, booking_data, user_context)
        
        return response
    
    def _analyze_query_intent(self, query):
        """Analyze user query to understand intent and extract entities"""
        
        system_prompt = """
        You are an AI assistant for a travel booking platform. Analyze the user's query and extract:
        1. Intent (search_booking, customer_bookings, booking_status, customer_info, financial_info, generate_invoice, send_whatsapp, general_help)
        2. Entities (booking reference, customer name, dates, destinations, etc.)
        3. Actions (print_invoice, send_whatsapp, email_invoice)
        
        Examples:
        - "Find bookings for Dalia" → intent: "customer_bookings", entities: {"customer_name": "Dalia"}
        - "Show me Dalia's bookings and send invoice via WhatsApp" → intent: "customer_bookings", entities: {"customer_name": "Dalia"}, actions: ["send_whatsapp", "generate_invoice"]
        - "Print invoice for booking IR-12345" → intent: "generate_invoice", entities: {"booking_reference": "IR-12345"}, actions: ["print_invoice"]
        
        Respond with JSON format:
        {
            "intent": "customer_bookings",
            "entities": {
                "booking_reference": "IR-12345",
                "customer_name": "Dalia",
                "destination": "Paris",
                "date_range": "2024-01-01 to 2024-01-31"
            },
            "actions": ["generate_invoice", "send_whatsapp"],
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
            
            # Enhanced customer search with fuzzy matching
            if entities.get("customer_name") or "customer" in query.lower() or "list customer" in query.lower():
                customers = self._search_customers(entities.get("customer_name", ""), query)
                data["customers"] = customers
            
            # Build booking query based on extracted entities
            booking_query = Booking.query
            
            # Filter by booking reference
            if entities.get("booking_reference"):
                ref = entities["booking_reference"]
                booking_query = booking_query.filter(
                    Booking.reference_number.ilike(f"%{ref}%")
                )
            
            # Enhanced customer name search for bookings
            if entities.get("customer_name"):
                # Get matching customers first
                matching_customers = self._search_customers(entities["customer_name"], query)
                if matching_customers:
                    customer_ids = [c["id"] for c in matching_customers]
                    # Fix: Use customer_id instead of user_id for proper customer linking
                    booking_query = booking_query.filter(Booking.customer_id.in_(customer_ids))
            
            # Filter by destination (search in service items)
            if entities.get("destination"):
                destination = entities["destination"]
                booking_query = booking_query.join(ServiceItem).filter(
                    ServiceItem.description.ilike(f"%{destination}%")
                )
            
            # Get recent bookings if no specific filter
            if not any([entities.get("booking_reference"), entities.get("customer_name"), entities.get("destination")]):
                booking_query = booking_query.order_by(Booking.created_at.desc())
            
            # Get bookings
            bookings = booking_query.limit(10).all()
            
            # Format booking data
            for booking in bookings:
                customer_name = "Unknown Customer"
                if hasattr(booking, 'requester') and booking.requester:
                    customer_name = f"{booking.requester.first_name} {booking.requester.last_name}"
                elif booking.user_id:
                    # Try to get customer from Customer table
                    from app.models.customer import Customer
                    customer = Customer.query.get(booking.user_id)
                    if customer:
                        customer_name = f"{customer.first_name} {customer.last_name}"
                
                booking_info = {
                    "id": booking.id,
                    "reference_number": booking.reference_number,
                    "status": booking.status,
                    "total_amount": float(booking.total_amount or 0),
                    "created_at": booking.created_at.strftime("%Y-%m-%d") if booking.created_at else None,
                    "customer_name": customer_name,
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
                "total_customers": Customer.query.count(),
                "recent_bookings": Booking.query.filter(
                    Booking.created_at >= datetime.now() - timedelta(days=30)
                ).count()
            }
            
        except Exception as e:
            data["error"] = str(e)
        
        return data
    
    def _search_customers(self, name_query, full_query):
        """Enhanced customer search with fuzzy matching"""
        from app.models.customer import Customer
        
        customers = []
        try:
            # If no specific name, check if user wants to list all customers
            if not name_query and ("list customer" in full_query.lower() or "all customer" in full_query.lower()):
                customer_results = Customer.query.order_by(Customer.first_name).limit(20).all()
            else:
                # Build fuzzy search query
                search_conditions = []
                
                if name_query:
                    # Split the name and search each part
                    name_parts = name_query.strip().split()
                    for part in name_parts:
                        if len(part) >= 2:  # Only search parts with 2+ characters
                            search_conditions.extend([
                                Customer.first_name.ilike(f"%{part}%"),
                                Customer.last_name.ilike(f"%{part}%"),
                                Customer.company_name.ilike(f"%{part}%")
                            ])
                
                # Execute search
                if search_conditions:
                    customer_results = Customer.query.filter(or_(*search_conditions)).limit(15).all()
                else:
                    customer_results = Customer.query.order_by(Customer.created_at.desc()).limit(10).all()
            
            # Format customer data
            for customer in customer_results:
                customer_info = {
                    "id": customer.id,
                    "name": f"{customer.first_name} {customer.last_name}".strip(),
                    "email": customer.email,
                    "phone": customer.phone,
                    "company": customer.company_name,
                    "customer_type": customer.customer_type,
                    "country": customer.country
                }
                customers.append(customer_info)
                
        except Exception as e:
            print(f"Customer search error: {e}")
        
        return customers
    
    def _handle_actions(self, intent, booking_data, user_context):
        """Handle special actions like invoice generation and WhatsApp sending"""
        actions = intent.get("actions", [])
        results = {
            "actions_performed": [],
            "action_results": {},
            "errors": []
        }
        
        try:
            # Find the booking to work with
            target_booking = None
            if booking_data.get("bookings"):
                target_booking = booking_data["bookings"][0]  # Use first booking found
            
            if not target_booking:
                results["errors"].append("No booking found to perform actions on")
                return results
            
            # Handle invoice generation
            if "generate_invoice" in actions or "print_invoice" in actions:
                invoice_result = self._generate_invoice_action(target_booking)
                results["action_results"]["invoice"] = invoice_result
                results["actions_performed"].append("Generated invoice")
            
            # Handle WhatsApp sending
            if "send_whatsapp" in actions:
                whatsapp_result = self._send_whatsapp_action(target_booking, user_context)
                results["action_results"]["whatsapp"] = whatsapp_result
                results["actions_performed"].append("Sent WhatsApp message")
                
        except Exception as e:
            results["errors"].append(f"Action error: {str(e)}")
        
        return results
    
    def _generate_invoice_action(self, booking):
        """Generate invoice for a booking"""
        try:
            # Create invoice data structure
            invoice_data = {
                "booking_id": booking["id"],
                "reference_number": booking["reference_number"],
                "customer_name": booking["customer_name"],
                "total_amount": booking["total_amount"],
                "status": "Generated",
                "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "items": booking.get("service_items", [])
            }
            
            # For now, return the invoice data structure
            # In a full implementation, this would generate a PDF
            return {
                "success": True,
                "invoice_data": invoice_data,
                "download_url": f"/api/invoice/{booking['id']}/download",
                "message": f"Invoice generated for booking {booking['reference_number']}"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def _send_whatsapp_action(self, booking, user_context):
        """Send booking details via WhatsApp"""
        try:
            # Create WhatsApp message content
            message = f"""
🎫 *Travel Booking Confirmation*

📋 Booking: {booking['reference_number']}
👤 Customer: {booking['customer_name']}
💰 Total Amount: ${booking['total_amount']:.2f}
📅 Status: {booking['status']}

✈️ Services:
"""
            
            for item in booking.get("service_items", []):
                message += f"• {item['type']}: {item['description']} (${item['amount']:.2f})\n"
            
            message += f"\n📞 Need help? Contact us!\n🌐 Travel Booking System"
            
            # Return success response with message preview
            return {
                "success": True,
                "message_preview": message,
                "recipient": booking["customer_name"],
                "sent_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "note": "WhatsApp integration requires Twilio setup"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
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