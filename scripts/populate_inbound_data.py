"""Populate database with realistic inbound request test data"""
from app import create_app, db
from app.models.user import User, Agent, create_test_data
from app.models.customer import Customer
from app.models.supplier import Supplier
from app.models.inbound import InboundRequest, ItineraryRow
from datetime import datetime, date, timedelta
import random

def main():
    app = create_app()
    with app.app_context():
        # First, ensure basic users and agents exist
        create_test_data()
        admin_user = User.query.get(1)

        print("Creating test inbound requests...")

        # Create some test customers if they don't exist
        if Customer.query.count() == 0:
            customers = [
                Customer(first_name="Smith", last_name="Family Group", email="john@example.com", phone="123-456-7890"),
                Customer(first_name="Corporate", last_name="Tours Ltd", email="corp@example.com", phone="987-654-3210"),
                Customer(first_name="Adventure", last_name="Club", email="adventure@example.com", phone="555-123-4567"),
                Customer(first_name="Education", last_name="Tours", email="education@example.com", phone="555-987-6543"),
            ]
            db.session.add_all(customers)
            db.session.commit()
            print(f"Created {len(customers)} test customers")

        # Create suppliers if they don't exist
        if Supplier.query.count() == 0:
            suppliers = [
                Supplier(
                    name="Grand Amman Hotel",
                    code="HOTEL001",
                    supplier_type="HOTEL",
                    contact_person="Ahmed",
                    email="info@grandamman.com",
                    phone="+962 6 555 1111",
                    is_active=True
                ),
                Supplier(
                    name="Desert Transport Co",
                    code="TRANS001",
                    supplier_type="TRANSPORT",
                    contact_person="Mohammed",
                    email="bookings@deserttransport.com",
                    phone="+962 6 555 2222",
                    is_active=True
                ),
                Supplier(
                    name="Petra Meals",
                    code="MEAL001",
                    supplier_type="RESTAURANT",
                    contact_person="Sara",
                    email="catering@petramels.com",
                    phone="+962 3 555 3333",
                    is_active=True
                ),
            ]
            db.session.add_all(suppliers)
            db.session.commit()
            print(f"Created {len(suppliers)} test suppliers")

        # Create inbound requests with different statuses
        if InboundRequest.query.count() == 0:
            customers = Customer.query.all()

            requests_data = [
                # REQUEST status
                {
                    "status": "REQUEST",
                    "from_date": date.today() + timedelta(days=7),
                    "to_date": date.today() + timedelta(days=14),
                    "contact_name": "John Smith",
                    "nationality": "USA (4)",
                    "pax": 4,
                    "customer": customers[0] if customers else None,
                },
                {
                    "status": "REQUEST",
                    "from_date": date.today() + timedelta(days=10),
                    "to_date": date.today() + timedelta(days=17),
                    "contact_name": "Jane Doe",
                    "nationality": "Canada (2)",
                    "pax": 2,
                    "customer": customers[1] if len(customers) > 1 else None,
                },
                # CONFIRMED status
                {
                    "status": "CONFIRMED",
                    "from_date": date.today() + timedelta(days=5),
                    "to_date": date.today() + timedelta(days=12),
                    "contact_name": "Corporate Group",
                    "nationality": "UK (8)",
                    "pax": 8,
                    "customer": customers[2] if len(customers) > 2 else None,
                    "is_saved": True,
                },
                {
                    "status": "BOOKED",
                    "from_date": date.today() + timedelta(days=2),
                    "to_date": date.today() + timedelta(days=9),
                    "contact_name": "Adventure Group",
                    "nationality": "Australia (5)",
                    "pax": 5,
                    "customer": customers[3] if len(customers) > 3 else None,
                    "is_saved": True,
                },
                # INVOICED status
                {
                    "status": "COMPLETED",
                    "from_date": date.today() - timedelta(days=20),
                    "to_date": date.today() - timedelta(days=13),
                    "contact_name": "Family Tour",
                    "nationality": "Germany (6)",
                    "pax": 6,
                    "customer": customers[0] if customers else None,
                    "is_saved": True,
                },
                {
                    "status": "INVOICED",
                    "from_date": date.today() - timedelta(days=15),
                    "to_date": date.today() - timedelta(days=8),
                    "contact_name": "School Group",
                    "nationality": "France (10)",
                    "pax": 10,
                    "customer": customers[1] if len(customers) > 1 else None,
                    "is_saved": True,
                },
                # IN_PROGRESS status
                {
                    "status": "IN_PROGRESS",
                    "from_date": date.today() - timedelta(days=2),
                    "to_date": date.today() + timedelta(days=5),
                    "contact_name": "Current Tour",
                    "nationality": "Italy (4)",
                    "pax": 4,
                    "customer": customers[2] if len(customers) > 2 else None,
                    "is_saved": True,
                },
            ]

            created_count = 0
            for req_data in requests_data:
                try:
                    from_date = req_data["from_date"]
                    to_date = req_data["to_date"]
                    days = (to_date - from_date).days

                    inbound_req = InboundRequest(
                        request_number=InboundRequest.generate_request_number(from_date),
                        status=req_data["status"],
                        from_date=from_date,
                        to_date=to_date,
                        no_of_days=days,
                        contact_name=req_data["contact_name"],
                        nationality=req_data["nationality"],
                        pax=req_data["pax"],
                        customer_type="GROUP",
                        is_saved=req_data.get("is_saved", False),
                        user_id=admin_user.id,
                        customer_id=req_data["customer"].id if req_data["customer"] else None,
                        arrival_point="Queen Alia Airport",
                        departure_point="Queen Alia Airport",
                        total_amount=req_data["pax"] * 500 * days,  # $500 per person per day
                        total_currency="USD",
                    )

                    db.session.add(inbound_req)
                    db.session.flush()

                    # Add some itinerary rows
                    for day_offset in range(days):
                        row_date = from_date + timedelta(days=day_offset)
                        activity_type = random.choice(["Hotel", "Hotel & Meals", "Full Day Tour", "Transport & Meals"])

                        itinerary_row = ItineraryRow(
                            request_id=inbound_req.id,
                            date=row_date,
                            description=activity_type,
                            flag_hotel=True if "Hotel" in activity_type else random.choice([True, False]),
                            flag_transport=True,
                            flag_meal="Meals" in activity_type or "Full Day" in activity_type,
                            flag_guide=random.choice([True, False]),
                            flag_airport=day_offset == 0 or day_offset == days - 1,
                        )
                        db.session.add(itinerary_row)

                    created_count += 1
                except Exception as e:
                    print(f"Error creating request {req_data.get('contact_name')}: {e}")
                    import traceback
                    traceback.print_exc()
                    db.session.rollback()
                    continue

            db.session.commit()
            print(f"Created {created_count} inbound requests with itineraries")

        # Print summary
        print("\nDatabase Summary:")
        print(f"Users: {User.query.count()}")
        print(f"Customers: {Customer.query.count()}")
        print(f"Suppliers: {Supplier.query.count()}")
        print(f"Inbound Requests: {InboundRequest.query.count()}")

        from app.models.inbound import InboundRequest as IR
        print(f"  - REQUEST: {IR.query.filter_by(status='REQUEST').count()}")
        print(f"  - CONFIRMED: {IR.query.filter(IR.status.in_(['CONFIRMED', 'BOOKED'])).count()}")
        print(f"  - INVOICED: {IR.query.filter(IR.status.in_(['INVOICED', 'COMPLETED'])).count()}")
        print(f"  - IN_PROGRESS: {IR.query.filter_by(status='IN_PROGRESS').count()}")

        print("\nTest data population complete!")

if __name__ == "__main__":
    main()
