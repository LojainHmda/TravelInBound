from app import create_app, db
from app.models.inbound import InboundRequest, ItineraryRow
from app.models.user import User
from app.models.customer import Customer
from datetime import date, timedelta

app = create_app()
with app.app_context():
    admin_user = User.query.get(1)
    customers = Customer.query.all()

    print(f'Admin user ID: {admin_user.id}')
    print(f'Customers: {[c.id for c in customers]}')

    requests_data = [
        {'status': 'CONFIRMED', 'from_date': date.today() + timedelta(days=5), 'to_date': date.today() + timedelta(days=12), 'contact_name': 'Corp', 'pax': 8},
        {'status': 'BOOKED', 'from_date': date.today() + timedelta(days=2), 'to_date': date.today() + timedelta(days=9), 'contact_name': 'Adv', 'pax': 5},
        {'status': 'COMPLETED', 'from_date': date.today() - timedelta(days=20), 'to_date': date.today() - timedelta(days=13), 'contact_name': 'Fam', 'pax': 6},
    ]

    for i, req_data in enumerate(requests_data):
        try:
            from_date = req_data['from_date']
            to_date = req_data['to_date']
            days = (to_date - from_date).days
            req_num = InboundRequest.generate_request_number(from_date)

            print(f'\n[{i}] Creating {req_data["status"]} request {req_num}')

            inbound_req = InboundRequest(
                request_number=req_num,
                status=req_data['status'],
                from_date=from_date,
                to_date=to_date,
                no_of_days=days,
                contact_name=req_data['contact_name'],
                nationality=req_data['status'],
                pax=req_data['pax'],
                customer_type='GROUP',
                is_saved=True,
                user_id=admin_user.id,
                customer_id=customers[0].id,
                arrival_point='Airport',
                departure_point='Airport',
                total_amount=req_data['pax'] * 500 * days,
                total_currency='USD',
            )
            db.session.add(inbound_req)
            db.session.flush()
            print(f'  Added to session')

            db.session.commit()
            print(f'  Committed: {inbound_req.request_number}')
        except Exception as e:
            print(f'  ERROR: {e}')
            import traceback
            traceback.print_exc()
            db.session.rollback()

    print(f'\nTotal requests: {InboundRequest.query.count()}')
