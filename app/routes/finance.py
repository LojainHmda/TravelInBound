import os
import sys
import csv
from datetime import datetime, date, timedelta
from dateutil.relativedelta import relativedelta
from io import StringIO
from calendar import monthrange
from sqlalchemy import extract, func, case, and_, or_
from flask import (
    Blueprint, render_template, request, redirect, url_for, 
    flash, jsonify, current_app, send_file, Response
)
from flask_login import login_required, current_user

from app import db
from app.models import (
    ExpenseCategory, Expense, ExpenseAttachment, FinancialMetric, 
    ServiceItem, Payment, User, Document,
    EXPENSE_CATEGORY_RENT, EXPENSE_CATEGORY_UTILITIES
)
from app.models.booking import Booking
from app.models.supplier import SupplierPayment, Supplier, SupplierPrepaymentLine
from app.forms.expense import (
    ExpenseCategoryForm, ExpenseForm, ExpenseFilterForm,
    ExpenseAttachmentForm, FinancialReportFilterForm
)

finance = Blueprint('finance', __name__, url_prefix='/finance')

@finance.route('/')
@login_required
def index():
    """Finance module home with financial KPIs - Admin only access"""
    if not current_user.can_access_finance():
        flash('Access denied. Finance dashboard requires admin privileges.', 'error')
        return redirect(url_for('main.dashboard'))
    
    return dashboard()

@finance.route('/dashboard')
@login_required  
def dashboard():
    """Finance dashboard with financial KPIs"""
    if not current_user.can_access_finance():
        flash('Access denied. Finance dashboard requires admin privileges.', 'error')
        return redirect(url_for('main.dashboard'))
    # Get selected month from query parameter or default to current
    today = date.today()
    selected_month = request.args.get('month', 'current')
    
    # Determine date range based on selected month
    if selected_month == 'current':
        first_day = date(today.year, today.month, 1)
        last_day = date(today.year, today.month, monthrange(today.year, today.month)[1])
    elif selected_month == 'all':
        # All time data - use a wide range
        first_day = date(2020, 1, 1)  # Far in the past
        last_day = today
    else:
        # Handle relative months (-1, -2, -3)
        try:
            months_offset = int(selected_month)
            target_date = today + relativedelta(months=months_offset)
            first_day = date(target_date.year, target_date.month, 1)
            last_day = date(target_date.year, target_date.month, 
                          monthrange(target_date.year, target_date.month)[1])
        except (ValueError, TypeError):
            # Default to current month if invalid value
            first_day = date(today.year, today.month, 1)
            last_day = date(today.year, today.month, monthrange(today.year, today.month)[1])
    
    # Get previous period for comparison (always one month before the selected period)
    prev_month = first_day - timedelta(days=1)
    prev_first = date(prev_month.year, prev_month.month, 1)
    prev_last = date(prev_month.year, prev_month.month, monthrange(prev_month.year, prev_month.month)[1])
    
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
    
    # 3. Supplier Costs
    current_month_supplier_costs = db.session.query(func.sum(SupplierPayment.amount)).filter(
        SupplierPayment.payment_date >= first_day,
        SupplierPayment.payment_date <= last_day
    ).scalar() or 0
    
    # Count of supplier payments for the current month
    supplier_payments_count = db.session.query(func.count(SupplierPayment.id)).filter(
        SupplierPayment.payment_date >= first_day,
        SupplierPayment.payment_date <= last_day
    ).scalar() or 0
    
    prev_month_supplier_costs = db.session.query(func.sum(SupplierPayment.amount)).filter(
        SupplierPayment.payment_date >= prev_first,
        SupplierPayment.payment_date <= prev_last
    ).scalar() or 0
    
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
    
    # Get the filtered results
    revenue_bookings = booking_query.order_by(Booking.total_amount.desc()).all()
    last_12_months = []
    for i in range(11, -1, -1):
        month_date = date.today() - relativedelta(months=i)
        month_first = date(month_date.year, month_date.month, 1)
        month_last = date(month_date.year, month_date.month, monthrange(month_date.year, month_date.month)[1])
        
        month_revenue = db.session.query(func.sum(Payment.amount)).filter(
            Payment.payment_date >= month_first,
            Payment.payment_date <= month_last
        ).scalar() or 0
        
        month_expenses = db.session.query(func.sum(Expense.amount)).filter(
            Expense.date_incurred >= month_first,
            Expense.date_incurred <= month_last
        ).scalar() or 0
        
        month_supplier_costs = db.session.query(func.sum(SupplierPayment.amount)).filter(
            SupplierPayment.payment_date >= month_first,
            SupplierPayment.payment_date <= month_last
        ).scalar() or 0
        
        month_profit = month_revenue - month_expenses - month_supplier_costs
        
        last_12_months.append({
            'month': month_date.strftime('%b %Y'),
            'revenue': month_revenue,
            'expenses': month_expenses + month_supplier_costs,
            'profit': month_profit
        })
    
    # Get recent expenses
    recent_expenses = Expense.query.order_by(Expense.date_incurred.desc()).limit(5).all()
    
    # Get recent supplier payments
    upcoming_payments = SupplierPayment.query.filter(
        SupplierPayment.payment_date >= today - timedelta(days=30)
    ).order_by(SupplierPayment.payment_date.desc()).limit(5).all()
    
    # Get supplier payments for the selected period for the breakdown modal
    from app.models.service import ServiceConfirmation
    from app.models.supplier import Supplier, SupplierPrepaymentLine
    # Booking already imported at top of file
    
    # Use joinedload to preload all related data in a single query
    # We need to use class-bound attributes instead of strings for SQLAlchemy relationships
    from app.models.service import ServiceItem
    
    # SQLAlchemy in newer versions doesn't accept string relationship names
    supplier_payments = SupplierPayment.query.options(
        # Use basic queries without joinedloads to avoid errors
        db.joinedload(SupplierPayment.prepayment_lines),
        db.joinedload(SupplierPayment.service_confirmation)
    ).filter(
        SupplierPayment.payment_date >= first_day,
        SupplierPayment.payment_date <= last_day
    ).order_by(SupplierPayment.payment_date.desc()).all()
    
    # Debug output to verify prepayment lines are loaded
    print(f"Loaded {len(supplier_payments)} supplier payments for breakdown", file=sys.stderr)
    for payment in supplier_payments:
        prepayment_count = len(payment.prepayment_lines) if payment.prepayment_lines else 0
        print(f"Payment ID {payment.id}: {prepayment_count} prepayment lines", file=sys.stderr)
        
        # Print booking references for each prepayment line
        if payment.prepayment_lines:
            for line in payment.prepayment_lines:
                # Get booking reference using the booking_id directly
                # Booking already imported at top of file
                booking = Booking.query.get(line.booking_id)
                if booking:
                    print(f"  → Booking reference: {booking.reference_number}", file=sys.stderr)
                else:
                    print(f"  → No booking found for line {line.id}", file=sys.stderr)
                    
        # Also verify service confirmation path for backwards compatibility
        if payment.service_confirmation and payment.service_confirmation.service_item and payment.service_confirmation.service_item.booking:
            print(f"  → Service confirmation booking reference: {payment.service_confirmation.service_item.booking.reference_number}", file=sys.stderr)

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
    
    # Order expenses by date (most recent first)
    expenses = query.order_by(Expense.date_incurred.desc()).all()
    
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
        # Get payments received from customers
        payments_in = db.session.query(
            Payment.payment_date,
            Payment.amount,
            Payment.payment_method,
            Booking.reference_number,
            Payment.notes
        ).join(Booking).order_by(Payment.payment_date.desc()).limit(50).all()
        
        # Get payments made to suppliers (only actually paid ones)
        payments_out = db.session.query(
            SupplierPayment.payment_date,
            SupplierPayment.amount,
            SupplierPayment.payment_method,
            Supplier.name.label('supplier_name'),
            SupplierPayment.notes
        ).join(Supplier).filter(
            SupplierPayment.status == 'PAID'
        ).order_by(SupplierPayment.payment_date.desc()).limit(50).all()
        
        # Calculate totals for current month
        current_month_start = date.today().replace(day=1)
        next_month = current_month_start + relativedelta(months=1)
        
        total_in = db.session.query(func.sum(Payment.amount)).filter(
            Payment.payment_date >= current_month_start,
            Payment.payment_date < next_month
        ).scalar() or 0
        
        total_out = db.session.query(func.sum(SupplierPayment.amount)).filter(
            SupplierPayment.payment_date >= current_month_start,
            SupplierPayment.payment_date < next_month,
            SupplierPayment.status == 'PAID'
        ).scalar() or 0
        
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
    return render_template('finance/categories.html', categories=categories)

@finance.route('/categories/new', methods=['GET', 'POST'])
@login_required
def new_category():
    """Create a new expense category"""
    form = ExpenseCategoryForm()
    
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
    
    return render_template('finance/category_form.html', form=form, category=None)

@finance.route('/categories/<int:category_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_category(category_id):
    """Edit an existing expense category"""
    category = ExpenseCategory.query.get_or_404(category_id)
    form = ExpenseCategoryForm(obj=category)
    
    if form.validate_on_submit():
        form.populate_obj(category)
        db.session.commit()
        
        flash('Category updated successfully.', 'success')
        return redirect(url_for('finance.expense_categories'))
    
    return render_template('finance/category_form.html', form=form, category=category)

@finance.route('/reports')
@login_required
def reports():
    """Financial reports landing page"""
    form = FinancialReportFilterForm()
    
    # Default to this month if no date range provided
    today = date.today()
    first_day = date(today.year, today.month, 1)
    last_day = date(today.year, today.month, monthrange(today.year, today.month)[1])
    
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
        
        if request.method == 'GET' or form.date_range.data == 'this_month':
            start_date = date(today.year, today.month, 1)
            end_date = date(today.year, today.month, monthrange(today.year, today.month)[1])
        elif form.date_range.data == 'last_month':
            last_month = today - relativedelta(months=1)
            start_date = date(last_month.year, last_month.month, 1)
            end_date = date(last_month.year, last_month.month, monthrange(last_month.year, last_month.month)[1])
        elif form.date_range.data == 'this_quarter':
            quarter = (today.month - 1) // 3 + 1
            start_date = date(today.year, (quarter - 1) * 3 + 1, 1)
            end_month = quarter * 3
            end_date = date(today.year, end_month, monthrange(today.year, end_month)[1])
        elif form.date_range.data == 'last_quarter':
            last_quarter_end = today - relativedelta(months=((today.month - 1) % 3) + 1)
            last_quarter_start = date(last_quarter_end.year, last_quarter_end.month - 2, 1)
            start_date = last_quarter_start
            end_date = date(last_quarter_end.year, last_quarter_end.month, monthrange(last_quarter_end.year, last_quarter_end.month)[1])
        elif form.date_range.data == 'this_year':
            start_date = date(today.year, 1, 1)
            end_date = date(today.year, 12, 31)
        elif form.date_range.data == 'last_year':
            start_date = date(today.year - 1, 1, 1)
            end_date = date(today.year - 1, 12, 31)
        elif form.date_range.data == 'custom':
            start_date = form.date_from.data
            end_date = form.date_to.data
        else:
            # Default to this month
            start_date = date(today.year, today.month, 1)
            end_date = date(today.year, today.month, monthrange(today.year, today.month)[1])
        
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
    # Get all prepayment lines with supplier info
    prepayment_query = db.session.query(
        SupplierPrepaymentLine,
        SupplierPayment,
        Supplier
    ).join(
        SupplierPayment, SupplierPrepaymentLine.supplier_payment_id == SupplierPayment.id
    ).join(
        Supplier, SupplierPayment.supplier_id == Supplier.id
    ).order_by(Supplier.name)
    
    prepayment_data = prepayment_query.all()
    
    # Group by supplier and calculate totals
    supplier_stats = {}
    for line, payment, supplier in prepayment_data:
        if supplier.id not in supplier_stats:
            supplier_stats[supplier.id] = {
                'supplier': supplier,
                'total_payments': 0,
                'active_services': 0,
                'prepayment_lines': []
            }
        
        supplier_stats[supplier.id]['total_payments'] += line.amount
        supplier_stats[supplier.id]['prepayment_lines'].append({
            'line': line,
            'payment': payment
        })
        
        # Count as active service if not cancelled
        if line.service_item and line.service_item.status != 'CANCELLED':
            supplier_stats[supplier.id]['active_services'] += 1
    
    # Convert to list and include suppliers with no prepayments
    all_suppliers = Supplier.query.order_by(Supplier.name).all()
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
    
    return render_template('finance/suppliers_simple.html', supplier_stats=final_stats)

@finance.route('/new-supplier', methods=['GET', 'POST'])
@login_required
def new_supplier():
    """Create a new supplier"""
    from app.forms.supplier import SupplierForm
    from app.models.supplier import Supplier
    
    form = SupplierForm()
    
    if form.validate_on_submit():
        try:
            # Collect selected service types from checkboxes
            service_types = []
            if form.service_flight.data:
                service_types.append('FLIGHT')
            if form.service_hotel.data:
                service_types.append('HOTEL')
            if form.service_transport.data:
                service_types.append('TRANSPORT')
            if form.service_visa.data:
                service_types.append('VISA')
            if form.service_insurance.data:
                service_types.append('INSURANCE')
            if form.service_tour.data:
                service_types.append('TOUR')
            if form.service_other.data:
                service_types.append('OTHER')
            
            supplier = Supplier(
                name=form.name.data,
                code=form.code.data,
                contact_person=form.contact_person.data,
                email=form.email.data,
                phone=form.phone.data,
                website=form.website.data,
                address=form.address.data,
                city=form.city.data,
                country=form.country.data,
                payment_terms=form.payment_terms.data,
                default_currency=form.default_currency.data,
                bank_name=form.bank_name.data,
                bank_account=form.bank_account.data,
                tax_number=form.tax_number.data,
                notes=form.notes.data
            )
            
            # Set service types using the new method
            supplier.set_service_types(service_types)
            
            db.session.add(supplier)
            db.session.commit()
            
            flash('Supplier created successfully!', 'success')
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
    
    # Order by date descending
    prepayment_lines = query.order_by(SupplierPrepaymentLine.created_at.desc()).all()
    
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

@finance.route('/supplier/<int:supplier_id>')
@login_required
def supplier_details(supplier_id):
    """Show supplier details and payment history"""
    from app.models.supplier import Supplier, SupplierPrepaymentLine
    
    supplier = Supplier.query.get_or_404(supplier_id)
    
    # Get prepayment lines for this supplier
    # This is our new approach - show costs directly from prepayment lines
    prepayment_lines = SupplierPrepaymentLine.query.filter(
        SupplierPrepaymentLine.supplier_name == supplier.name
    ).options(
        db.joinedload(SupplierPrepaymentLine.service_item)
    ).order_by(
        SupplierPrepaymentLine.created_at.desc()
    ).all()
    
    # Also get legacy supplier payments for this supplier
    supplier_payments = SupplierPayment.query.filter_by(
        supplier_id=supplier_id
    ).options(
        db.joinedload(SupplierPayment.prepayment_lines)
    ).all()
    
    # Debug output
    print(f"Loaded {len(prepayment_lines)} supplier prepayment lines for supplier {supplier_id}", file=sys.stderr)
    for line in prepayment_lines:
        booking_ref = "Unknown"
        try:
            # Get booking reference from the booking relationship
            # Booking already imported at top of file
            booking = Booking.query.get(line.booking_id)
            if booking:
                booking_ref = booking.reference_number
        except Exception as e:
            print(f"Error getting booking: {str(e)}", file=sys.stderr)
            
        print(f"Prepayment line ID {line.id}: {line.service_type} for booking {booking_ref}", file=sys.stderr)
    
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