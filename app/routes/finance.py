import os
import sys
import csv
from datetime import datetime, date, timedelta
from dateutil.relativedelta import relativedelta
from io import StringIO
from calendar import monthrange
from sqlalchemy import extract, func, case, and_, or_
from werkzeug.utils import secure_filename
from flask import (
    Blueprint, render_template, request, redirect, url_for,
    flash, jsonify, current_app, send_file, Response
)
from flask_login import login_required, current_user

from app.extensions import db
from app.models import (
    ExpenseCategory, Expense, ExpenseAttachment, FinancialMetric, 
    ServiceItem, Payment, User, Document,
    EXPENSE_CATEGORY_RENT, EXPENSE_CATEGORY_UTILITIES
)
from app.models.booking import Booking
from app.models.supplier import SupplierPayment, Supplier, SupplierPrepaymentLine, SupplierService
from app.forms.expense import (
    ExpenseCategoryForm, ExpenseForm, ExpenseFilterForm,
    ExpenseAttachmentForm, FinancialReportFilterForm
)
from app.utils import is_valid_phone, PHONE_ERROR

finance = Blueprint('finance', __name__, url_prefix='/finance')

def safe_log_error(message, error=None):
    """Safely log errors to avoid Windows encoding issues with sys.stderr"""
    try:
        from flask import has_request_context, current_app
        if has_request_context():
            if error:
                error_str = str(error).encode('ascii', 'replace').decode('ascii')
                current_app.logger.error(f"{message}: {error_str}")
            else:
                msg_str = str(message).encode('ascii', 'replace').decode('ascii')
                current_app.logger.error(msg_str)
    except:
        pass  # If logging fails, continue silently

def validate_date_for_query(date_value, default=None, param_name="date"):
    """Validate and normalize date for SQL queries
    
    Ensures date_value is a date object (not datetime or string) before using in queries.
    This prevents OSError: [Errno 22] Invalid argument on Windows when date types mismatch.
    
    Args:
        date_value: The date value to validate (can be date, datetime, or None)
        default: Default date to return if validation fails (defaults to today)
        param_name: Name of parameter for logging purposes
    
    Returns:
        date: Validated date object
    """
    if date_value is None:
        safe_log_error(f"{param_name} is None, using default", None)
        return default or date.today()
    
    if isinstance(date_value, datetime):
        return date_value.date()
    elif isinstance(date_value, date):
        return date_value
    else:
        safe_log_error(f"{param_name} is invalid type: {type(date_value)}, value: {date_value}", None)
        return default or date.today()

@finance.route('/')
@login_required
def index():
    """Finance module home with financial KPIs"""
    return dashboard()

@finance.route('/dashboard')
@login_required
def dashboard():
    """Finance dashboard with financial KPIs"""
    # Authentication disabled - all users have access
    # Get selected month from query parameter or default to current
    today = date.today()
    selected_month = request.args.get('month', 'current')

    # Determine date range based on selected month
    # Use defensive date calculations to prevent OSError on Windows
    try:
        if selected_month == 'current':
            first_day = validate_date_for_query(
                date(today.year, today.month, 1),
                default=date.today().replace(day=1),
                param_name="first_day (current)"
            )
            try:
                last_day = validate_date_for_query(
                    date(today.year, today.month, monthrange(today.year, today.month)[1]),
                    default=date.today(),
                    param_name="last_day (current)"
                )
            except (OSError, ValueError, TypeError) as e:
                safe_log_error("Error calculating last_day for current month", e)
                last_day = date.today()
        elif selected_month == 'all':
            # All time data - use a wide range
            first_day = date(2020, 1, 1)  # Far in the past
            last_day = today
        else:
            # Handle relative months (-1, -2, -3)
            try:
                months_offset = int(selected_month)
                target_date = today + relativedelta(months=months_offset)
                first_day = validate_date_for_query(
                    date(target_date.year, target_date.month, 1),
                    default=date.today().replace(day=1),
                    param_name=f"first_day (month {months_offset})"
                )
                try:
                    last_day = validate_date_for_query(
                        date(target_date.year, target_date.month, monthrange(target_date.year, target_date.month)[1]),
                        default=date.today(),
                        param_name=f"last_day (month {months_offset})"
                    )
                except (OSError, ValueError, TypeError) as e:
                    safe_log_error(f"Error calculating last_day for month {months_offset}", e)
                    last_day = date.today()
            except (ValueError, TypeError, OSError) as e:
                safe_log_error("Error parsing selected_month or calculating dates", e)
                # Default to current month if invalid value
                first_day = date.today().replace(day=1)
                last_day = date.today()
    except Exception as e:
        safe_log_error("Error in date range calculation", e)
        first_day = date.today().replace(day=1)
        last_day = date.today()

    # Get previous period for comparison (always one month before the selected period)
    try:
        prev_month = first_day - timedelta(days=1)
        prev_first = validate_date_for_query(
            date(prev_month.year, prev_month.month, 1),
            default=date.today().replace(day=1),
            param_name="prev_first"
        )
        try:
            prev_last = validate_date_for_query(
                date(prev_month.year, prev_month.month, monthrange(prev_month.year, prev_month.month)[1]),
                default=date.today(),
                param_name="prev_last"
            )
        except (OSError, ValueError, TypeError) as e:
            safe_log_error("Error calculating prev_last", e)
            prev_last = date.today()
    except Exception as e:
        safe_log_error("Error calculating previous period dates", e)
        prev_first = date.today().replace(day=1)
        prev_last = date.today()

    # Calculate KPIs
    # 1. Revenue - based on invoiced bookings (single source of truth: booking table)

    # Current month invoiced revenue from booking table
    current_month_invoices = db.session.query(func.sum(Booking.total_amount)).filter(
        Booking.invoice_date >= first_day,
        Booking.invoice_date <= last_day,
        Booking.invoice_number.isnot(None)  # Only invoiced bookings
    ).scalar() or 0

    # Credit memos are stored separately in the invoice table
    from app.models.invoice import Invoice
    current_month_credits = db.session.query(func.sum(Invoice.total_amount)).filter(
        Invoice.invoice_date >= first_day,
        Invoice.invoice_date <= last_day,
        Invoice.is_credit_memo == True
    ).scalar() or 0

    current_month_revenue = current_month_invoices - abs(current_month_credits)

    # Previous month invoiced revenue
    prev_month_invoices = db.session.query(func.sum(Invoice.total_amount)).filter(
        Invoice.invoice_date >= prev_first,
        Invoice.invoice_date <= prev_last,
        Invoice.is_credit_memo == False
    ).scalar() or 0

    # Previous month credit memos
    prev_month_credits = db.session.query(func.sum(Invoice.total_amount)).filter(
        Invoice.invoice_date >= prev_first,
        Invoice.invoice_date <= prev_last,
        Invoice.is_credit_memo == True
    ).scalar() or 0

    prev_month_revenue = prev_month_invoices - abs(prev_month_credits)

    # 2. Expenses - with error handling to prevent SSL connection issues
    try:
        current_month_expenses = db.session.query(func.sum(Expense.amount)).filter(
            Expense.date_incurred >= first_day,
            Expense.date_incurred <= last_day
        ).scalar() or 0
    except Exception as e:
        # Import current_app for logging
        from flask import current_app
        current_app.logger.error(f"Error fetching current month expenses: {str(e)}")
        current_month_expenses = 0

    try:
        prev_month_expenses = db.session.query(func.sum(Expense.amount)).filter(
            Expense.date_incurred >= prev_first,
            Expense.date_incurred <= prev_last
        ).scalar() or 0
    except Exception as e:
        from flask import current_app
        current_app.logger.error(f"Error fetching previous month expenses: {str(e)}")
        prev_month_expenses = 0

    # 3. Supplier Costs - with error handling for schema mismatches and date validation
    # Validate dates before using in queries
    first_day_valid = validate_date_for_query(first_day, default=date.today().replace(day=1), param_name="first_day")
    last_day_valid = validate_date_for_query(last_day, default=date.today(), param_name="last_day")
    prev_first_valid = validate_date_for_query(prev_first, default=date.today().replace(day=1), param_name="prev_first")
    prev_last_valid = validate_date_for_query(prev_last, default=date.today(), param_name="prev_last")
    
    try:
        current_month_supplier_costs = db.session.query(func.sum(SupplierPayment.amount)).filter(
            SupplierPayment.payment_date.isnot(None),
            SupplierPayment.payment_date >= first_day_valid,
            SupplierPayment.payment_date <= last_day_valid
        ).scalar() or 0

        # Count of supplier payments for the current month
        supplier_payments_count = db.session.query(func.count(SupplierPayment.id)).filter(
            SupplierPayment.payment_date.isnot(None),
            SupplierPayment.payment_date >= first_day_valid,
            SupplierPayment.payment_date <= last_day_valid
        ).scalar() or 0

        prev_month_supplier_costs = db.session.query(func.sum(SupplierPayment.amount)).filter(
            SupplierPayment.payment_date.isnot(None),
            SupplierPayment.payment_date >= prev_first_valid,
            SupplierPayment.payment_date <= prev_last_valid
        ).scalar() or 0
    except OSError as os_err:
        safe_log_error("OSError querying supplier payments", os_err)
        current_month_supplier_costs = 0
        supplier_payments_count = 0
        prev_month_supplier_costs = 0
    except Exception as e:
        safe_log_error("Error querying supplier payments", e)
        current_month_supplier_costs = 0
        supplier_payments_count = 0
        prev_month_supplier_costs = 0

    # 4. Cash Flow - Customer payments received minus supplier payments processed
    current_month_customer_payments = db.session.query(func.sum(Payment.amount)).filter(
        Payment.payment_date >= first_day,
        Payment.payment_date <= last_day
    ).scalar() or 0

    prev_month_customer_payments = db.session.query(func.sum(Payment.amount)).filter(
        Payment.payment_date >= prev_first,
        Payment.payment_date <= prev_last
    ).scalar() or 0

    current_month_cash_flow = current_month_customer_payments - current_month_supplier_costs
    prev_month_cash_flow = prev_month_customer_payments - prev_month_supplier_costs

    # 5. Profit calculation
    current_month_profit = current_month_revenue - current_month_expenses - current_month_supplier_costs
    prev_month_profit = prev_month_revenue - prev_month_expenses - prev_month_supplier_costs

    # Calculate percentage changes
    revenue_change_pct = ((current_month_revenue / prev_month_revenue) - 1) * 100 if prev_month_revenue > 0 else 0
    expenses_change_pct = ((current_month_expenses / prev_month_expenses) - 1) * 100 if prev_month_expenses > 0 else 0
    cash_flow_change_pct = ((current_month_cash_flow / prev_month_cash_flow) - 1) * 100 if prev_month_cash_flow != 0 else 0
    profit_change_pct = ((current_month_profit / prev_month_profit) - 1) * 100 if prev_month_profit > 0 else 0

    # Get expense breakdown by category for current month
    expense_by_category = db.session.query(
        ExpenseCategory.name, 
        func.sum(Expense.amount).label('total')
    ).join(
        Expense, Expense.category_id == ExpenseCategory.id
    ).filter(
        Expense.date_incurred >= first_day,
        Expense.date_incurred <= last_day
    ).group_by(
        ExpenseCategory.name
    ).all()

    # Get monthly data for last 12 months for trend chart

    # Get revenue bookings for the selected period with additional filters
    # Booking already imported at top of file
    from datetime import datetime

    # Base query
    booking_query = Booking.query.filter(Booking.total_amount > 0)

    # Apply date range filters from the main date selector
    booking_query = booking_query.filter(
        Booking.created_at >= first_day,
        Booking.created_at <= last_day
    )

    # Apply reference number filter if provided
    if request.args.get('booking_reference'):
        ref_filter = request.args.get('booking_reference')
        booking_query = booking_query.filter(Booking.reference_number.ilike(f'%{ref_filter}%'))

    # Apply custom date range filters if provided
    if request.args.get('date_from'):
        try:
            date_from = datetime.strptime(request.args.get('date_from'), '%Y-%m-%d').date()
            booking_query = booking_query.filter(Booking.created_at >= date_from)
        except (ValueError, TypeError):
            pass  # Invalid date format, ignore filter

    if request.args.get('date_to'):
        try:
            date_to = datetime.strptime(request.args.get('date_to'), '%Y-%m-%d').date()
            booking_query = booking_query.filter(Booking.created_at <= date_to)
        except (ValueError, TypeError):
            pass  # Invalid date format, ignore filter

    # Get the filtered results - with robust ordering
    try:
        revenue_bookings = booking_query.order_by(
            func.coalesce(Booking.total_amount, 0).desc(),
            Booking.id.desc()
        ).all()
    except (OSError, Exception) as e:
        safe_log_error("Error ordering revenue bookings", e)
        try:
            # Fallback: order by ID only
            revenue_bookings = booking_query.order_by(Booking.id.desc()).all()
        except:
            revenue_bookings = []
    last_12_months = []
    for i in range(11, -1, -1):
        # Calculate month dates with validation and error handling
        try:
            month_date = date.today() - relativedelta(months=i)
            month_first = validate_date_for_query(
                date(month_date.year, month_date.month, 1),
                default=date.today().replace(day=1),
                param_name=f"month_first for month {i}"
            )
            month_last = validate_date_for_query(
                date(month_date.year, month_date.month, monthrange(month_date.year, month_date.month)[1]),
                default=date.today(),
                param_name=f"month_last for month {i}"
            )
        except Exception as calc_err:
            safe_log_error(f"Error calculating dates for month {i}", calc_err)
            month_first = date.today().replace(day=1)
            month_last = date.today()
            month_date = date.today()

        month_revenue = db.session.query(func.sum(Payment.amount)).filter(
            Payment.payment_date >= month_first,
            Payment.payment_date <= month_last
        ).scalar() or 0

        month_expenses = db.session.query(func.sum(Expense.amount)).filter(
            Expense.date_incurred >= month_first,
            Expense.date_incurred <= month_last
        ).scalar() or 0

        # Defensive query with NULL check and OSError handling
        try:
            month_supplier_costs = db.session.query(func.sum(SupplierPayment.amount)).filter(
                SupplierPayment.payment_date.isnot(None),
                SupplierPayment.payment_date >= month_first,
                SupplierPayment.payment_date <= month_last
            ).scalar() or 0
        except OSError as os_err:
            safe_log_error(f"OSError querying supplier costs for month {month_date} (first={month_first}, last={month_last})", os_err)
            month_supplier_costs = 0
        except Exception as e:
            safe_log_error(f"Error querying supplier costs for month {month_date}", e)
            month_supplier_costs = 0

        month_profit = month_revenue - month_expenses - month_supplier_costs

        last_12_months.append({
            'month': month_date.strftime('%b %Y'),
            'revenue': month_revenue,
            'expenses': month_expenses + month_supplier_costs,
            'profit': month_profit
        })

    # Get recent expenses - with robust ordering to handle NULL dates
    try:
        recent_expenses = db.session.query(Expense).order_by(
            func.coalesce(Expense.date_incurred, date(1970, 1, 1)).desc(),
            Expense.id.desc()
        ).limit(5).all()
    except (OSError, Exception) as e:
        safe_log_error("Error loading recent expenses", e)
        try:
            # Fallback: order by ID only
            recent_expenses = db.session.query(Expense).order_by(Expense.id.desc()).limit(5).all()
        except:
            recent_expenses = []

    # Get recent supplier payments - with robust ordering to handle NULL dates
    # Validate date calculation
    thirty_days_ago = validate_date_for_query(
        today - timedelta(days=30),
        default=date.today() - timedelta(days=30),
        param_name="thirty_days_ago"
    )
    try:
        upcoming_payments = db.session.query(SupplierPayment).filter(
            SupplierPayment.payment_date.isnot(None),
            SupplierPayment.payment_date >= thirty_days_ago
        ).order_by(
            func.coalesce(SupplierPayment.payment_date, date(1970, 1, 1)).desc(),
            SupplierPayment.id.desc()
        ).limit(5).all()
    except OSError as os_err:
        safe_log_error("OSError loading recent supplier payments", os_err)
        try:
            # Fallback: order by ID only
            upcoming_payments = db.session.query(SupplierPayment).filter(
                SupplierPayment.payment_date.isnot(None),
                SupplierPayment.payment_date >= thirty_days_ago
            ).order_by(SupplierPayment.id.desc()).limit(5).all()
        except:
            upcoming_payments = []
    except Exception as e:
        safe_log_error("Error loading recent supplier payments", e)
        try:
            # Fallback: order by ID only
            upcoming_payments = db.session.query(SupplierPayment).filter(
                SupplierPayment.payment_date.isnot(None),
                SupplierPayment.payment_date >= thirty_days_ago
            ).order_by(SupplierPayment.id.desc()).limit(5).all()
        except:
            upcoming_payments = []

    # Get supplier payments for the selected period for the breakdown modal
    from app.models.service import ServiceConfirmation
    from app.models.supplier import Supplier, SupplierPrepaymentLine
    # Booking already imported at top of file

    # Use joinedload to preload all related data in a single query
    # We need to use class-bound attributes instead of strings for SQLAlchemy relationships
    from app.models.service import ServiceItem

    # SQLAlchemy in newer versions doesn't accept string relationship names
    # Use defensive query to handle missing columns and NULL dates
    # Use validated dates from earlier calculations
    try:
        supplier_payments = db.session.query(SupplierPayment).options(
            # Use basic queries without joinedloads to avoid errors
            db.joinedload(SupplierPayment.prepayment_lines),
            db.joinedload(SupplierPayment.service_confirmation)
        ).filter(
            SupplierPayment.payment_date.isnot(None),
            SupplierPayment.payment_date >= first_day_valid,
            SupplierPayment.payment_date <= last_day_valid
        ).order_by(
            func.coalesce(SupplierPayment.payment_date, date(1970, 1, 1)).desc(),
            SupplierPayment.id.desc()
        ).all()
    except OSError as os_err:
        # If there's a schema mismatch (missing columns) or encoding issue, use a simpler query
        safe_log_error("OSError loading supplier payments with relationships", os_err)
        # Try querying without relationships first, with robust ordering
        try:
            supplier_payments = db.session.query(SupplierPayment).filter(
                SupplierPayment.payment_date.isnot(None),
                SupplierPayment.payment_date >= first_day_valid,
                SupplierPayment.payment_date <= last_day_valid
            ).order_by(
                func.coalesce(SupplierPayment.payment_date, date(1970, 1, 1)).desc(),
                SupplierPayment.id.desc()
            ).all()
        except OSError as os_err2:
            safe_log_error("OSError loading supplier payments (fallback 1)", os_err2)
            # If ordering by date fails, try ordering by ID only
            try:
                supplier_payments = db.session.query(SupplierPayment).filter(
                    SupplierPayment.payment_date.isnot(None),
                    SupplierPayment.payment_date >= first_day_valid,
                    SupplierPayment.payment_date <= last_day_valid
                ).order_by(SupplierPayment.id.desc()).all()
            except Exception as e3:
                # If even basic query fails, return empty list
                safe_log_error("Error with basic supplier payment query", e3)
                supplier_payments = []
        except Exception as e2:
            safe_log_error("Error loading supplier payments (fallback 1)", e2)
            try:
                supplier_payments = db.session.query(SupplierPayment).filter(
                    SupplierPayment.payment_date.isnot(None),
                    SupplierPayment.payment_date >= first_day_valid,
                    SupplierPayment.payment_date <= last_day_valid
                ).order_by(SupplierPayment.id.desc()).all()
            except Exception as e3:
                safe_log_error("Error with basic supplier payment query", e3)
                supplier_payments = []
    except Exception as e:
        # If there's a schema mismatch (missing columns) or encoding issue, use a simpler query
        safe_log_error("Error loading supplier payments with relationships", e)
        # Try querying without relationships first, with robust ordering
        try:
            supplier_payments = db.session.query(SupplierPayment).filter(
                SupplierPayment.payment_date.isnot(None),
                SupplierPayment.payment_date >= first_day_valid,
                SupplierPayment.payment_date <= last_day_valid
            ).order_by(
                func.coalesce(SupplierPayment.payment_date, date(1970, 1, 1)).desc(),
                SupplierPayment.id.desc()
            ).all()
        except OSError as os_err2:
            safe_log_error("OSError loading supplier payments (fallback 1)", os_err2)
            try:
                supplier_payments = db.session.query(SupplierPayment).filter(
                    SupplierPayment.payment_date.isnot(None),
                    SupplierPayment.payment_date >= first_day_valid,
                    SupplierPayment.payment_date <= last_day_valid
                ).order_by(SupplierPayment.id.desc()).all()
            except Exception as e3:
                safe_log_error("Error with basic supplier payment query", e3)
                supplier_payments = []
        except Exception as e2:
            safe_log_error("Error with supplier payment query ordering", e2)
            try:
                supplier_payments = db.session.query(SupplierPayment).filter(
                    SupplierPayment.payment_date.isnot(None),
                    SupplierPayment.payment_date >= first_day_valid,
                    SupplierPayment.payment_date <= last_day_valid
                ).order_by(SupplierPayment.id.desc()).all()
            except Exception as e3:
                # If even basic query fails, return empty list
                safe_log_error("Error with basic supplier payment query", e3)
                supplier_payments = []

    # Debug output to verify prepayment lines are loaded
    # Debug logging (commented out to avoid Windows encoding issues)
    # current_app.logger.debug(f"Loaded {len(supplier_payments)} supplier payments for breakdown")
    for payment in supplier_payments:
        prepayment_count = len(payment.prepayment_lines) if payment.prepayment_lines else 0
        # current_app.logger.debug(f"Payment ID {payment.id}: {prepayment_count} prepayment lines")

        # Get booking references for each prepayment line
        if payment.prepayment_lines:
            for line in payment.prepayment_lines:
                # Get booking reference using the booking_id directly
                # Booking already imported at top of file
                booking = Booking.query.get(line.booking_id)
                # if booking:
                #     current_app.logger.debug(f"  → Booking reference: {booking.reference_number}")
                # else:
                #     current_app.logger.debug(f"  → No booking found for line {line.id}")

        # Also verify service confirmation path for backwards compatibility
        # if payment.service_confirmation and payment.service_confirmation.service_item and payment.service_confirmation.service_item.booking:
        #     current_app.logger.debug(f"  → Service confirmation booking reference: {payment.service_confirmation.service_item.booking.reference_number}")

    # Get display name for the selected period
    if selected_month == 'current':
        period_display = today.strftime('%B %Y')
    elif selected_month == 'all':
        period_display = 'All Time'
    else:
        try:
            months_offset = int(selected_month)
            target_date = today + relativedelta(months=months_offset)
            period_display = target_date.strftime('%B %Y')
        except (ValueError, TypeError):
            period_display = today.strftime('%B %Y')

    return render_template(
        'finance/index.html',
        today=today,
        current_month=period_display,
        prev_month=prev_month.strftime('%B %Y'),
        current_month_revenue=current_month_revenue,
        prev_month_revenue=prev_month_revenue,
        revenue_change_pct=revenue_change_pct,
        current_month_expenses=current_month_expenses,
        prev_month_expenses=prev_month_expenses,
        expenses_change_pct=expenses_change_pct,
        current_month_supplier_costs=current_month_supplier_costs,
        prev_month_supplier_costs=prev_month_supplier_costs,
        supplier_payments_count=supplier_payments_count,
        current_month_cash_flow=current_month_cash_flow,
        prev_month_cash_flow=prev_month_cash_flow,
        cash_flow_change_pct=cash_flow_change_pct,
        current_month_profit=current_month_profit,
        prev_month_profit=prev_month_profit,
        profit_change_pct=profit_change_pct,
        expense_by_category=expense_by_category,
        last_12_months=last_12_months,
        recent_expenses=recent_expenses,
        upcoming_payments=upcoming_payments,
        supplier_payments=supplier_payments,
        selected_month=selected_month,
        revenue_bookings=revenue_bookings
    )

@finance.route('/expenses')
@login_required
def expenses():
    """List and manage expenses"""
    filter_form = ExpenseFilterForm()

    # Populate category dropdown
    categories = ExpenseCategory.query.filter_by(is_active=True).all()
    filter_form.category_id.choices = [(0, 'All Categories')] + [(c.id, c.name) for c in categories]

    # Apply filters if submitted
    query = Expense.query

    if request.args.get('date_from'):
        date_from = datetime.strptime(request.args.get('date_from'), '%Y-%m-%d').date()
        query = query.filter(Expense.date_incurred >= date_from)
        filter_form.date_from.data = date_from

    if request.args.get('date_to'):
        date_to = datetime.strptime(request.args.get('date_to'), '%Y-%m-%d').date()
        query = query.filter(Expense.date_incurred <= date_to)
        filter_form.date_to.data = date_to

    if request.args.get('category_id') and int(request.args.get('category_id')) > 0:
        category_id = int(request.args.get('category_id'))
        query = query.filter(Expense.category_id == category_id)
        filter_form.category_id.data = category_id

    if request.args.get('payment_status'):
        status = request.args.get('payment_status')
        if status == 'paid':
            query = query.filter(Expense.is_paid == True)
        elif status == 'unpaid':
            query = query.filter(Expense.is_paid == False)
        filter_form.payment_status.data = status

    if request.args.get('vendor_name'):
        vendor_name = request.args.get('vendor_name')
        query = query.filter(Expense.vendor_name.like(f'%{vendor_name}%'))
        filter_form.vendor_name.data = vendor_name

    if request.args.get('min_amount'):
        min_amount = float(request.args.get('min_amount'))
        query = query.filter(Expense.amount >= min_amount)
        filter_form.min_amount.data = min_amount

    if request.args.get('max_amount'):
        max_amount = float(request.args.get('max_amount'))
        query = query.filter(Expense.amount <= max_amount)
        filter_form.max_amount.data = max_amount

    # Order expenses by date (most recent first) - with robust ordering to handle NULL dates
    try:
        expenses = query.order_by(
            func.coalesce(Expense.date_incurred, date(1970, 1, 1)).desc(),
            Expense.id.desc()
        ).all()
    except (OSError, Exception) as e:
        safe_log_error("Error ordering expenses", e)
        try:
            # Fallback: order by ID only
            expenses = query.order_by(Expense.id.desc()).all()
        except:
            expenses = []

    # Calculate totals
    total_amount = sum(expense.amount for expense in expenses)
    paid_amount = sum(expense.amount for expense in expenses if expense.is_paid)
    unpaid_amount = total_amount - paid_amount

    # Handle export if requested
    if request.args.get('export'):
        return export_expenses_csv(expenses)

    return render_template(
        'finance/expenses.html',
        expenses=expenses,
        filter_form=filter_form,
        total_amount=total_amount,
        paid_amount=paid_amount, 
        unpaid_amount=unpaid_amount
    )

@finance.route('/cash-flow')
@login_required
def cash_flow():
    """Cash flow dashboard showing payments in and out"""
    try:
        # Get payments received from customers - with robust ordering to handle NULL dates
        try:
            payments_in = db.session.query(
                Payment.payment_date,
                Payment.amount,
                Payment.payment_method,
                Booking.reference_number,
                Payment.notes
            ).join(Booking).order_by(
                func.coalesce(Payment.payment_date, date(1970, 1, 1)).desc(),
                Payment.id.desc()
            ).limit(50).all()
        except (OSError, Exception) as e:
            safe_log_error("Error ordering customer payments", e)
            try:
                # Fallback: order by ID only
                payments_in = db.session.query(
                    Payment.payment_date,
                    Payment.amount,
                    Payment.payment_method,
                    Booking.reference_number,
                    Payment.notes
                ).join(Booking).order_by(Payment.id.desc()).limit(50).all()
            except:
                payments_in = []

        # Get payments made to suppliers (only actually paid ones)
        # Use defensive query to handle missing columns and NULL dates
        try:
            payments_out = db.session.query(
                SupplierPayment.payment_date,
                SupplierPayment.amount,
                SupplierPayment.payment_method,
                Supplier.name.label('supplier_name'),
                SupplierPayment.notes
            ).join(Supplier).filter(
                SupplierPayment.status == 'PAID',
                SupplierPayment.payment_date.isnot(None)
            ).order_by(
                func.coalesce(SupplierPayment.payment_date, date(1970, 1, 1)).desc(),
                SupplierPayment.id.desc()
            ).limit(50).all()
        except OSError as os_err:
            safe_log_error("OSError loading supplier payments for cash flow", os_err)
            try:
                # Fallback: order by ID only
                payments_out = db.session.query(
                    SupplierPayment.payment_date,
                    SupplierPayment.amount,
                    SupplierPayment.payment_method,
                    Supplier.name.label('supplier_name'),
                    SupplierPayment.notes
                ).join(Supplier).filter(
                    SupplierPayment.status == 'PAID',
                    SupplierPayment.payment_date.isnot(None)
                ).order_by(SupplierPayment.id.desc()).limit(50).all()
            except:
                payments_out = []
        except Exception as e:
            safe_log_error("Error loading supplier payments for cash flow", e)
            try:
                # Fallback: order by ID only
                payments_out = db.session.query(
                    SupplierPayment.payment_date,
                    SupplierPayment.amount,
                    SupplierPayment.payment_method,
                    Supplier.name.label('supplier_name'),
                    SupplierPayment.notes
                ).join(Supplier).filter(
                    SupplierPayment.status == 'PAID',
                    SupplierPayment.payment_date.isnot(None)
                ).order_by(SupplierPayment.id.desc()).limit(50).all()
            except:
                payments_out = []

        # Calculate totals for current month
        # Validate dates before using in queries
        try:
            current_month_start = validate_date_for_query(
                date.today().replace(day=1),
                default=date.today().replace(day=1),
                param_name="current_month_start"
            )
            next_month = validate_date_for_query(
                current_month_start + relativedelta(months=1),
                default=date.today(),
                param_name="next_month"
            )
        except Exception as calc_err:
            safe_log_error("Error calculating current month dates in cash_flow", calc_err)
            current_month_start = date.today().replace(day=1)
            next_month = date.today()

        total_in = db.session.query(func.sum(Payment.amount)).filter(
            Payment.payment_date >= current_month_start,
            Payment.payment_date < next_month
        ).scalar() or 0

        # Defensive query with NULL check and OSError handling
        try:
            total_out = db.session.query(func.sum(SupplierPayment.amount)).filter(
                SupplierPayment.payment_date.isnot(None),
                SupplierPayment.payment_date >= current_month_start,
                SupplierPayment.payment_date < next_month,
                SupplierPayment.status == 'PAID'
            ).scalar() or 0
        except OSError as os_err:
            safe_log_error("OSError calculating total supplier payments for current month", os_err)
            total_out = 0
        except Exception as e:
            safe_log_error("Error calculating total supplier payments for current month", e)
            total_out = 0
        except Exception as e:
            safe_log_error("Error calculating total supplier payments", e)
            total_out = 0

        net_cash_flow = total_in - total_out

        return render_template('finance/cash_flow.html',
            payments_in=payments_in,
            payments_out=payments_out,
            total_in=total_in,
            total_out=total_out,
            net_cash_flow=net_cash_flow,
            current_month=current_month_start.strftime('%B %Y')
        )
    except Exception as e:
        current_app.logger.error(f"Error loading cash flow: {str(e)}")
        flash('Error loading cash flow data.', 'error')
        return redirect(url_for('finance.index'))

@finance.route('/expenses/new', methods=['GET', 'POST'])
@login_required
def new_expense():
    """Create a new expense"""
    form = ExpenseForm()

    # Populate category dropdown
    categories = ExpenseCategory.query.filter_by(is_active=True).all()
    form.category_id.choices = [(c.id, c.name) for c in categories]

    if form.validate_on_submit():
        expense = Expense(
            title=form.title.data,
            description=form.description.data,
            amount=form.amount.data,
            category_id=form.category_id.data,
            date_incurred=form.date_incurred.data,
            payment_date=form.payment_date.data,
            payment_method=form.payment_method.data,
            reference_number=form.reference_number.data,
            vendor_name=form.vendor_name.data,
            is_paid=form.is_paid.data,
            is_recurring=form.is_recurring.data,
            recurrence_type=form.recurrence_type.data,
            recurrence_ends=form.recurrence_ends.data
        )

        db.session.add(expense)
        db.session.commit()

        flash('Expense created successfully.', 'success')
        return redirect(url_for('finance.expenses'))

    return render_template('finance/expense_form.html', form=form, expense=None)

@finance.route('/expenses/<int:expense_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_expense(expense_id):
    """Edit an existing expense"""
    expense = Expense.query.get_or_404(expense_id)
    form = ExpenseForm(obj=expense)

    # Populate category dropdown
    categories = ExpenseCategory.query.filter_by(is_active=True).all()
    form.category_id.choices = [(c.id, c.name) for c in categories]

    if form.validate_on_submit():
        form.populate_obj(expense)
        db.session.commit()

        flash('Expense updated successfully.', 'success')
        return redirect(url_for('finance.expenses'))

    return render_template('finance/expense_form.html', form=form, expense=expense)

@finance.route('/expenses/<int:expense_id>/delete', methods=['POST'])
@login_required
def delete_expense(expense_id):
    """Delete an expense"""
    expense = Expense.query.get_or_404(expense_id)

    db.session.delete(expense)
    db.session.commit()

    flash('Expense deleted successfully.', 'success')
    return redirect(url_for('finance.expenses'))

@finance.route('/expenses/<int:expense_id>/attachments/upload', methods=['POST'])
@login_required
def upload_attachment(expense_id):
    """Upload attachment for an expense"""
    expense = Expense.query.get_or_404(expense_id)
    form = ExpenseAttachmentForm()

    if form.validate_on_submit():
        file = form.file.data
        filename = file.filename

        # Create upload directory if it doesn't exist
        upload_dir = os.path.join(current_app.root_path, 'static', 'uploads', 'expenses', str(expense_id))
        os.makedirs(upload_dir, exist_ok=True)

        # Save the file
        file_path = os.path.join(upload_dir, filename)
        file.save(file_path)

        # Store relative path in database
        rel_path = os.path.join('uploads', 'expenses', str(expense_id), filename)

        attachment = ExpenseAttachment(
            expense_id=expense_id,
            file_name=filename,
            file_path=rel_path,
            file_type=file.content_type,
            file_size=os.path.getsize(file_path)
        )

        db.session.add(attachment)
        db.session.commit()

        flash('Attachment uploaded successfully.', 'success')

    return redirect(url_for('finance.edit_expense', expense_id=expense_id))

@finance.route('/categories')
@login_required
def expense_categories():
    """List and manage expense categories"""
    categories = ExpenseCategory.query.all()
    form = ExpenseCategoryForm()

    edit_category_id = request.args.get('edit_id', type=int)
    edit_category_obj = None
    if edit_category_id:
        edit_category_obj = ExpenseCategory.query.get(edit_category_id)

    return render_template(
        'finance/categories.html',
        categories=categories,
        form=form,
        edit_category=edit_category_obj
    )

@finance.route('/categories/new', methods=['GET', 'POST'])
@login_required
def new_category():
    """Create a new expense category"""
    form = ExpenseCategoryForm()

    if request.method == 'GET':
        return redirect(url_for('finance.expense_categories', open='new'))

    if form.validate_on_submit():
        category = ExpenseCategory(
            name=form.name.data,
            code=form.code.data,
            description=form.description.data,
            is_active=form.is_active.data
        )

        db.session.add(category)
        db.session.commit()

        flash('Category created successfully.', 'success')
        return redirect(url_for('finance.expense_categories'))

    categories = ExpenseCategory.query.all()
    return render_template(
        'finance/categories.html',
        categories=categories,
        form=form,
        edit_category=None,
        force_modal_open=True,
        modal_mode='create'
    )

@finance.route('/categories/<int:category_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_category(category_id):
    """Edit an existing expense category"""
    category = ExpenseCategory.query.get_or_404(category_id)

    if request.method == 'GET':
        return redirect(url_for('finance.expense_categories', edit_id=category.id))

    form = ExpenseCategoryForm(obj=category)

    if form.validate_on_submit():
        form.populate_obj(category)
        db.session.commit()

        flash('Category updated successfully.', 'success')
        return redirect(url_for('finance.expense_categories'))

    categories = ExpenseCategory.query.all()
    return render_template(
        'finance/categories.html',
        categories=categories,
        form=form,
        edit_category=category,
        force_modal_open=True,
        modal_mode='edit'
    )

@finance.route('/reports')
@login_required
def reports():
    """Financial reports landing page"""
    form = FinancialReportFilterForm()

    # Default to this month if no date range provided
    # Use defensive date calculations to prevent OSError on Windows
    try:
        today = date.today()
        first_day = validate_date_for_query(
            date(today.year, today.month, 1),
            default=date.today().replace(day=1),
            param_name="first_day (reports)"
        )
        try:
            last_day = validate_date_for_query(
                date(today.year, today.month, monthrange(today.year, today.month)[1]),
                default=date.today(),
                param_name="last_day (reports)"
            )
        except (OSError, ValueError, TypeError) as e:
            safe_log_error("Error calculating last_day in reports()", e)
            last_day = date.today()
    except Exception as e:
        safe_log_error("Error calculating dates in reports()", e)
        first_day = date.today().replace(day=1)
        last_day = date.today()

    form.date_from.data = first_day
    form.date_to.data = last_day

    return render_template('finance/reports.html', form=form)

@finance.route('/reports/generate', methods=['GET', 'POST'])
@login_required
def generate_report():
    """Generate financial reports based on filters"""
    form = FinancialReportFilterForm()

    if form.validate_on_submit() or request.method == 'GET':
        # Process date range
        today = date.today()

        # Use defensive date calculations to prevent OSError on Windows
        try:
            if request.method == 'GET' or form.date_range.data == 'this_month':
                start_date = validate_date_for_query(
                    date(today.year, today.month, 1),
                    default=date.today().replace(day=1),
                    param_name="start_date (this_month)"
                )
                try:
                    end_date = validate_date_for_query(
                        date(today.year, today.month, monthrange(today.year, today.month)[1]),
                        default=date.today(),
                        param_name="end_date (this_month)"
                    )
                except (OSError, ValueError, TypeError) as e:
                    safe_log_error("Error calculating end_date for this_month", e)
                    end_date = date.today()
            elif form.date_range.data == 'last_month':
                try:
                    last_month = today - relativedelta(months=1)
                    start_date = validate_date_for_query(
                        date(last_month.year, last_month.month, 1),
                        default=date.today().replace(day=1),
                        param_name="start_date (last_month)"
                    )
                    try:
                        end_date = validate_date_for_query(
                            date(last_month.year, last_month.month, monthrange(last_month.year, last_month.month)[1]),
                            default=date.today(),
                            param_name="end_date (last_month)"
                        )
                    except (OSError, ValueError, TypeError) as e:
                        safe_log_error("Error calculating end_date for last_month", e)
                        end_date = date.today()
                except Exception as e:
                    safe_log_error("Error calculating last_month dates", e)
                    start_date = date.today().replace(day=1)
                    end_date = date.today()
            elif form.date_range.data == 'this_quarter':
                try:
                    quarter = (today.month - 1) // 3 + 1
                    start_date = validate_date_for_query(
                        date(today.year, (quarter - 1) * 3 + 1, 1),
                        default=date.today().replace(day=1),
                        param_name="start_date (this_quarter)"
                    )
                    end_month = quarter * 3
                    try:
                        end_date = validate_date_for_query(
                            date(today.year, end_month, monthrange(today.year, end_month)[1]),
                            default=date.today(),
                            param_name="end_date (this_quarter)"
                        )
                    except (OSError, ValueError, TypeError) as e:
                        safe_log_error("Error calculating end_date for this_quarter", e)
                        end_date = date.today()
                except Exception as e:
                    safe_log_error("Error calculating this_quarter dates", e)
                    start_date = date.today().replace(day=1)
                    end_date = date.today()
            elif form.date_range.data == 'last_quarter':
                try:
                    last_quarter_end = today - relativedelta(months=((today.month - 1) % 3) + 1)
                    last_quarter_start = date(last_quarter_end.year, last_quarter_end.month - 2, 1)
                    start_date = validate_date_for_query(
                        last_quarter_start,
                        default=date.today().replace(day=1),
                        param_name="start_date (last_quarter)"
                    )
                    try:
                        end_date = validate_date_for_query(
                            date(last_quarter_end.year, last_quarter_end.month, monthrange(last_quarter_end.year, last_quarter_end.month)[1]),
                            default=date.today(),
                            param_name="end_date (last_quarter)"
                        )
                    except (OSError, ValueError, TypeError) as e:
                        safe_log_error("Error calculating end_date for last_quarter", e)
                        end_date = date.today()
                except Exception as e:
                    safe_log_error("Error calculating last_quarter dates", e)
                    start_date = date.today().replace(day=1)
                    end_date = date.today()
            elif form.date_range.data == 'this_year':
                start_date = date(today.year, 1, 1)
                end_date = date(today.year, 12, 31)
            elif form.date_range.data == 'last_year':
                start_date = date(today.year - 1, 1, 1)
                end_date = date(today.year - 1, 12, 31)
            elif form.date_range.data == 'custom':
                start_date = validate_date_for_query(
                    form.date_from.data,
                    default=date.today().replace(day=1),
                    param_name="start_date (custom)"
                )
                end_date = validate_date_for_query(
                    form.date_to.data,
                    default=date.today(),
                    param_name="end_date (custom)"
                )
            else:
                # Default to this month
                start_date = validate_date_for_query(
                    date(today.year, today.month, 1),
                    default=date.today().replace(day=1),
                    param_name="start_date (default)"
                )
                try:
                    end_date = validate_date_for_query(
                        date(today.year, today.month, monthrange(today.year, today.month)[1]),
                        default=date.today(),
                        param_name="end_date (default)"
                    )
                except (OSError, ValueError, TypeError) as e:
                    safe_log_error("Error calculating end_date (default)", e)
                    end_date = date.today()
        except Exception as e:
            safe_log_error("Error in date range calculation in generate_report()", e)
            start_date = date.today().replace(day=1)
            end_date = date.today()

        # Set form date fields
        form.date_from.data = start_date
        form.date_to.data = end_date

        # Generate the appropriate report
        report_type = request.args.get('report_type', form.report_type.data)

        if report_type == 'profit_loss':
            report_data = generate_profit_loss_report(start_date, end_date, form.group_by.data)
            template = 'finance/reports/profit_loss.html'
        elif report_type == 'expense_summary':
            report_data = generate_expense_summary_report(start_date, end_date, form.group_by.data, form.include_details.data)
            template = 'finance/reports/expense_summary.html'
        elif report_type == 'revenue_summary':
            report_data = generate_revenue_summary_report(start_date, end_date, form.group_by.data)
            template = 'finance/reports/revenue_summary.html'
        elif report_type == 'supplier_payments':
            report_data = generate_supplier_payments_report(start_date, end_date)
            template = 'finance/reports/supplier_payments.html'
        else:
            flash('Invalid report type specified.', 'error')
            return redirect(url_for('finance.reports'))

        # Check if export requested
        if form.export.data:
            if report_type == 'profit_loss':
                return export_profit_loss_csv(report_data, start_date, end_date)
            elif report_type == 'expense_summary':
                return export_expense_summary_csv(report_data, start_date, end_date)
            elif report_type == 'revenue_summary':
                return export_revenue_summary_csv(report_data, start_date, end_date)
            elif report_type == 'supplier_payments':
                return export_supplier_payments_csv(report_data, start_date, end_date)

        return render_template(
            template,
            form=form,
            report_data=report_data,
            start_date=start_date,
            end_date=end_date
        )

    return render_template('finance/reports.html', form=form)

# Helper functions for report generation
def generate_profit_loss_report(start_date, end_date, group_by='month'):
    """Generate profit and loss report data"""
    # TODO: Implement calculations for profit and loss report
    # This is a placeholder for the actual implementation

    # Sample data structure for the profit and loss report
    report_data = {
        'summary': {
            'total_revenue': 0.0,
            'total_expenses': 0.0,
            'total_supplier_costs': 0.0,
            'gross_profit': 0.0,
            'net_profit': 0.0
        },
        'periods': []  # Will contain period-by-period breakdown
    }

    return report_data

def generate_expense_summary_report(start_date, end_date, group_by='month', include_details=False):
    """Generate expense summary report data"""
    # TODO: Implement calculations for expense summary report
    # This is a placeholder for the actual implementation

    # Sample data structure for the expense summary report
    report_data = {
        'summary': {
            'total_expenses': 0.0,
            'by_category': []  # Will contain category breakdown
        },
        'periods': []  # Will contain period-by-period breakdown
    }

    return report_data

def generate_revenue_summary_report(start_date, end_date, group_by='month'):
    """Generate revenue summary report data"""
    # TODO: Implement calculations for revenue summary report
    # This is a placeholder for the actual implementation

    # Sample data structure for the revenue summary report
    report_data = {
        'summary': {
            'total_revenue': 0.0,
            'by_service_type': []  # Will contain service type breakdown
        },
        'periods': []  # Will contain period-by-period breakdown
    }

    return report_data

def generate_supplier_payments_report(start_date, end_date):
    """Generate supplier payments report data"""
    # TODO: Implement calculations for supplier payments report
    # This is a placeholder for the actual implementation

    # Sample data structure for the supplier payments report
    report_data = {
        'summary': {
            'total_payments': 0.0,
            'by_supplier': []  # Will contain supplier breakdown
        },
        'payments': []  # Will contain list of payments
    }

    return report_data

# Helper functions for CSV exports
def export_expenses_csv(expenses):
    """Export expenses to CSV file"""
    output = StringIO()
    writer = csv.writer(output)

    # Write header row
    writer.writerow([
        'Title', 'Description', 'Category', 'Amount', 'Date Incurred', 
        'Payment Date', 'Payment Method', 'Reference Number', 
        'Vendor/Supplier', 'Paid Status'
    ])

    # Write data rows
    for expense in expenses:
        category = ExpenseCategory.query.get(expense.category_id)
        writer.writerow([
            expense.title,
            expense.description,
            category.name if category else '',
            f"${expense.amount:.2f}",
            expense.date_incurred.strftime('%Y-%m-%d'),
            expense.payment_date.strftime('%Y-%m-%d') if expense.payment_date else '',
            expense.payment_method,
            expense.reference_number,
            expense.vendor_name,
            'Paid' if expense.is_paid else 'Unpaid'
        ])

    # Create response
    output.seek(0)
    return Response(
        output,
        mimetype='text/csv',
        headers={'Content-Disposition': f'attachment;filename=expenses_{date.today().strftime("%Y%m%d")}.csv'}
    )

def export_profit_loss_csv(report_data, start_date, end_date):
    """Export profit and loss report to CSV"""
    # Placeholder - implement actual CSV export for profit and loss report
    pass

def export_expense_summary_csv(report_data, start_date, end_date):
    """Export expense summary report to CSV"""
    # Placeholder - implement actual CSV export for expense summary report
    pass

def export_revenue_summary_csv(report_data, start_date, end_date):
    """Export revenue summary report to CSV"""
    # Placeholder - implement actual CSV export for revenue summary report
    pass

def export_supplier_payments_csv(report_data, start_date, end_date):
    """Export supplier payments report to CSV"""
    # Placeholder - implement actual CSV export for supplier payments report
    pass

@finance.route('/suppliers')
@login_required
def list_suppliers():
    """List all suppliers with prepayment data - same as supplier costs"""
    # Wrap entire function in try-except to catch any unhandled OSError
    try:
        return _list_suppliers_impl()
    except OSError as os_err:
        safe_log_error("OSError in list_suppliers (top-level catch)", os_err)
        # Return empty data to allow page to render
        from app.forms.supplier import SupplierSearchForm
        form = SupplierSearchForm()
        return render_template('finance/suppliers_simple.html', 
                             supplier_stats=[],
                             form=form,
                             query='',
                             country='',
                             supplier_type='')
    except Exception as e:
        safe_log_error("Unexpected error in list_suppliers (top-level catch)", e)
        # Return empty data to allow page to render
        from app.forms.supplier import SupplierSearchForm
        form = SupplierSearchForm()
        return render_template('finance/suppliers_simple.html', 
                             supplier_stats=[],
                             form=form,
                             query='',
                             country='',
                             supplier_type='')

def _list_suppliers_impl():
    """Implementation of list_suppliers - separated for error handling"""
    # Get search/filter parameters
    query = request.args.get('query', '').strip()
    country = request.args.get('country', '')
    supplier_type = request.args.get('supplier_type', '')

    # Build base query for suppliers with filters
    # Wrap in try-except to catch any OSError during query construction
    try:
        suppliers_query = Supplier.query

        # Apply search filter (name, code, email)
        if query:
            try:
                search_term = f'%{query}%'
                suppliers_query = suppliers_query.filter(
                    db.or_(
                        Supplier.name.ilike(search_term),
                        Supplier.code.ilike(search_term),
                        Supplier.email.ilike(search_term),
                        Supplier.contact_person.ilike(search_term)
                    )
                )
            except OSError as os_err:
                safe_log_error(f"OSError applying search filter for query '{query}'", os_err)
                # Continue without search filter
            except Exception as e:
                safe_log_error(f"Error applying search filter for query '{query}'", e)
                # Continue without search filter

        # Apply country filter
        if country:
            try:
                suppliers_query = suppliers_query.filter(Supplier.country == country)
            except OSError as os_err:
                safe_log_error(f"OSError applying country filter '{country}'", os_err)
                # Continue without country filter
            except Exception as e:
                safe_log_error(f"Error applying country filter '{country}'", e)
                # Continue without country filter

        # Apply supplier type filter
        if supplier_type:
            try:
                suppliers_query = suppliers_query.filter(Supplier.supplier_type == supplier_type)
            except OSError as os_err:
                safe_log_error(f"OSError applying supplier_type filter '{supplier_type}'", os_err)
                # Continue without supplier type filter
            except Exception as e:
                safe_log_error(f"Error applying supplier_type filter '{supplier_type}'", e)
                # Continue without supplier type filter

        # Get filtered suppliers - with defensive ordering to handle NULL names and encoding issues
        try:
            # Try ordering by name with NULL handling
            all_suppliers = suppliers_query.order_by(
                func.coalesce(Supplier.name, '').asc(),
                Supplier.id.asc()
            ).all()
        except OSError as os_err:
            safe_log_error("OSError ordering suppliers by name", os_err)
            try:
                # Fallback: order by ID only
                all_suppliers = suppliers_query.order_by(Supplier.id.asc()).all()
            except OSError as os_err2:
                safe_log_error("OSError ordering suppliers by ID", os_err2)
                # Last resort: no ordering
                try:
                    all_suppliers = suppliers_query.all()
                    # Sort in Python instead
                    try:
                        all_suppliers.sort(key=lambda s: (s.name or '', s.id or 0))
                    except:
                        pass  # If sorting fails, use unsorted list
                except OSError as os_err3:
                    safe_log_error("OSError loading suppliers without ordering", os_err3)
                    all_suppliers = []
                except Exception as e3:
                    safe_log_error("Error loading suppliers without ordering", e3)
                    all_suppliers = []
            except Exception as e2:
                safe_log_error("Error ordering suppliers by ID", e2)
                try:
                    all_suppliers = suppliers_query.all()
                except:
                    all_suppliers = []
        except Exception as e:
            safe_log_error("Error ordering suppliers", e)
            try:
                # Fallback: order by ID only
                all_suppliers = suppliers_query.order_by(Supplier.id.asc()).all()
            except:
                # Last resort: no ordering
                try:
                    all_suppliers = suppliers_query.all()
                except:
                    all_suppliers = []
    except OSError as os_err:
        safe_log_error("OSError in supplier query construction", os_err)
        all_suppliers = []
    except Exception as e:
        safe_log_error("Error in supplier query construction", e)
        all_suppliers = []

    # Get all prepayment lines with supplier info
    # Use a simpler approach to avoid Windows encoding issues with complex queries
    prepayment_data = []
    try:
        # Get all prepayment lines first
        # Handle NULL created_at values and potential encoding issues
        prepayment_lines = []
        
        # Try multiple ordering strategies, falling back if one fails
        ordering_strategies = [
            # Strategy 1: Order by created_at with NULL handling using coalesce
            lambda: db.session.query(SupplierPrepaymentLine).order_by(
                func.coalesce(SupplierPrepaymentLine.created_at, datetime(1970, 1, 1)).desc(),
                SupplierPrepaymentLine.id.desc()
            ),
            # Strategy 2: Order by ID only (most reliable)
            lambda: db.session.query(SupplierPrepaymentLine).order_by(
                SupplierPrepaymentLine.id.desc()
            ),
            # Strategy 3: No ordering (last resort)
            lambda: db.session.query(SupplierPrepaymentLine)
        ]
        
        for strategy in ordering_strategies:
            try:
                prepayment_lines = strategy().all()
                break  # Success, exit the loop
            except OSError as os_err:
                # Log OSError specifically for Windows encoding issues
                safe_log_error("OSError in prepayment lines ordering strategy", os_err)
                # Try next strategy
                continue
            except Exception as order_err:
                # Log other errors
                safe_log_error("Error in prepayment lines ordering strategy", order_err)
                # Try next strategy
                continue
        
        # If all strategies failed, prepayment_lines will be empty list
        if not prepayment_lines:
            # Last resort: try without any ordering
            try:
                prepayment_lines = db.session.query(SupplierPrepaymentLine).all()
                # Sort in Python instead, handling None values safely
                def sort_key(x):
                    try:
                        created = x.created_at if x.created_at else datetime(1970, 1, 1)
                        return (created, x.id or 0)
                    except:
                        return (datetime(1970, 1, 1), x.id or 0)
                prepayment_lines.sort(key=sort_key, reverse=True)
            except OSError as os_err:
                safe_log_error("OSError loading prepayment lines without ordering", os_err)
                prepayment_lines = []
            except Exception as e:
                safe_log_error("Error loading prepayment lines without ordering", e)
                prepayment_lines = []
        
        # Then manually join with payments and suppliers
        # Add defensive handling for each iteration to prevent OSError from corrupting data
        for line in prepayment_lines:
            payment = None
            supplier = None
            if line.supplier_payment_id:
                try:
                    payment = SupplierPayment.query.get(line.supplier_payment_id)
                    if payment and payment.supplier_id:
                        try:
                            supplier = Supplier.query.get(payment.supplier_id)
                        except OSError as os_err:
                            safe_log_error(f"OSError loading supplier {payment.supplier_id} for prepayment line {line.id}", os_err)
                            supplier = None
                        except Exception as e:
                            safe_log_error(f"Error loading supplier {payment.supplier_id} for prepayment line {line.id}", e)
                            supplier = None
                except OSError as os_err:
                    safe_log_error(f"OSError loading payment {line.supplier_payment_id} for prepayment line {line.id}", os_err)
                    payment = None
                except Exception as e:
                    safe_log_error(f"Error loading payment {line.supplier_payment_id} for prepayment line {line.id}", e)
                    payment = None
            
            # Safely append the data, handling any encoding issues
            try:
                prepayment_data.append((line, payment, supplier))
            except OSError as os_err:
                safe_log_error(f"OSError appending prepayment data for line {line.id}", os_err)
                # Skip this line if appending fails
                continue
            except Exception as e:
                safe_log_error(f"Error appending prepayment data for line {line.id}", e)
                # Skip this line if appending fails
                continue
    except OSError as os_err:
        # Catch Windows encoding errors - use empty list
        safe_log_error("OSError in prepayment data loading (outer catch)", os_err)
        prepayment_data = []
    except Exception as e:
        # If there's any other error, log it safely and use empty list
        safe_log_error("Error loading prepayment data (outer catch)", e)
        prepayment_data = []

    # Group by supplier and calculate totals
    supplier_stats = {}
    for line, payment, supplier in prepayment_data:
        # Skip if supplier is None (from outerjoin)
        if not supplier:
            continue

        if supplier.id not in supplier_stats:
            supplier_stats[supplier.id] = {
                'supplier': supplier,
                'total_payments': 0,
                'active_services': 0,
                'prepayment_lines': []
            }

        supplier_stats[supplier.id]['total_payments'] += line.amount or 0
        supplier_stats[supplier.id]['prepayment_lines'].append({
            'line': line,
            'payment': payment
        })

        # Count as active service if not cancelled
        # Safely check service_item relationship
        try:
            if line.service_item_id and line.service_item:
                # Check if status attribute exists before accessing
                if hasattr(line.service_item, 'status') and line.service_item.status != 'CANCELLED':
                    supplier_stats[supplier.id]['active_services'] += 1
        except (AttributeError, Exception) as e:
            # If service_item relationship fails, skip counting
            safe_log_error(f"Error accessing service_item for line {line.id}", e)
            pass

    # Build final stats list from filtered suppliers
    final_stats = []

    for supplier in all_suppliers:
        if supplier.id in supplier_stats:
            final_stats.append(supplier_stats[supplier.id])
        else:
            final_stats.append({
                'supplier': supplier,
                'total_payments': 0,
                'active_services': 0,
                'prepayment_lines': []
            })

    # Build form choices for dropdowns
    from app.forms.supplier import SupplierSearchForm
    form = SupplierSearchForm()

    return render_template('finance/suppliers_simple.html', 
                          supplier_stats=final_stats,
                          form=form,
                          query=query,
                          country=country,
                          supplier_type=supplier_type)

_SUPPLIER_TYPE_PAGE_MAP = {
    'accommodation': {
        'label': 'Accommodation',
        'icon': 'fa-hotel',
        'patterns': ['HOTEL', 'ACCOMMODATION'],
        'new_supplier_type': 'HOTEL',
        'search_placeholder': 'Search by Name / City',
        'search_fields': ['name', 'city'],
    },
    'airline': {
        'label': 'Airline',
        'icon': 'fa-plane',
        'patterns': ['AIRLINE'],
        'new_supplier_type': 'AIRLINE',
        'search_placeholder': 'Search by Name',
        'search_fields': ['name'],
    },
    'transportation': {
        'label': 'Transportation',
        'icon': 'fa-bus',
        'patterns': ['TRANSPORT', 'TRANSPORTATION', 'TRANSFER'],
        'new_supplier_type': 'TRANSPORT',
        'search_placeholder': 'Search by Name / Phone / City',
        'search_fields': ['name', 'phone', 'city'],
    },
    'guides': {
        'label': 'Guides',
        'icon': 'fa-user-tie',
        'patterns': ['GUIDE'],
        'new_supplier_type': 'GUIDE',
        'search_placeholder': 'Search by Name / Phone / City',
        'search_fields': ['name', 'phone', 'city'],
    },
    'meet-assist': {
        'label': 'Meet and assist',
        'icon': 'fa-handshake',
        'patterns': ['GROUND_HANDLER', 'MEET', 'ASSIST'],
        'new_supplier_type': 'GROUND_HANDLER',
        'search_placeholder': 'Search by Name / City',
        'search_fields': ['name', 'city'],
    },
    'restaurant': {
        'label': 'Restaurant',
        'icon': 'fa-utensils',
        'patterns': ['RESTAURANT', 'MEAL', 'FOOD'],
        'new_supplier_type': 'RESTAURANT',
        'search_placeholder': 'Search by Name / Phone / City',
        'search_fields': ['name', 'phone', 'city'],
    },
    'others': {
        'label': 'Others',
        'icon': 'fa-layer-group',
        'patterns': [],
        'new_supplier_type': '',
        'search_placeholder': 'Search by Name',
        'search_fields': ['name'],
    },
}


def _query_suppliers_for_type(type_key, search_query=''):
    """Return suppliers for a supplier type hub page, optionally filtered by name."""
    config = _SUPPLIER_TYPE_PAGE_MAP.get(type_key)
    if not config:
        return None, []

    suppliers_query = Supplier.query
    search_query = (search_query or '').strip()

    try:
        if config['patterns']:
            filters = [Supplier.supplier_type.ilike(f'%{p}%') for p in config['patterns']]
            suppliers_query = suppliers_query.filter(or_(*filters))
        else:
            suppliers_query = suppliers_query.filter(
                ~or_(
                    Supplier.supplier_type.ilike('%HOTEL%'),
                    Supplier.supplier_type.ilike('%ACCOMMODATION%'),
                    Supplier.supplier_type.ilike('%AIRLINE%'),
                    Supplier.supplier_type.ilike('%TRANSPORT%'),
                    Supplier.supplier_type.ilike('%TRANSFER%'),
                    Supplier.supplier_type.ilike('%GUIDE%'),
                    Supplier.supplier_type.ilike('%GROUND_HANDLER%'),
                    Supplier.supplier_type.ilike('%MEET%'),
                    Supplier.supplier_type.ilike('%ASSIST%'),
                    Supplier.supplier_type.ilike('%RESTAURANT%'),
                    Supplier.supplier_type.ilike('%MEAL%'),
                    Supplier.supplier_type.ilike('%FOOD%'),
                )
            )
    except Exception as e:
        safe_log_error(f'Error applying supplier type page filter {type_key}', e)
        suppliers_query = Supplier.query.filter(db.text('1=0'))

    if search_query:
        search_fields = config.get('search_fields', ['name'])
        search_filters = []
        for field in search_fields:
            if field == 'name':
                search_filters.append(Supplier.name.ilike(f'%{search_query}%'))
            elif field == 'city':
                search_filters.append(Supplier.city.ilike(f'%{search_query}%'))
            elif field == 'phone':
                search_filters.append(Supplier.phone.ilike(f'%{search_query}%'))
        if search_filters:
            suppliers_query = suppliers_query.filter(or_(*search_filters))

    if type_key == 'meet-assist':
        from app.routes.inbound import sync_all_meet_assist_representative_pairs
        try:
            sync_all_meet_assist_representative_pairs()
        except Exception as e:
            safe_log_error('Meet & Assist representative sync failed', e)

    suppliers = suppliers_query.order_by(func.coalesce(Supplier.name, '').asc()).all()
    return config, suppliers


@finance.route('/suppliers/type/<type_key>')
@login_required
def supplier_type_page(type_key):
    """Dedicated page for a supplier type"""
    config, suppliers = _query_suppliers_for_type(type_key, request.args.get('q', ''))
    if not config:
        return redirect(url_for('finance.list_suppliers'))

    search_query = request.args.get('q', '').strip()
    return render_template(
        'finance/suppliers_type_page.html',
        type_key=type_key,
        type_label=config['label'],
        type_icon=config['icon'],
        suppliers=suppliers,
        query=search_query,
        new_supplier_type=config['new_supplier_type'],
        search_placeholder=config.get('search_placeholder', 'Search'),
    )


@finance.route('/suppliers/type/<type_key>/print')
@login_required
def print_supplier_type_page(type_key):
    """Print-friendly view of suppliers for a type page."""
    config, suppliers = _query_suppliers_for_type(type_key, request.args.get('q', ''))
    if not config:
        return redirect(url_for('finance.list_suppliers'))

    search_query = request.args.get('q', '').strip()
    filter_summary = []
    if search_query:
        filter_summary.append(('Search', search_query))

    return render_template(
        'finance/suppliers_type_print.html',
        type_key=type_key,
        type_label=config['label'],
        suppliers=suppliers,
        filter_summary=filter_summary,
        page_title=f'{config["label"]} Suppliers',
        printed_at=datetime.now(),
    )


def _bank_fields_from_payment_method(payment_method, bank_name, bank_account, cliq_alias, other_payment_method=None):
    """Map payment method selection to stored supplier bank fields."""
    method = (payment_method or '').strip()
    if method == 'Cliq':
        return 'Cliq', (cliq_alias or '').strip() or None
    if method == 'Bank':
        return (bank_name or '').strip() or None, (bank_account or '').strip() or None
    if method == 'Other':
        return 'Other', (other_payment_method or '').strip() or None
    return None, None


@finance.route('/suppliers/type/<type_key>/quick-add', methods=['POST'])
@login_required
def quick_add_supplier(type_key):
    """Create supplier from the type-page popup modal."""
    type_map = {
        'accommodation': 'HOTEL',
        'airline': 'AIRLINE',
        'transportation': 'TRANSPORT',
        'guides': 'GUIDE',
        'meet-assist': 'GROUND_HANDLER',
        'restaurant': 'RESTAURANT',
        'others': ''
    }

    base_supplier_type = type_map.get(type_key)
    if base_supplier_type is None:
        flash('Invalid supplier type page.', 'error')
        return redirect(url_for('finance.list_suppliers'))

    name = (request.form.get('name') or '').strip()
    if not name:
        flash('Name is required.', 'error')
        return redirect(url_for('finance.supplier_type_page', type_key=type_key))

    phone_val = (request.form.get('phone') or '').strip()
    if phone_val and not is_valid_phone(phone_val):
        flash(f'Phone: {PHONE_ERROR}', 'error')
        return redirect(url_for('finance.supplier_type_page', type_key=type_key))

    entity_type = (request.form.get('entity_type') or 'COMPANY').strip().upper() or 'COMPANY'
    requested_type = (request.form.get('supplier_type') or '').strip().upper()
    supplier_type = requested_type or base_supplier_type
    payment_terms = (request.form.get('payment_terms') or '').strip() or None
    payment_method = (request.form.get('payment_method') or '').strip()
    cliq_alias = (request.form.get('cliq_alias') or '').strip()
    guide_languages = (request.form.get('guide_languages') or '').strip()

    # Generate unique supplier code similar to SUP001 style.
    base_code = ''.join([c for c in name.upper() if c.isalnum()])[:4] or 'SUP'
    candidate_code = f"{base_code}{datetime.utcnow().strftime('%H%M%S')}"
    code = candidate_code
    suffix = 1
    while Supplier.query.filter_by(code=code).first():
        code = f"{candidate_code}{suffix}"
        suffix += 1

    category = (request.form.get('category') or '').strip()
    custom_category = (request.form.get('custom_category') or '').strip()
    room_category = (request.form.get('room_category') or '').strip()
    notes = (request.form.get('notes') or '').strip()
    other_payment_method = (request.form.get('other_payment_method') or '').strip()
    bank_iban = (request.form.get('bank_iban') or '').strip() or None
    merged_notes = notes
    # Keep category as "Other" but store custom value in notes if provided
    if category == 'Other' and custom_category:
        merged_notes = f"Custom Category: {custom_category}\n{merged_notes}".strip()
    if category:
        merged_notes = f"Category: {category}\n{merged_notes}".strip()
    if room_category:
        merged_notes = f"Room Category: {room_category}\n{merged_notes}".strip()
    if payment_method:
        merged_notes = f"Payment Method: {payment_method}\n{merged_notes}".strip()

    if payment_method:
        bank_name_val, bank_account_val = _bank_fields_from_payment_method(
            payment_method,
            request.form.get('bank_name'),
            request.form.get('bank_account'),
            cliq_alias,
            other_payment_method,
        )
    elif payment_terms == 'Cliq':
        bank_name_val = 'Cliq'
        bank_account_val = cliq_alias or None
    else:
        bank_name_val = (request.form.get('bank_name') or '').strip() or None
        bank_account_val = (request.form.get('bank_account') or '').strip() or None

    contract_file = request.files.get('contract_file')
    contract_saved_name = None
    if contract_file and contract_file.filename:
        try:
            safe_name = secure_filename(contract_file.filename)
            upload_dir = os.path.join(current_app.root_path, 'static', 'uploads', 'supplier_contracts')
            os.makedirs(upload_dir, exist_ok=True)
            timestamped_name = f"{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{safe_name}"
            contract_file.save(os.path.join(upload_dir, timestamped_name))
            contract_saved_name = timestamped_name
        except Exception as e:
            safe_log_error('Could not save contract attachment', e)

    try:
        supplier = Supplier(
            name=name,
            code=code,
            supplier_type=supplier_type,
            entity_type=entity_type,
            contact_person=(request.form.get('contact_person') or '').strip() or None,
            email=(request.form.get('email') or '').strip() or None,
            phone=(request.form.get('phone') or '').strip() or None,
            website=(request.form.get('website') or '').strip() or None,
            address=(request.form.get('address') or '').strip() or None,
            city=(request.form.get('city') or '').strip() or None,
            country=(request.form.get('country') or '').strip() or None,
            payment_terms=payment_terms,
            payment_method=payment_method,
            default_currency=(request.form.get('default_currency') or 'USD').strip() or 'USD',
            bank_name=bank_name_val,
            bank_account=bank_account_val,
            bank_iban=bank_iban,
            tax_number=(request.form.get('tax_number') or '').strip() or None,
            notes=merged_notes or None,
            languages=guide_languages or None
        )
        if contract_saved_name:
            supplier.notes = (supplier.notes or '')
            supplier.notes = f"Contract file: {contract_saved_name}\n{supplier.notes}".strip()
        db.session.add(supplier)
        db.session.commit()
        from app.routes.inbound import _invalidate_supplier_dropdown_cache
        _invalidate_supplier_dropdown_cache()
        flash(f'{name} added successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        safe_log_error(f'Error quick-adding supplier on {type_key}', e)
        flash('Could not add supplier. Please try again.', 'error')

    return redirect(url_for('finance.supplier_type_page', type_key=type_key))


def _parse_supplier_notes(notes_raw):
    """Extract structured fields that quick_add_supplier embeds into the notes column."""
    category = ''
    custom_category = ''
    room_category = ''
    payment_method_embedded = ''
    contract_file = ''
    clean_lines = []
    for line in (notes_raw or '').split('\n'):
        if line.startswith('Category: ') and not category:
            category = line[len('Category: '):]
        elif line.startswith('Custom Category: ') and not custom_category:
            custom_category = line[len('Custom Category: '):]
        elif line.startswith('Room Category: ') and not room_category:
            room_category = line[len('Room Category: '):]
        elif line.startswith('Payment Method: ') and not payment_method_embedded:
            payment_method_embedded = line[len('Payment Method: '):]
        elif line.startswith('Contract file: ') and not contract_file:
            contract_file = line[len('Contract file: '):]
        else:
            clean_lines.append(line)
    return {
        'category': category,
        'custom_category': custom_category,
        'room_category': room_category,
        'payment_method_embedded': payment_method_embedded,
        'contract_file': contract_file,
        'clean_notes': '\n'.join(clean_lines).strip(),
    }


@finance.route('/suppliers/type/<type_key>/edit/<int:supplier_id>', methods=['GET', 'POST'])
@login_required
def edit_supplier_type(type_key, supplier_id):
    """Full-page edit form for a supplier on a type page (replaces the old details screen)."""
    supplier = Supplier.query.get_or_404(supplier_id)
    config, _ = _query_suppliers_for_type(type_key, '')
    if not config:
        return redirect(url_for('finance.list_suppliers'))

    if request.method == 'POST':
        name = (request.form.get('name') or '').strip()
        if not name:
            flash('Name is required.', 'error')
            return redirect(request.url)

        phone_val = (request.form.get('phone') or '').strip()
        if phone_val and not is_valid_phone(phone_val):
            flash(f'Phone: {PHONE_ERROR}', 'error')
            return redirect(request.url)

        entity_type = (request.form.get('entity_type') or 'COMPANY').strip().upper() or 'COMPANY'
        if entity_type:
            supplier.entity_type = entity_type

        requested_type = (request.form.get('supplier_type') or '').strip().upper()
        if requested_type:
            supplier.supplier_type = requested_type

        payment_method = (request.form.get('payment_method') or '').strip()
        cliq_alias = (request.form.get('cliq_alias') or '').strip()
        guide_languages = (request.form.get('guide_languages') or '').strip()
        category = (request.form.get('category') or '').strip()
        custom_category = (request.form.get('custom_category') or '').strip()
        room_category = (request.form.get('room_category') or '').strip()
        notes = (request.form.get('notes') or '').strip()
        other_payment_method = (request.form.get('other_payment_method') or '').strip()
        bank_iban = (request.form.get('bank_iban') or '').strip() or None

        merged_notes = notes
        # Keep category as "Other" but store custom value in notes if provided
        if category == 'Other' and custom_category:
            merged_notes = f"Custom Category: {custom_category}\n{merged_notes}".strip()
        if category:
            merged_notes = f"Category: {category}\n{merged_notes}".strip()
        if room_category:
            merged_notes = f"Room Category: {room_category}\n{merged_notes}".strip()
        if payment_method:
            merged_notes = f"Payment Method: {payment_method}\n{merged_notes}".strip()

        # Handle contract file upload: use new file if provided, otherwise keep existing
        parsed_existing = _parse_supplier_notes(supplier.notes)
        new_contract_file = request.files.get('contract_file')
        contract_saved_name = parsed_existing['contract_file']
        if new_contract_file and new_contract_file.filename:
            try:
                safe_name = secure_filename(new_contract_file.filename)
                upload_dir = os.path.join(current_app.root_path, 'static', 'uploads', 'supplier_contracts')
                os.makedirs(upload_dir, exist_ok=True)
                timestamped_name = f"{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{safe_name}"
                new_contract_file.save(os.path.join(upload_dir, timestamped_name))
                contract_saved_name = timestamped_name
            except Exception as e:
                safe_log_error('Could not save contract attachment', e)
        if contract_saved_name:
            merged_notes = f"Contract file: {contract_saved_name}\n{merged_notes}".strip()

        if payment_method:
            bank_name_val, bank_account_val = _bank_fields_from_payment_method(
                payment_method,
                request.form.get('bank_name'),
                request.form.get('bank_account'),
                cliq_alias,
                other_payment_method,
            )
        else:
            bank_name_val = (request.form.get('bank_name') or '').strip() or None
            bank_account_val = (request.form.get('bank_account') or '').strip() or None

        supplier.name = name
        supplier.contact_person = (request.form.get('contact_person') or '').strip() or None
        supplier.email = (request.form.get('email') or '').strip() or None
        supplier.phone = (request.form.get('phone') or '').strip() or None
        supplier.website = (request.form.get('website') or '').strip() or None
        supplier.address = (request.form.get('address') or '').strip() or None
        supplier.city = (request.form.get('city') or '').strip() or None
        supplier.country = (request.form.get('country') or '').strip() or None
        supplier.payment_terms = (request.form.get('payment_terms') or '').strip() or None
        supplier.payment_method = payment_method or None
        supplier.default_currency = (request.form.get('default_currency') or 'USD').strip() or 'USD'
        supplier.bank_name = bank_name_val
        supplier.bank_account = bank_account_val
        supplier.bank_iban = bank_iban
        supplier.tax_number = (request.form.get('tax_number') or '').strip() or None
        supplier.notes = merged_notes or None
        if guide_languages:
            supplier.languages = guide_languages

        try:
            db.session.commit()
            from app.routes.inbound import _invalidate_supplier_dropdown_cache
            _invalidate_supplier_dropdown_cache()
            flash(f'{name} updated successfully.', 'success')
        except Exception as e:
            db.session.rollback()
            safe_log_error(f'Error updating supplier {supplier_id}', e)
            flash('Could not save changes. Please try again.', 'error')

        return redirect(url_for('finance.supplier_type_page', type_key=type_key))

    # GET: determine pre-fill values
    parsed = _parse_supplier_notes(supplier.notes)

    if supplier.bank_name == 'Cliq':
        payment_method = 'Cliq'
        cliq_alias = supplier.bank_account or ''
        bank_name = ''
        bank_account = ''
        bank_iban = ''
        other_payment_method = ''
    elif supplier.bank_name == 'Other':
        payment_method = 'Other'
        other_payment_method = supplier.bank_account or ''
        cliq_alias = ''
        bank_name = ''
        bank_account = ''
        bank_iban = ''
    elif supplier.bank_name:
        payment_method = 'Bank'
        bank_name = supplier.bank_name
        bank_account = supplier.bank_account or ''
        bank_iban = supplier.bank_iban or ''
        cliq_alias = ''
        other_payment_method = ''
    else:
        payment_method = parsed['payment_method_embedded']
        bank_name = ''
        bank_account = ''
        bank_iban = ''
        cliq_alias = ''
        other_payment_method = ''

    return render_template(
        'finance/supplier_type_edit.html',
        supplier=supplier,
        type_key=type_key,
        type_label=config['label'],
        type_icon=config['icon'],
        new_supplier_type=config['new_supplier_type'],
        category=parsed['category'],
        custom_category=parsed['custom_category'],
        room_category=parsed['room_category'],
        clean_notes=parsed['clean_notes'],
        payment_method=payment_method,
        bank_name=bank_name,
        bank_account=bank_account,
        bank_iban=bank_iban,
        cliq_alias=cliq_alias,
        other_payment_method=other_payment_method,
        contract_file=parsed['contract_file'],
    )


@finance.route('/new-supplier', methods=['GET', 'POST'])
@login_required
def new_supplier():
    """Create a new supplier"""
    from app.forms.supplier import SupplierForm
    from app.models.supplier import Supplier

    form = SupplierForm()
    default_supplier_type = (request.args.get('supplier_type') or '').strip().upper()
    if request.method == 'GET' and default_supplier_type:
        form.supplier_type.data = default_supplier_type

    if form.validate_on_submit():
        try:
            entity_type = form.entity_type.data or 'COMPANY'

            # For freelancers, service types are not required
            if entity_type == 'FREELANCER' and not form.service_types.data:
                # Service types validation is only required for companies
                pass
            elif entity_type == 'COMPANY' and not form.service_types.data:
                # Service types are required for companies
                flash('Service Types are required for Company suppliers.', 'error')
                return render_template('finance/new_supplier.html', form=form, is_new=True)

            supplier = Supplier(
                name=form.name.data,
                code=form.code.data,
                entity_type=entity_type,
                supplier_type=form.supplier_type.data,
                contact_person=form.contact_person.data,
                email=form.email.data,
                phone=form.phone.data,
                website=form.website.data,
                address=form.address.data,
                city=form.city.data,
                country=form.country.data,
                payment_terms=form.payment_terms.data,
                payment_method=form.payment_method.data,
                default_currency=form.default_currency.data,
                bank_name=form.bank_name.data,
                bank_account=form.bank_account.data,
                tax_number=form.tax_number.data,
                notes=form.notes.data
            )

            db.session.add(supplier)
            db.session.flush()  # Get the supplier ID before creating services

            # Create SupplierService records for each selected service type (only for companies)
            from app.models.supplier import SupplierService
            if entity_type == 'COMPANY' and form.service_types.data:
                for service_type in form.service_types.data:
                    # Default commission rates per service type
                    default_rates = {
                        'FLIGHT': 8.0,
                        'HOTEL': 15.0,
                        'TRANSPORT': 12.0,
                        'VISA': 10.0,
                        'INSURANCE': 25.0
                    }

                    service = SupplierService(
                        supplier_id=supplier.id,
                        service_type=service_type,
                        service_name=f"{service_type.title()} Services",
                        commission_rate=default_rates.get(service_type, 10.0)
                    )
                    db.session.add(service)

            db.session.commit()

            message = 'Freelancer created successfully!' if entity_type == 'FREELANCER' else 'Supplier created successfully with selected service types!'
            flash(message, 'success')
            return redirect(url_for('finance.list_suppliers'))

        except Exception as e:
            db.session.rollback()
            flash(f'Error creating supplier: {str(e)}', 'error')

    return render_template('finance/new_supplier.html', form=form, is_new=True)

@finance.route('/supplier-costs')
@login_required
def supplier_costs():
    """Supplier costs view - shows prepayment lines across all suppliers"""
    # Get filter parameters
    supplier_id = request.args.get('supplier_id')
    service_type = request.args.get('service_type')
    payment_status = request.args.get('payment_status')
    from_date = request.args.get('from_date')
    to_date = request.args.get('to_date')

    # Build query
    query = SupplierPrepaymentLine.query

    # Apply filters
    if supplier_id:
        # Find prepayment lines for supplier payments from this supplier
        from app.models.supplier import SupplierPayment
        supplier_payments = SupplierPayment.query.filter_by(supplier_id=int(supplier_id)).all()
        payment_ids = [payment.id for payment in supplier_payments]
        if payment_ids:
            query = query.filter(SupplierPrepaymentLine.supplier_payment_id.in_(payment_ids))
    if service_type:
        query = query.filter(SupplierPrepaymentLine.service_type == service_type)
    if payment_status:
        query = query.filter(SupplierPrepaymentLine.payment_status == payment_status)
    if from_date:
        try:
            from_date_obj = datetime.strptime(from_date, '%Y-%m-%d').date()
            query = query.filter(SupplierPrepaymentLine.created_at >= from_date_obj)
        except (ValueError, TypeError):
            flash('Invalid from date format', 'warning')
    if to_date:
        try:
            to_date_obj = datetime.strptime(to_date, '%Y-%m-%d').date()
            to_date_obj = datetime.combine(to_date_obj, datetime.max.time())
            query = query.filter(SupplierPrepaymentLine.created_at <= to_date_obj)
        except (ValueError, TypeError):
            flash('Invalid to date format', 'warning')

    # Order by date descending - with robust ordering to handle NULL dates
    try:
        prepayment_lines = query.order_by(
            func.coalesce(SupplierPrepaymentLine.created_at, datetime(1970, 1, 1)).desc(),
            SupplierPrepaymentLine.id.desc()
        ).all()
    except (OSError, Exception) as e:
        safe_log_error("Error ordering prepayment lines", e)
        try:
            # Fallback: order by ID only
            prepayment_lines = query.order_by(SupplierPrepaymentLine.id.desc()).all()
        except:
            prepayment_lines = []

    # Calculate total amount
    total_amount = sum(line.amount for line in prepayment_lines)

    # Get all suppliers for the filter dropdown
    suppliers = Supplier.query.order_by(Supplier.name).all()

    return render_template(
        'finance/supplier_costs.html', 
        prepayment_lines=prepayment_lines,
        total_amount=total_amount,
        suppliers=suppliers
    )

@finance.route('/clear-all-suppliers', methods=['POST'])
@login_required
def clear_all_suppliers():
    """Clear all supplier data from the database"""
    try:
        from sqlalchemy import text
        
        # Count existing records BEFORE deletion
        supplier_count_before = Supplier.query.count()
        service_count_before = SupplierService.query.count()
        payment_count_before = SupplierPayment.query.count()
        prepayment_count_before = SupplierPrepaymentLine.query.count()
        
        if supplier_count_before == 0:
            flash('No suppliers found. Nothing to delete.', 'info')
            return redirect(url_for('finance.list_suppliers'))
        
        # Handle ServiceConfirmation references (set supplier_id to NULL)
        with db.engine.connect() as conn:
            conn.execute(text("UPDATE service_confirmation SET supplier_id = NULL WHERE supplier_id IS NOT NULL"))
            conn.commit()
        
        # Delete prepayment lines
        prepayment_deleted = db.session.query(SupplierPrepaymentLine).delete()
        db.session.commit()
        
        # Delete supplier payments
        payment_deleted = db.session.query(SupplierPayment).delete()
        db.session.commit()
        
        # Delete supplier services
        service_deleted = db.session.query(SupplierService).delete()
        db.session.commit()
        
        # Finally, delete all suppliers - use direct SQL to ensure it works
        with db.engine.connect() as conn:
            # Delete all suppliers using direct SQL
            result = conn.execute(text("DELETE FROM supplier"))
            supplier_deleted = result.rowcount
            conn.commit()
        
        # Verify deletion
        supplier_count_after = Supplier.query.count()
        service_count_after = SupplierService.query.count()
        payment_count_after = SupplierPayment.query.count()
        prepayment_count_after = SupplierPrepaymentLine.query.count()
        
        if supplier_count_after > 0:
            flash(f'Warning: {supplier_count_after} suppliers still remain after deletion. This may be a caching issue - please hard refresh the page (Ctrl+F5) or clear your browser cache.', 'warning')
        else:
            flash(f'Successfully deleted all supplier data: {supplier_deleted} suppliers, {service_deleted} services, {payment_deleted} payments, {prepayment_deleted} prepayment lines. Please refresh any open pages to see the changes.', 'success')
        
        return redirect(url_for('finance.list_suppliers'))
        
    except Exception as e:
        db.session.rollback()
        safe_log_error("Error clearing all suppliers", e)
        flash(f'Error clearing supplier data: {str(e)}', 'error')
        return redirect(url_for('finance.list_suppliers'))

@finance.route('/supplier/<int:supplier_id>')
@login_required
def supplier_details(supplier_id):
    """Show supplier details and payment history"""
    from app.models.supplier import Supplier, SupplierPrepaymentLine

    supplier = Supplier.query.get_or_404(supplier_id)

    # Get prepayment lines for this supplier
    # This is our new approach - show costs directly from prepayment lines
    # With robust ordering to handle NULL dates
    try:
        prepayment_lines = SupplierPrepaymentLine.query.filter(
            SupplierPrepaymentLine.supplier_name == supplier.name
        ).options(
            db.joinedload(SupplierPrepaymentLine.service_item)
        ).order_by(
            func.coalesce(SupplierPrepaymentLine.created_at, datetime(1970, 1, 1)).desc(),
            SupplierPrepaymentLine.id.desc()
        ).all()
    except (OSError, Exception) as e:
        safe_log_error("Error loading prepayment lines for supplier", e)
        try:
            # Fallback: order by ID only
            prepayment_lines = SupplierPrepaymentLine.query.filter(
                SupplierPrepaymentLine.supplier_name == supplier.name
            ).options(
                db.joinedload(SupplierPrepaymentLine.service_item)
            ).order_by(SupplierPrepaymentLine.id.desc()).all()
        except:
            prepayment_lines = []

    # Also get legacy supplier payments for this supplier
    supplier_payments = SupplierPayment.query.filter_by(
        supplier_id=supplier_id
    ).options(
        db.joinedload(SupplierPayment.prepayment_lines)
    ).all()

    # Debug output
    # Debug logging (commented out to avoid Windows encoding issues)
    # current_app.logger.debug(f"Loaded {len(prepayment_lines)} supplier prepayment lines for supplier {supplier_id}")
    for line in prepayment_lines:
        booking_ref = "Unknown"
        try:
            # Get booking reference from the booking relationship
            # Booking already imported at top of file
            booking = Booking.query.get(line.booking_id)
            if booking:
                booking_ref = booking.reference_number
        except Exception as e:
            safe_log_error("Error getting booking", e)

        # current_app.logger.debug(f"Prepayment line ID {line.id}: {line.service_type} for booking {booking_ref}")

    # Calculate financial metrics
    total_paid = sum(payment.amount for payment in supplier_payments if payment.status == 'PAID')
    total_due = sum(line.amount for line in prepayment_lines if line.payment_status != 'PAID')
    total_confirmed = len(prepayment_lines)

    return render_template(
        'finance/supplier_details_new.html',
        supplier=supplier,
        prepayment_lines=prepayment_lines,
        supplier_payments=supplier_payments,
        total_paid=total_paid,
        total_due=total_due,
        total_confirmed=total_confirmed
    )

@finance.route('/supplier/<int:supplier_id>/toggle-status', methods=['POST'])
@login_required
def toggle_supplier_status(supplier_id):
    """Suspend or reactivate a supplier from the type page table."""
    from app.routes.inbound import _invalidate_supplier_dropdown_cache

    supplier = Supplier.query.get_or_404(supplier_id)
    supplier_name = supplier.name
    try:
        supplier.is_active = not supplier.is_active
        db.session.commit()
        _invalidate_supplier_dropdown_cache()
        if supplier.is_active:
            flash(f'Supplier "{supplier_name}" is now active.', 'success')
        else:
            flash(
                f'Supplier "{supplier_name}" suspended. It will not appear in request dropdowns.',
                'success',
            )
    except Exception as e:
        db.session.rollback()
        safe_log_error(f'Error toggling supplier status {supplier_id}', e)
        flash('Could not update supplier status. Please try again.', 'error')

    return redirect(request.referrer or url_for('finance.list_suppliers'))


@finance.route('/supplier/<int:supplier_id>/delete', methods=['POST'])
@login_required
def delete_supplier(supplier_id):
    """Delete one supplier from type page table."""
    supplier = Supplier.query.get_or_404(supplier_id)
    supplier_name = supplier.name
    try:
        db.session.delete(supplier)
        db.session.commit()
        flash(f'Supplier "{supplier_name}" deleted.', 'success')
    except Exception as e:
        db.session.rollback()
        safe_log_error(f'Error deleting supplier {supplier_id}', e)
        flash('Could not delete supplier. Please try again.', 'error')

    return redirect(request.referrer or url_for('finance.list_suppliers'))