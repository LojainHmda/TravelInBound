"""Assistant tools -- Phase 1.

Every Run Down number the assistant reports comes from the *same view function*
the Run Down page calls. Nothing here re-implements a query: if the page and the
assistant ever disagreed, one of them would be lying and there would be no way
to tell which. Calling the view is what makes that impossible by construction.
"""

from urllib.parse import urlencode

from flask import current_app, url_for
from flask_login import current_user, login_user

from .dates import UnknownDatePhrase, resolve_date_range

__all__ = [
    'CATEGORIES', 'STATUS_CHOICES',
    'search_customers', 'find_inbound_tours',
    'run_down_summary', 'run_down_drilldown',
]


# section key -> view function, rows key, cut-off applicability, grouping field.
# Cut-off exists only for the three services in RUN_DOWN_CUT_OFF_SERVICES;
# guides and Meet & Assist have no cut-off concept at all, which is what
# REQ-3.3's "where applicable" refers to.
CATEGORIES = {
    'accommodation': {
        'view': 'run_down_accommodation_data', 'rows': 'hotels',
        'label': 'Accommodation', 'cut_off': True, 'group_by': 'city',
        'name_field': 'hotel_name', 'filters': ('city', 'hotel_name', 'category'),
    },
    'transportation': {
        'view': 'run_down_transportation_data', 'rows': 'transports',
        'label': 'Transportation', 'cut_off': True, 'group_by': 'company',
        'name_field': 'vehicle', 'filters': ('vehicle', 'company'),
    },
    'guide': {
        'view': 'run_down_guide_data', 'rows': 'guides',
        'label': 'Guides', 'cut_off': False, 'group_by': 'language',
        'name_field': 'guide_name', 'filters': ('language', 'guide_name'),
    },
    'restaurant': {
        'view': 'run_down_restaurant_data', 'rows': 'restaurants',
        'label': 'Restaurant', 'cut_off': True, 'group_by': 'city',
        'name_field': 'restaurant_name', 'filters': ('city', 'restaurant_name'),
    },
    'meet_assist': {
        'view': 'run_down_meet_assist_data', 'rows': 'meet_assists',
        'label': 'Meet & Assist', 'cut_off': False, 'group_by': 'ma_type',
        'name_field': 'ma_name', 'filters': ('ma_name', 'ma_type'),
    },
}

# REQ-4.2 -- the wire values the endpoints expect for ?statuses=
STATUS_CHOICES = {
    'requested': 'REQUESTED',
    'confirmed': 'CONFIRMED',
    'waiting': 'WAITING_LIST',
    'cancelled': 'CANCELLED',
    'all': 'ALL',
}

_CATEGORY_ALIASES = {
    'hotel': 'accommodation', 'hotels': 'accommodation',
    'accommodations': 'accommodation',
    'transport': 'transportation', 'transports': 'transportation',
    'guides': 'guide',
    'restaurants': 'restaurant', 'meals': 'restaurant', 'meal': 'restaurant',
    'meet_and_assist': 'meet_assist', 'meet': 'meet_assist', 'ma': 'meet_assist',
}


def _call_view(view_name, params):
    """Invoke an inbound view function in a nested request context.

    The view reads ``request.args``, so params have to arrive as a real query
    string rather than as arguments. ``login_user`` re-establishes the caller's
    identity inside the nested context -- the views are ``@login_required`` and
    a nested context does not inherit the outer one's user.
    """
    from app.routes import inbound as inbound_routes

    view = getattr(inbound_routes, view_name)
    user = current_user._get_current_object()
    clean = {k: v for k, v in params.items() if v not in (None, '', [])}
    qs = urlencode(clean)

    with current_app.test_request_context('/?' + qs):
        login_user(user)
        response = view()

    # Views return a Response, or a (Response, status) tuple on bad input.
    if isinstance(response, tuple):
        response = response[0]
    return response.get_json()


def _range_from(date_phrase=None, date_from=None, date_to=None):
    """Resolve a period from either a phrase or an explicit pair."""
    if date_from and date_to:
        return resolve_date_range(str(date_from) + ' to ' + str(date_to))
    return resolve_date_range(date_phrase or 'today')


def _name_matches(query, *columns):
    """AND-of-ORs name filter: every word must match at least one column.

    Matching the whole phrase against each column separately is what a naive
    filter does, and it silently returns nothing for "Semba Qatash" when the
    name is split across first_name/last_name -- an empty result that looks
    exactly like "this customer has no files".
    """
    from app.extensions import db

    words = [w for w in (query or '').split() if w]
    if not words:
        return None
    clauses = [
        db.or_(*[col.ilike('%' + word + '%') for col in columns])
        for word in words
    ]
    return db.and_(*clauses)


def _resolve_category(category):
    key = (category or '').strip().lower().replace(' ', '_').replace('-', '_')
    key = _CATEGORY_ALIASES.get(key, key)
    return key, CATEGORIES.get(key)


# --------------------------------------------------------------------------
# REQ-1: customer search
# --------------------------------------------------------------------------

def search_customers(name, limit=10):
    """REQ-1.1 -- find customers by name and return a selectable list."""
    from app.extensions import db
    from app.models.customer import Customer

    name = (name or '').strip()
    if not name:
        return {'ok': False, 'error': 'A customer name is required.', 'customers': []}

    condition = _name_matches(
        name, Customer.first_name, Customer.last_name,
        Customer.company_name, Customer.email,
    )
    rows = (
        Customer.query.filter(condition)
        .order_by(Customer.first_name, Customer.last_name)
        .limit(limit)
        .all()
    )

    customers = [{
        'id': c.id,
        'name': c.name,
        'email': c.email or '',
        'phone': c.phone or '',
        'company_name': c.company_name or '',
        'customer_type': c.customer_type or '',
    } for c in rows]

    return {
        'ok': True,
        'query': name,
        'count': len(customers),
        'customers': customers,
        'selectable': True,
    }


# --------------------------------------------------------------------------
# REQ-2: inbound tours lookup
# --------------------------------------------------------------------------

def find_inbound_tours(customer_name, limit=25):
    """REQ-2.1/2.2 -- inbound tours for a customer, plus the page deep link.

    The list page filters by ``agent`` (a name), which resolves through
    ``InboundRequest.agent`` -- the customer's name when the file is linked to
    one. Matching the FK *and* the free-text contact keeps files that predate
    the customer link from silently vanishing from the answer.
    """
    from app.extensions import db
    from app.models.customer import Customer
    from app.models.inbound import InboundRequest

    customer_name = (customer_name or '').strip()
    if not customer_name:
        return {'ok': False, 'error': 'A customer name is required.', 'tours': []}

    matched = Customer.query.filter(
        _name_matches(customer_name, Customer.first_name,
                      Customer.last_name, Customer.company_name)
    ).all()
    customer_ids = [c.id for c in matched]

    conditions = [_name_matches(customer_name, InboundRequest.contact_name)]
    if customer_ids:
        conditions.append(InboundRequest.customer_id.in_(customer_ids))

    base = InboundRequest.query.filter(db.or_(*conditions))
    # Count before the limit: reporting len(rows) would say "25 tours" for a
    # customer with 90, which reads as a fact rather than as a page size.
    total = base.count()
    rows = (
        base.order_by(InboundRequest.created_at.desc(), InboundRequest.id.desc())
        .limit(limit)
        .all()
    )

    tours = [{
        'id': r.id,
        'request_number': r.request_number,
        'agent': r.agent or '',
        'status': r.status or 'REQUEST',
        'pax': r.pax,
        'from_date': r.from_date.strftime('%Y-%m-%d') if r.from_date else '',
        'to_date': r.to_date.strftime('%Y-%m-%d') if r.to_date else '',
        'no_of_days': r.no_of_days,
        'url': url_for('inbound.view_request', id=r.id),
    } for r in rows]

    # Group like a Run Down drill-down. Location is the grouping there because
    # it is what a service row varies by; a tour file varies by its own status,
    # so that is the equivalent axis here.
    groups, order = {}, []
    for tour in tours:
        label = tour['status'] or 'REQUEST'
        if label not in groups:
            groups[label] = []
            order.append(label)
        groups[label].append(tour)

    # The travel span across the whole matched set, aggregated in SQL so it
    # covers every file rather than only the rows on this page.
    span_from, span_to = base.with_entities(
        db.func.min(InboundRequest.from_date),
        db.func.max(InboundRequest.to_date),
    ).one()

    list_link = url_for('inbound.index') + '?' + urlencode({
        'agent': customer_name, 'search': '1', 'all_files_view': '1',
    })
    if span_from and span_to:
        run_down_link = url_for('inbound.run_down_plan') + '?' + urlencode({
            'date_from': span_from.strftime('%Y-%m-%d'),
            'date_to': span_to.strftime('%Y-%m-%d'),
        })
    else:
        run_down_link = None

    return {
        'ok': True,
        'customer_name': customer_name,
        'count': total,
        'returned': len(tours),
        'truncated': total > len(tours),
        'tours': tours,
        'groups': [
            {'label': lbl, 'count': len(groups[lbl]), 'rows': groups[lbl]}
            for lbl in order
        ],
        'grouped_by': 'status',
        'span': {
            'date_from': span_from.strftime('%Y-%m-%d') if span_from else '',
            'date_to': span_to.strftime('%Y-%m-%d') if span_to else '',
        },
        'list_url': list_link,
        # The Run Down over the customer's travel span is the primary link.
        'navigate_url': run_down_link or list_link,
    }


# --------------------------------------------------------------------------
# REQ-3: run down summary
# --------------------------------------------------------------------------

def run_down_summary(date_phrase=None, date_from=None, date_to=None):
    """REQ-3.2-3.5 -- per-category counts for a resolved period.

    Every category in CATEGORIES is reported, including those with no activity
    (REQ-3.5): a silently omitted category reads as "nothing to worry about"
    when it may equally mean "nobody has entered it yet".
    """
    try:
        period = _range_from(date_phrase, date_from, date_to)
    except UnknownDatePhrase:
        return {
            'ok': False,
            'error': 'Could not work out the period from "%s".' % (date_phrase,),
            'hint': 'Try today, tomorrow, this week, this month, '
                    'or 01/03/2026 to 15/03/2026.',
        }

    params = period.as_params()
    categories, flagged = [], []

    for key, cfg in CATEGORIES.items():
        payload = _call_view(cfg['view'], dict(params)) or {}
        stats = payload.get('stats') or {}

        entry = {
            'key': key,
            'label': cfg['label'],
            'requested': stats.get('requested', 0),
            'confirmed': stats.get('confirmed', 0),
            'waiting': stats.get('waiting', 0),
            'cancelled': stats.get('cancelled', 0),
            'total': payload.get('total', 0),
            'cut_off': stats.get('cut_off') if cfg['cut_off'] else None,
            'cut_off_applicable': cfg['cut_off'],
        }
        entry['has_activity'] = entry['total'] > 0
        categories.append(entry)

        # REQ-3.4 -- a cut-off is a deadline that has entered the window.
        if cfg['cut_off'] and (stats.get('cut_off') or 0) > 0:
            flagged.append({
                'key': key, 'label': cfg['label'], 'cut_off': stats['cut_off'],
            })

    return {
        'ok': True,
        'period': period.to_dict(),
        'categories': categories,
        'flagged': flagged,
        'urgent': bool(flagged),
        'navigate_url': url_for('inbound.run_down_plan') + '?' + urlencode(params),
    }


# --------------------------------------------------------------------------
# REQ-4: run down drill-down
# --------------------------------------------------------------------------

def run_down_drilldown(category, status='requested', date_phrase=None,
                       date_from=None, date_to=None, city=None,
                       hotel_name=None, limit=200):
    """REQ-4.1-4.5 -- rows for one category, filtered and grouped."""
    key, cfg = _resolve_category(category)
    if not cfg:
        return {
            'ok': False,
            'error': 'Unknown category "%s".' % (category,),
            'valid': sorted(CATEGORIES),
        }

    # REQ-4.2 -- default to Requested when the user did not say.
    status_key = (status or 'requested').strip().lower()
    wire_status = STATUS_CHOICES.get(status_key)
    if wire_status is None:
        return {
            'ok': False,
            'error': 'Unknown status "%s".' % (status,),
            'valid': sorted(STATUS_CHOICES),
        }

    try:
        period = _range_from(date_phrase, date_from, date_to)
    except UnknownDatePhrase:
        return {
            'ok': False,
            'error': 'Could not work out the period from "%s".' % (date_phrase,),
            'hint': 'Try today, tomorrow, this week, this month, '
                    'or an explicit range.',
        }

    params = period.as_params()
    params['statuses'] = wire_status

    # REQ-4.3 -- City / Hotel Name, only where the endpoint supports them.
    supported = cfg['filters']
    if city and 'city' in supported:
        params['city'] = city
    if hotel_name:
        for field in ('hotel_name', 'restaurant_name', 'guide_name',
                      'ma_name', 'company'):
            if field in supported:
                params[field] = hotel_name
                break

    payload = _call_view(cfg['view'], params) or {}
    rows = payload.get(cfg['rows']) or []
    if limit:
        rows = rows[:limit]

    # REQ-4.4 -- group by the same field the source page orders by.
    group_by = cfg['group_by']
    groups, order = {}, []
    for row in rows:
        label = (row.get(group_by) or '').strip() or 'Unspecified'
        if label not in groups:
            groups[label] = []
            order.append(label)
        groups[label].append({
            'request_number': row.get('request_number', ''),
            'date': row.get('date', ''),
            'description': row.get('description', ''),
            'name': row.get(cfg['name_field']) or '',
            'pax': row.get('pax'),
            # REQ-4.5 -- the service status and the file's own status are
            # different things and are never collapsed into one field.
            'status': row.get('status', ''),
            'file_status': row.get('file_status', ''),
        })

    return {
        'ok': True,
        'category': key,
        'label': cfg['label'],
        'status_filter': status_key,
        'period': period.to_dict(),
        'grouped_by': group_by,
        'city': city or '',
        'name_filter': hotel_name or '',
        'total_in_range': payload.get('total', 0),
        'matched': payload.get('filtered', len(rows)),
        'returned': len(rows),
        'groups': [
            {'label': lbl, 'count': len(groups[lbl]), 'rows': groups[lbl]}
            for lbl in order
        ],
        'navigate_url': url_for('inbound.run_down_plan') + '?' + urlencode(params),
    }
