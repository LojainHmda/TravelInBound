# P1 Schema & Migrations Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add supplier_id FK to inbound_hotel and inbound_meal (linking bookings to master supplier table), and remove the legacy booking system that duplicates the inbound system.

**Architecture:** Each service type (hotel, meal) gains a `supplier_id` FK referencing `supplier.id`. The existing free-text name field stays as an optional display override. Two new Alembic migrations handle the schema changes on TEST DB only. The legacy booking blueprint (Booking, ServiceItem, ServiceConfirmation, Payment models) is removed — it was never used by the inbound system and only adds confusion.

**Tech Stack:** Flask-Migrate/Alembic, SQLAlchemy, psycopg2, PostgreSQL (TEST DB)

**Prerequisite:** P0 Foundation plan must be complete. Flask-Migrate must be initialized.

## Global Constraints

- ALL schema changes via `flask db migrate` + `flask db upgrade` — no raw ALTER TABLE scripts
- DATABASE_URL_TEST only — never run migrations against DATABASE_URL
- inbound_hotel.hotel_name and inbound_meal.restaurant stay as nullable text (display override)
- supplier_id FK is nullable (existing rows have no supplier — don't break them)
- UI stays exactly the same — no template changes
- Legacy booking removal: delete booking.py route, booking model, booking templates ONLY after confirming no inbound route imports from them

---

## File Map

```
MODIFY  app/models/inbound.py         add supplier_id FK + relationship to InboundHotel
MODIFY  app/models/inbound.py         verify InboundMeal.supplier_id already exists (it does)
DELETE  app/routes/booking.py         legacy booking system route
DELETE  app/models/booking.py         legacy Booking, Payment models
DELETE  app/templates/booking/        all booking templates
DELETE  app/static/js/booking.js      booking JS
DELETE  app/forms/booking.py          booking forms
MODIFY  app/__init__.py               remove booking_bp registration
MODIFY  app/models/__init__.py        remove Booking import
CREATE  migrations/versions/xxxx_add_supplier_fk_to_hotel.py    (auto-generated)
CREATE  tests/test_supplier_fk.py     FK integrity tests
```

---

### Task 1: Verify inbound_meal already has supplier_id

**Files:**
- Read: `app/models/inbound.py` (InboundMeal section)

- [ ] **Step 1: Check InboundMeal**

```bash
grep -n "supplier_id" app/models/inbound.py
```
Expected output includes:
```
660:    supplier_id = db.Column(db.Integer, db.ForeignKey('supplier.id'), nullable=True)
```

If present → InboundMeal is already correct. Proceed to Task 2.
If missing → add it (same pattern as Task 2 below).

- [ ] **Step 2: Verify InboundTransport supplier_id too**

```bash
grep -n "supplier_id" app/models/inbound.py | grep -i transport
```
Expected: line ~581 with `supplier_id = db.Column(db.Integer, db.ForeignKey('supplier.id'), nullable=True)`

All service types except InboundHotel already have supplier_id. Only hotel needs the fix.

---

### Task 2: Add supplier_id FK to InboundHotel

**Files:**
- Modify: `app/models/inbound.py` (InboundHotel class, lines ~439-488)

- [ ] **Step 1: Add supplier_id column to InboundHotel**

In `app/models/inbound.py`, inside `class InboundHotel(db.Model)`, after the `source_itinerary_id` line, add:

```python
# Supplier FK — links hotel booking to master supplier (type=ACCOMMODATION)
# nullable: existing rows have no supplier_id; hotel_name stays as display override
supplier_id = db.Column(db.Integer, db.ForeignKey('supplier.id'), nullable=True)
```

- [ ] **Step 2: Add relationship**

After the `rooms` relationship in InboundHotel, add:

```python
supplier_ref = db.relationship('Supplier', foreign_keys=[supplier_id], lazy='joined')
```

- [ ] **Step 3: Verify model loads**

```bash
.venv/Scripts/python.exe -c "
from app import create_app
app = create_app()
with app.app_context():
    from app.models.inbound import InboundHotel
    print('supplier_id' in [c.key for c in InboundHotel.__table__.columns])
"
```
Expected: `True`

- [ ] **Step 4: Generate migration**

```bash
.venv/Scripts/python.exe -m flask --app start_server:app db migrate -m "add supplier_id FK to inbound_hotel"
```
Expected: new file in `migrations/versions/` containing:
```python
op.add_column('inbound_hotel', sa.Column('supplier_id', sa.Integer(), nullable=True))
op.create_foreign_key(None, 'inbound_hotel', 'supplier', ['supplier_id'], ['id'])
```

- [ ] **Step 5: Apply to TEST DB**

```bash
.venv/Scripts/python.exe -m flask --app start_server:app db upgrade
```
Expected: `Running upgrade ... add supplier_id FK to inbound_hotel`

- [ ] **Step 6: Verify TEST DB column exists**

```bash
.venv/Scripts/python.exe -c "
from app import create_app
from app.extensions import db
from sqlalchemy import inspect, text
app = create_app()
with app.app_context():
    cols = [c['name'] for c in inspect(db.engine).get_columns('inbound_hotel')]
    print('supplier_id in inbound_hotel:', 'supplier_id' in cols)
"
```
Expected: `supplier_id in inbound_hotel: True`

- [ ] **Step 7: Commit**

```bash
git add app/models/inbound.py migrations/
git commit -m "feat: add supplier_id FK to inbound_hotel, migration applied to TEST DB"
```

---

### Task 3: Add supplier_id FK to InboundHotelRoom (for per-room supplier override)

**Files:**
- Modify: `app/models/inbound.py` (HotelRoom class)

Note: HotelRoom already has `supplier_name` as text. Adding FK is optional — the hotel-level supplier_id is sufficient for most analytics. Skip this task if the user doesn't need per-room supplier tracking.

**Decision: SKIP** — hotel-level FK is sufficient per YAGNI. Per-room supplier tracking can be added later if needed.

---

### Task 4: Audit and remove legacy booking system

**CAUTION: Read carefully before deleting anything.**

The legacy booking system consists of:
- `app/routes/booking.py` — BookingBP routes (SessionService, ServiceItem CRUD)
- `app/models/booking.py` — Booking, Payment models
- `app/forms/booking.py` — booking forms
- `app/static/js/booking.js` — booking JS

The inbound system does NOT use any of these. Confirm before deleting:

- [ ] **Step 1: Confirm no inbound route imports from booking**

```bash
grep -r "from app.models.booking\|from app.routes.booking\|import booking" app/routes/inbound.py app/routes/main.py app/routes/finance.py
```
Expected: no output (no imports from booking system in active routes)

- [ ] **Step 2: Confirm no templates import booking**

```bash
grep -r "booking_bp\|url_for.*booking\." app/templates/inbound/ app/templates/index.html app/templates/base.html
```
Expected: no output, or only references to `/booking/` URLs that were already unused

- [ ] **Step 3: Check what references Booking model**

```bash
grep -r "from app.models.booking\|models.booking\|Booking\b" app/routes/ app/models/
```
Note which files reference Booking. If `app/models/invoice.py` does, check it — Invoice has `booking_id` FK. This FK must stay but can be made nullable or removed.

- [ ] **Step 4: Remove booking_bp from __init__.py**

In `app/__init__.py`, remove:
```python
from app.routes.booking import booking_bp
app.register_blueprint(booking_bp, url_prefix='/booking')
```

- [ ] **Step 5: Delete legacy files**

```bash
# Routes
rm app/routes/booking.py
rm app/forms/booking.py
rm app/static/js/booking.js

# Templates (only booking-specific ones)
rm -rf app/templates/booking/
```

Do NOT delete `app/models/booking.py` yet — Invoice model has `booking_id` FK. Leave model but strip it to just what Invoice needs (Booking class with id only).

- [ ] **Step 6: Strip booking.py model to minimum**

Replace `app/models/booking.py` content with only what's needed to keep Invoice FK valid:

```python
from app.extensions import db
from datetime import datetime


class Booking(db.Model):
    """Minimal stub — kept for Invoice.booking_id FK compatibility only."""
    __tablename__ = 'booking'

    id = db.Column(db.Integer, primary_key=True)
    reference_number = db.Column(db.String(50), unique=True, nullable=True)
    status = db.Column(db.String(20), default='REQUEST')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Payment(db.Model):
    """Stub — legacy payment model."""
    __tablename__ = 'payment'

    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.Integer, db.ForeignKey('booking.id'), nullable=True)
    amount = db.Column(db.Float, nullable=True)
    payment_date = db.Column(db.DateTime, nullable=True)
```

- [ ] **Step 7: Verify app starts without booking blueprint**

```bash
.venv/Scripts/python.exe -c "from app import create_app; app = create_app(); print('OK')"
```
Expected: `OK` — no ImportError, no routing errors

- [ ] **Step 8: Commit**

```bash
git add app/__init__.py app/models/booking.py
git rm app/routes/booking.py app/forms/booking.py app/static/js/booking.js
git rm -r app/templates/booking/
git commit -m "refactor: remove legacy booking system, keep Booking stub for Invoice FK"
```

---

### Task 5: Supplier FK integration tests

**Files:**
- Create: `tests/test_supplier_fk.py`

- [ ] **Step 1: Write tests**

```python
def test_inbound_hotel_has_supplier_id_column(app):
    from app.models.inbound import InboundHotel
    col_names = [c.key for c in InboundHotel.__table__.columns]
    assert 'supplier_id' in col_names


def test_inbound_meal_has_supplier_id_column(app):
    from app.models.inbound import InboundMeal
    col_names = [c.key for c in InboundMeal.__table__.columns]
    assert 'supplier_id' in col_names


def test_inbound_transport_has_supplier_id_column(app):
    from app.models.inbound import InboundTransport
    col_names = [c.key for c in InboundTransport.__table__.columns]
    assert 'supplier_id' in col_names


def test_inbound_guide_has_supplier_id_column(app):
    from app.models.inbound import InboundGuide
    col_names = [c.key for c in InboundGuide.__table__.columns]
    assert 'supplier_id' in col_names


def test_hotel_supplier_fk_references_supplier_table(app):
    from app.models.inbound import InboundHotel
    fk = next(
        (fk for fk in InboundHotel.__table__.foreign_keys
         if 'supplier' in str(fk.column).lower()),
        None
    )
    assert fk is not None, "InboundHotel.supplier_id has no FK to supplier table"


def test_hotel_supplier_id_is_nullable(app):
    from app.models.inbound import InboundHotel
    col = InboundHotel.__table__.columns['supplier_id']
    assert col.nullable is True, "supplier_id must be nullable (existing rows have no supplier)"
```

- [ ] **Step 2: Run**

```bash
.venv/Scripts/python.exe -m pytest tests/test_supplier_fk.py -v
```
Expected: 6 tests pass.

- [ ] **Step 3: Commit**

```bash
git add tests/test_supplier_fk.py
git commit -m "test: add supplier FK integrity tests (6 passing)"
```

---

## Plan Complete

After all 5 tasks:
- InboundHotel has `supplier_id` FK → `supplier` table
- All service types (hotel, meal, transport, guide) have supplier FK
- Migration applied to TEST DB via Alembic
- Legacy booking system removed
- 6 FK tests passing

**Next plan:** `2026-06-28-p2-data-model.md` — normalize JSON blobs, document storage.
