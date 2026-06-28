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
