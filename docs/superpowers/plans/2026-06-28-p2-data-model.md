# P2 Data Model Improvements Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace JSON blobs (expense sheets, invoice data) with proper normalized tables. Route all voucher/document generation through the existing `inbound_document` table. Formalize two-level status (service-level vs request-level) with clear enums and rules.

**Architecture:** Three new models replace JSON TEXT columns: `GuideExpenseSheet` (replaces `advance_expense_sheet_data`), `GuidePaymentSheet` (replaces `closing_guide_payment_sheet_data`). Invoice JSON is replaced by `InboundInvoiceLine` table. All generated documents (vouchers, invoices, proformas) are written through a `DocumentService` that saves the file and records metadata in `inbound_document`. Status enums are defined in a central `app/core/enums.py` and imported by all models/routes.

**Tech Stack:** SQLAlchemy, Flask-Migrate, Python dataclasses for status enum

**Prerequisite:** P0 and P1 plans complete. Flask-Migrate initialized.

## Global Constraints

- JSON blob columns stay in DB for backwards compatibility — new tables are additive
- Existing API endpoints for expense sheets keep same URL, same JSON request/response format
- UI stays exactly the same — routes return same data shape as before
- All Alembic migrations target TEST DB only (FLASK_ENV=development)
- Generated files stored under `uploads/documents/<request_id>/` relative to app root
- On Cloud Run: GCS bucket used instead of local filesystem (via storage service)

---

## File Map

```
CREATE  app/core/__init__.py          empty
CREATE  app/core/enums.py             RequestStatus, ServiceStatus enums
CREATE  app/models/expense_sheet.py   GuideExpenseSheet, GuideExpenseSheetItem models
CREATE  app/models/invoice_line.py    InboundInvoiceLine model
CREATE  app/services/storage.py       DocumentStorage: save/get/delete abstraction
MODIFY  app/models/inbound.py         add relationships to new models
MODIFY  app/routes/inbound.py         update advance-expense-sheet API to use new model
MODIFY  app/__init__.py               import new models so SQLAlchemy registers them
CREATE  migrations/versions/xxxx_add_expense_sheet_tables.py   (auto-generated)
CREATE  migrations/versions/xxxx_add_invoice_line_table.py     (auto-generated)
CREATE  tests/test_enums.py           status enum tests
CREATE  tests/test_document_storage.py storage service tests
```

---

### Task 1: Create app/core/enums.py — status constants

**Files:**
- Create: `app/core/__init__.py`
- Create: `app/core/enums.py`

**Produces:** `RequestStatus`, `ServiceStatus` importable from `app.core.enums`

- [ ] **Step 1: Create app/core/__init__.py**

Empty file.

- [ ] **Step 2: Create app/core/enums.py**

```python
"""
Central status definitions.

TWO STATUS LEVELS:
  ServiceStatus  — per-service (hotel, transport, meal, guide)
                   "Confirmed" = supplier sent us confirmation
  RequestStatus  — whole tour file
                   "Confirmed" = customer sent us confirmation
"""


class ServiceStatus:
    REQUEST = 'REQUEST'        # awaiting supplier confirmation
    CONFIRMED = 'CONFIRMED'    # supplier confirmed — deal done
    CANCELLED = 'CANCELLED'    # cancelled with supplier

    ALL = (REQUEST, CONFIRMED, CANCELLED)

    LABELS = {
        REQUEST: 'Requested',
        CONFIRMED: 'Confirmed',
        CANCELLED: 'Cancelled',
    }

    @classmethod
    def label(cls, value: str) -> str:
        return cls.LABELS.get(str(value).upper(), value)


class RequestStatus:
    REQUEST = 'REQUEST'        # initial — customer has not confirmed
    CONFIRMED = 'CONFIRMED'    # customer confirmed the whole tour
    INVOICED = 'INVOICED'      # invoice issued to customer

    # Legacy aliases kept for backwards compatibility
    BOOKED = 'CONFIRMED'
    IN_PROGRESS = 'REQUEST'
    COMPLETED = 'INVOICED'

    ALL = (REQUEST, CONFIRMED, INVOICED)

    LABELS = {
        REQUEST: 'Requested',
        CONFIRMED: 'Confirmed',
        INVOICED: 'Invoiced',
    }

    @classmethod
    def label(cls, value: str) -> str:
        v = str(value).upper()
        # Normalize legacy values
        if v in ('BOOKED', 'IN_PROGRESS', 'PROCESSING', 'QUOTED', 'SUPPLIER_CONFIRMED'):
            v = cls.CONFIRMED
        if v in ('COMPLETED', 'INVOICE'):
            v = cls.INVOICED
        return cls.LABELS.get(v, value)

    @classmethod
    def normalize(cls, value: str) -> str:
        """Convert legacy status string to canonical value."""
        v = str(value).upper()
        if v in ('BOOKED', 'IN_PROGRESS', 'PROCESSING', 'QUOTED', 'SUPPLIER_CONFIRMED'):
            return cls.CONFIRMED
        if v in ('COMPLETED', 'INVOICE'):
            return cls.INVOICED
        return v if v in cls.ALL else cls.REQUEST
```

- [ ] **Step 3: Run tests**

```bash
.venv/Scripts/python.exe -m pytest tests/test_enums.py -v
```

- [ ] **Step 4: Create tests/test_enums.py first**

```python
from app.core.enums import ServiceStatus, RequestStatus


def test_service_status_constants():
    assert ServiceStatus.REQUEST == 'REQUEST'
    assert ServiceStatus.CONFIRMED == 'CONFIRMED'
    assert ServiceStatus.CANCELLED == 'CANCELLED'


def test_service_status_label():
    assert ServiceStatus.label('REQUEST') == 'Requested'
    assert ServiceStatus.label('CONFIRMED') == 'Confirmed'


def test_request_status_normalize_legacy():
    assert RequestStatus.normalize('BOOKED') == 'CONFIRMED'
    assert RequestStatus.normalize('COMPLETED') == 'INVOICED'
    assert RequestStatus.normalize('IN_PROGRESS') == 'CONFIRMED'
    assert RequestStatus.normalize('QUOTED') == 'CONFIRMED'


def test_request_status_label_legacy():
    assert RequestStatus.label('BOOKED') == 'Confirmed'
    assert RequestStatus.label('COMPLETED') == 'Invoiced'


def test_request_status_all_values():
    assert 'REQUEST' in RequestStatus.ALL
    assert 'CONFIRMED' in RequestStatus.ALL
    assert 'INVOICED' in RequestStatus.ALL
```

Run:
```bash
.venv/Scripts/python.exe -m pytest tests/test_enums.py -v
```
Expected: 5 tests pass.

- [ ] **Step 5: Commit**

```bash
git add app/core/ tests/test_enums.py
git commit -m "feat: add central status enums (ServiceStatus, RequestStatus) with legacy normalization"
```

---

### Task 2: Create GuideExpenseSheet models

**Files:**
- Create: `app/models/expense_sheet.py`

**Produces:** `GuideExpenseSheet`, `GuideExpenseSheetItem` models replacing JSON blob `advance_expense_sheet_data`

- [ ] **Step 1: Create app/models/expense_sheet.py**

```python
from datetime import datetime
from app.extensions import db


class GuideExpenseSheet(db.Model):
    """Replaces InboundRequest.advance_expense_sheet_data JSON blob.

    One sheet per request. Items are the expense line rows.
    The old JSON blob is kept for migration period — this is additive.
    """
    __tablename__ = 'guide_expense_sheet'

    id = db.Column(db.Integer, primary_key=True)
    request_id = db.Column(db.Integer, db.ForeignKey('inbound_request.id', ondelete='CASCADE'),
                           nullable=False, unique=True)
    guide_name = db.Column(db.String(200), nullable=True)
    currency = db.Column(db.String(3), default='JOD')
    notes = db.Column(db.Text, nullable=True)
    total_advance = db.Column(db.Float, default=0.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    items = db.relationship('GuideExpenseSheetItem', backref='sheet',
                            cascade='all, delete-orphan', lazy=True)


class GuideExpenseSheetItem(db.Model):
    """One line in the guide advance expense sheet."""
    __tablename__ = 'guide_expense_sheet_item'

    id = db.Column(db.Integer, primary_key=True)
    sheet_id = db.Column(db.Integer,
                         db.ForeignKey('guide_expense_sheet.id', ondelete='CASCADE'),
                         nullable=False)
    date = db.Column(db.Date, nullable=True)
    description = db.Column(db.String(500), nullable=False)
    category = db.Column(db.String(100), nullable=True)   # meals, transport, entrance, etc.
    amount = db.Column(db.Float, nullable=False, default=0.0)
    currency = db.Column(db.String(3), default='JOD')
    notes = db.Column(db.Text, nullable=True)
    sort_order = db.Column(db.Integer, default=0)


class GuidePaymentSheet(db.Model):
    """Replaces InboundRequest.closing_guide_payment_sheet_data JSON blob.

    Final guide payment breakdown after tour completion.
    """
    __tablename__ = 'guide_payment_sheet'

    id = db.Column(db.Integer, primary_key=True)
    request_id = db.Column(db.Integer, db.ForeignKey('inbound_request.id', ondelete='CASCADE'),
                           nullable=False, unique=True)
    guide_name = db.Column(db.String(200), nullable=True)
    currency = db.Column(db.String(3), default='JOD')
    total_days = db.Column(db.Integer, nullable=True)
    daily_rate = db.Column(db.Float, nullable=True)
    total_guide_fee = db.Column(db.Float, default=0.0)
    advance_paid = db.Column(db.Float, default=0.0)
    balance_due = db.Column(db.Float, default=0.0)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    items = db.relationship('GuidePaymentSheetItem', backref='sheet',
                            cascade='all, delete-orphan', lazy=True)


class GuidePaymentSheetItem(db.Model):
    """One line in the guide closing payment sheet."""
    __tablename__ = 'guide_payment_sheet_item'

    id = db.Column(db.Integer, primary_key=True)
    sheet_id = db.Column(db.Integer,
                         db.ForeignKey('guide_payment_sheet.id', ondelete='CASCADE'),
                         nullable=False)
    description = db.Column(db.String(500), nullable=False)
    quantity = db.Column(db.Float, default=1.0)
    unit = db.Column(db.String(50), nullable=True)   # days, hours, pax, etc.
    rate = db.Column(db.Float, default=0.0)
    amount = db.Column(db.Float, default=0.0)
    notes = db.Column(db.Text, nullable=True)
    sort_order = db.Column(db.Integer, default=0)
```

- [ ] **Step 2: Register models in __init__.py**

In `app/__init__.py`, inside `with app.app_context()`, after existing model imports:
```python
from app.models.expense_sheet import GuideExpenseSheet, GuidePaymentSheet  # noqa: F401
```

- [ ] **Step 3: Generate and apply migration**

```bash
.venv/Scripts/python.exe -m flask --app start_server:app db migrate -m "add guide expense and payment sheet tables"
.venv/Scripts/python.exe -m flask --app start_server:app db upgrade
```

- [ ] **Step 4: Verify tables exist in TEST DB**

```bash
.venv/Scripts/python.exe -c "
from app import create_app
from app.extensions import db
from sqlalchemy import inspect
app = create_app()
with app.app_context():
    tables = inspect(db.engine).get_table_names()
    for t in ['guide_expense_sheet', 'guide_expense_sheet_item', 'guide_payment_sheet', 'guide_payment_sheet_item']:
        print(t, ':', t in tables)
"
```
Expected: all 4 print `True`

- [ ] **Step 5: Commit**

```bash
git add app/models/expense_sheet.py app/__init__.py migrations/
git commit -m "feat: add GuideExpenseSheet and GuidePaymentSheet models replacing JSON blobs"
```

---

### Task 3: Create InboundInvoiceLine model

**Files:**
- Create: `app/models/invoice_line.py`

**Produces:** `InboundInvoiceLine` — replaces `admin_invoice_data` and `customer_invoice_data` JSON blobs

- [ ] **Step 1: Create app/models/invoice_line.py**

```python
from datetime import datetime
from app.extensions import db


class InboundInvoiceLine(db.Model):
    """Invoice line item for an inbound request.

    Replaces admin_invoice_data / customer_invoice_data JSON blobs.
    invoice_type: 'admin' or 'customer'
    """
    __tablename__ = 'inbound_invoice_line'

    id = db.Column(db.Integer, primary_key=True)
    request_id = db.Column(db.Integer,
                           db.ForeignKey('inbound_request.id', ondelete='CASCADE'),
                           nullable=False)
    invoice_type = db.Column(db.String(20), nullable=False, default='customer')
    line_order = db.Column(db.Integer, default=0)
    description = db.Column(db.String(500), nullable=False)
    quantity = db.Column(db.Float, default=1.0)
    unit_price = db.Column(db.Float, default=0.0)
    currency = db.Column(db.String(3), default='USD')
    line_total = db.Column(db.Float, default=0.0)
    category = db.Column(db.String(100), nullable=True)  # hotel, transport, guide, etc.
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
```

- [ ] **Step 2: Register in __init__.py**

```python
from app.models.invoice_line import InboundInvoiceLine  # noqa: F401
```

- [ ] **Step 3: Generate and apply migration**

```bash
.venv/Scripts/python.exe -m flask --app start_server:app db migrate -m "add inbound_invoice_line table"
.venv/Scripts/python.exe -m flask --app start_server:app db upgrade
```

- [ ] **Step 4: Commit**

```bash
git add app/models/invoice_line.py app/__init__.py migrations/
git commit -m "feat: add InboundInvoiceLine model replacing invoice JSON blobs"
```

---

### Task 4: Create DocumentStorage service

**Files:**
- Create: `app/services/storage.py`

**Produces:** `DocumentStorage` class with `save(file_obj, request_id, doc_type, filename)` → returns `(relative_path, stored_filename)`

- [ ] **Step 1: Create app/services/storage.py**

```python
"""
Document storage service.

Saves generated files (vouchers, invoices, proformas) to:
  - Local: uploads/documents/<request_id>/<filename>
  - Cloud (GCS): gs://<bucket>/documents/<request_id>/<filename>

Routes should call DocumentStorage.save() and record the returned path
in the inbound_document table.
"""
import os
import uuid
from datetime import datetime


class DocumentStorage:
    """Abstraction over local filesystem and GCS for document storage."""

    def __init__(self, app=None):
        self._app = app
        self._bucket = None

    def init_app(self, app):
        self._app = app
        bucket_name = os.environ.get('GCS_BUCKET_NAME')
        if bucket_name:
            try:
                from google.cloud import storage as gcs
                client = gcs.Client()
                self._bucket = client.bucket(bucket_name)
                app.logger.info(f'DocumentStorage: using GCS bucket {bucket_name}')
            except ImportError:
                app.logger.warning('google-cloud-storage not installed — falling back to local storage')
            except Exception as e:
                app.logger.warning(f'GCS init failed ({e}) — falling back to local storage')

    @property
    def _upload_root(self):
        if self._app:
            return os.path.join(self._app.root_path, '..', 'uploads', 'documents')
        return os.path.join(os.getcwd(), 'uploads', 'documents')

    def save(self, file_bytes: bytes, request_id: int, doc_type: str,
             original_filename: str) -> tuple[str, str]:
        """Save file bytes and return (relative_path, stored_filename).

        stored_filename: UUID-based unique name
        relative_path: path relative to upload_root for serving
        """
        ext = os.path.splitext(original_filename)[1].lower() or '.bin'
        stored_filename = f"{doc_type}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}{ext}"
        relative_path = os.path.join(str(request_id), stored_filename)

        if self._bucket:
            return self._save_gcs(file_bytes, relative_path, stored_filename)
        return self._save_local(file_bytes, relative_path, stored_filename)

    def _save_local(self, file_bytes: bytes, relative_path: str,
                    stored_filename: str) -> tuple[str, str]:
        full_path = os.path.join(self._upload_root, relative_path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, 'wb') as f:
            f.write(file_bytes)
        return relative_path, stored_filename

    def _save_gcs(self, file_bytes: bytes, relative_path: str,
                  stored_filename: str) -> tuple[str, str]:
        blob_name = f'documents/{relative_path}'
        blob = self._bucket.blob(blob_name)
        blob.upload_from_string(file_bytes)
        return f'gcs:{blob_name}', stored_filename

    def get_full_path(self, relative_path: str) -> str:
        """Return absolute local path for serving. GCS paths return as-is."""
        if relative_path.startswith('gcs:'):
            return relative_path
        return os.path.join(self._upload_root, relative_path)

    def delete(self, relative_path: str) -> bool:
        """Delete stored file. Returns True if deleted, False if not found."""
        if relative_path.startswith('gcs:'):
            blob_name = relative_path[4:]
            try:
                self._bucket.blob(blob_name).delete()
                return True
            except Exception:
                return False
        full_path = os.path.join(self._upload_root, relative_path)
        if os.path.exists(full_path):
            os.remove(full_path)
            return True
        return False


document_storage = DocumentStorage()
```

- [ ] **Step 2: Register in create_app**

In `app/__init__.py`, after `db.init_app(app)`:
```python
from app.services.storage import document_storage
document_storage.init_app(app)
```

- [ ] **Step 3: Write storage tests**

Create `tests/test_document_storage.py`:

```python
import os
import pytest
from app.services.storage import DocumentStorage


@pytest.fixture
def storage(tmp_path, app):
    s = DocumentStorage(app)
    # Override upload root to tmp_path for testing
    s._upload_root_override = str(tmp_path)
    return s


def test_save_returns_path_and_filename(app, tmp_path):
    s = DocumentStorage()
    s._app = app
    # Monkey-patch upload root
    original = s._upload_root
    import unittest.mock as mock
    with mock.patch.object(type(s), '_upload_root', new_callable=lambda: property(lambda self: str(tmp_path))):
        path, name = s.save(b'PDF content', request_id=42, doc_type='voucher', original_filename='test.pdf')
        assert '42' in path
        assert name.endswith('.pdf')
        assert 'voucher' in name


def test_save_creates_file_on_disk(app, tmp_path):
    s = DocumentStorage()
    s._app = app
    import unittest.mock as mock
    with mock.patch.object(type(s), '_upload_root', new_callable=lambda: property(lambda self: str(tmp_path))):
        path, _ = s.save(b'test data', request_id=1, doc_type='invoice', original_filename='inv.pdf')
        full = s.get_full_path(path)
        assert os.path.exists(full)
        assert open(full, 'rb').read() == b'test data'


def test_delete_removes_file(app, tmp_path):
    s = DocumentStorage()
    s._app = app
    import unittest.mock as mock
    with mock.patch.object(type(s), '_upload_root', new_callable=lambda: property(lambda self: str(tmp_path))):
        path, _ = s.save(b'to delete', request_id=99, doc_type='proforma', original_filename='p.pdf')
        full = s.get_full_path(path)
        assert os.path.exists(full)
        result = s.delete(path)
        assert result is True
        assert not os.path.exists(full)
```

- [ ] **Step 4: Run tests**

```bash
.venv/Scripts/python.exe -m pytest tests/test_document_storage.py -v
```
Expected: 3 tests pass.

- [ ] **Step 5: Commit**

```bash
git add app/services/storage.py app/__init__.py tests/test_document_storage.py
git commit -m "feat: add DocumentStorage service (local+GCS) for voucher/invoice files"
```

---

### Task 5: Record generated documents in inbound_document table

**Files:**
- Modify: `app/routes/inbound.py` (voucher generation routes)

The goal: whenever a voucher or invoice is generated and served, also record it in `inbound_document` so there's an audit trail.

- [ ] **Step 1: Find voucher generation routes in inbound.py**

```bash
grep -n "hotel_voucher\|restaurant_voucher\|voucher\|invoice" app/routes/inbound.py | grep "def " | head -20
```

Note the function names and line numbers.

- [ ] **Step 2: Add document recording helper**

At the top of `app/routes/inbound.py`, add import:
```python
from app.services.storage import document_storage
```

Add this helper function before the voucher routes:

```python
def _record_document(request_id: int, doc_type: str, filename: str,
                     filepath: str, file_bytes: bytes, user_id: int = 1) -> None:
    """Record a generated document in inbound_document table."""
    try:
        from app.models.inbound import InboundDocument
        doc = InboundDocument(
            request_id=request_id,
            document_type=doc_type,
            filename=filename,
            original_filename=filename,
            filepath=filepath,
            file_size=len(file_bytes),
            mime_type='application/pdf',
            uploaded_by=user_id,
        )
        db.session.add(doc)
        db.session.commit()
    except Exception as e:
        current_app.logger.warning(f'Document record failed (non-fatal): {e}')
```

- [ ] **Step 3: Wire into hotel voucher route**

Find the route that generates hotel voucher HTML/PDF. After generating the bytes, call:
```python
rel_path, stored_name = document_storage.save(
    pdf_bytes, request_id=req.id, doc_type='HOTEL_VOUCHER',
    original_filename=f'hotel_voucher_{req.request_number}.pdf'
)
_record_document(req.id, 'HOTEL_VOUCHER', stored_name, rel_path, pdf_bytes)
```

Apply the same pattern to restaurant voucher and invoice generation routes.

- [ ] **Step 4: Commit**

```bash
git add app/routes/inbound.py
git commit -m "feat: record generated vouchers/invoices in inbound_document table"
```

---

## Plan Complete

After all 5 tasks:
- Central status enums replace scattered string literals
- GuideExpenseSheet + GuidePaymentSheet models replace JSON blobs (additive, not destructive)
- InboundInvoiceLine model replaces invoice JSON blobs (additive)
- DocumentStorage service handles local/GCS file storage
- All generated documents recorded in inbound_document with metadata
- 8 new tests passing

**Next plan:** `2026-06-28-p3-file-structure.md` — enterprise file structure cleanup.
