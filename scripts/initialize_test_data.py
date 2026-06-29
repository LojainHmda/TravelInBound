    """
    Initialize test data in the database for testing
    """
    from app import create_app, db
    from app.models.user import User, Agent, create_test_data
    from app.models.customer import Customer
    from app.models.supplier import Supplier
    from app.models.finance import ExpenseCategory
    from datetime import datetime

    def main():
        """Create initial test data in the database"""
        app = create_app()
        with app.app_context():
            print("Creating initial test data...")

            # First, create test users and agents
            create_test_data()
            print("Created test users and agents")

            # Create a few customers for testing
            if Customer.query.count() == 0:
                print("Creating test customers...")
                customers = [
                    Customer(
                        name="John Smith",
                        email="john@example.com",
                        phone="123-456-7890",
                        address="123 Main St, City",
                        notes="VIP customer"
                    ),
                    Customer(
                        name="Jane Doe",
                        email="jane@example.com",
                        phone="987-654-3210",
                        address="456 Oak Ave, Town",
                        notes="Regular customer"
                    ),
                    Customer(
                        name="Corporate Client",
                        email="corporate@example.com",
                        phone="555-123-4567",
                        address="789 Business Blvd, City",
                        notes="Corporate account, special rates"
                    )
                ]
                db.session.add_all(customers)
                print("Created test customers")

            # Create suppliers (add 3 example suppliers for inbound system)
            existing_supplier_count = Supplier.query.count()
            if existing_supplier_count < 3:
                print(f"Creating example suppliers (found {existing_supplier_count} existing)...")

                # Check which suppliers already exist by code
                existing_codes = {s.code for s in Supplier.query.all()}

                suppliers_to_add = []

                # Hotel Supplier
                if "HOTEL01" not in existing_codes:
                    suppliers_to_add.append(Supplier(
                        name="Grand Jordan Hotel",
                        code="HOTEL01",
                        supplier_type="HOTEL",
                        contact_person="Ahmed Al-Mansour",
                        email="reservations@grandjordan.com",
                        phone="+962 6 555 1234",
                        address="King Hussein Street",
                        city="Amman",
                        country="Jordan",
                        payment_terms="NET 30",
                        default_currency="USD",
                        is_active=True
                    ))

                # Transport Supplier
                if "TRANS01" not in existing_codes:
                    suppliers_to_add.append(Supplier(
                        name="Jordan Express Transport",
                        code="TRANS01",
                        supplier_type="TRANSPORT",
                        contact_person="Mohammed Hassan",
                        email="bookings@jordanexpress.com",
                        phone="+962 6 555 5678",
                        address="Airport Road",
                        city="Amman",
                        country="Jordan",
                        payment_terms="NET 15",
                        default_currency="USD",
                        is_active=True
                    ))

                # Restaurant Supplier
                if "REST01" not in existing_codes:
                    suppliers_to_add.append(Supplier(
                        name="Petra Restaurant Group",
                        code="REST01",
                        supplier_type="RESTAURANT",
                        contact_person="Sara Khoury",
                        email="events@petrarestaurants.com",
                        phone="+962 3 555 9012",
                        address="Tourism Street",
                        city="Petra",
                        country="Jordan",
                        payment_terms="NET 30",
                        default_currency="USD",
                        is_active=True
                    ))

                if suppliers_to_add:
                    db.session.add_all(suppliers_to_add)
                    db.session.commit()
                    print(f"Created {len(suppliers_to_add)} example suppliers")
                else:
                    print("All example suppliers already exist")

            # Create expense categories if they don't exist
            if ExpenseCategory.query.count() == 0:
                from app.models.finance import (
                    EXPENSE_CATEGORY_RENT, EXPENSE_CATEGORY_UTILITIES, EXPENSE_CATEGORY_SALARIES,
                    EXPENSE_CATEGORY_MARKETING, EXPENSE_CATEGORY_INSURANCE, EXPENSE_CATEGORY_SUPPLIES,
                    EXPENSE_CATEGORY_TRAVEL, EXPENSE_CATEGORY_TAXES, EXPENSE_CATEGORY_SOFTWARE,
                    EXPENSE_CATEGORY_TELECOM, EXPENSE_CATEGORY_MAINTENANCE, EXPENSE_CATEGORY_OTHER
                )

                print("Creating expense categories...")
                categories = [
                    ExpenseCategory(name=EXPENSE_CATEGORY_RENT, description="Office rent and lease expenses"),
                    ExpenseCategory(name=EXPENSE_CATEGORY_UTILITIES, description="Electricity, water, etc."),
                    ExpenseCategory(name=EXPENSE_CATEGORY_SALARIES, description="Employee salaries and benefits"),
                    ExpenseCategory(name=EXPENSE_CATEGORY_MARKETING, description="Marketing and advertising"),
                    ExpenseCategory(name=EXPENSE_CATEGORY_INSURANCE, description="Business insurance"),
                    ExpenseCategory(name=EXPENSE_CATEGORY_SUPPLIES, description="Office supplies"),
                    ExpenseCategory(name=EXPENSE_CATEGORY_TRAVEL, description="Business travel expenses"),
                    ExpenseCategory(name=EXPENSE_CATEGORY_TAXES, description="Business taxes"),
                    ExpenseCategory(name=EXPENSE_CATEGORY_SOFTWARE, description="Software subscriptions"),
                    ExpenseCategory(name=EXPENSE_CATEGORY_TELECOM, description="Phone and internet expenses"),
                    ExpenseCategory(name=EXPENSE_CATEGORY_MAINTENANCE, description="Equipment maintenance"),
                    ExpenseCategory(name=EXPENSE_CATEGORY_OTHER, description="Miscellaneous expenses")
                ]
                db.session.add_all(categories)
                print("Created expense categories")

            # Commit all changes
            db.session.commit()
            print("All test data created successfully!")

            # Print summary of data
            print("\nDatabase Summary:")
            print(f"Users: {User.query.count()}")
            print(f"Agents: {Agent.query.count()}")
            print(f"Customers: {Customer.query.count()}")
            print(f"Suppliers: {Supplier.query.count()}")
            print(f"Expense Categories: {ExpenseCategory.query.count()}")

    if __name__ == "__main__":
        main()