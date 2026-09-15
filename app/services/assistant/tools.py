"""Assistant tools -- Phase 1.

Every Run Down number the assistant reports comes from the *same view function*
the Run Down page calls. Nothing here re-implements a query: if the page and the
assistant ever disagreed, one of them would be lying and there would be no way
to tell which. Calling the view is what makes that impossible by construction.
"""

from calendar import monthrange
from datetime import date
from urllib.parse import urlencode

from flask import current_app, url_for
from flask_login import current_user, login_user

from .dates import MissingPeriod, UnknownDatePhrase, resolve_date_range

__all__ = [
    'CATEGORIES', 'STATUS_CHOICES', 'FILE_STATUS_CHOICES',
    'search_customers', 'find_inbound_tours',
    'run_down_summary', 'run_down_drilldown', 'run_down_cut_off',
    'list_inbound_files', 'find_file_by_number', 'search_suppliers',
    'list_customers',
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

# A tour FILE's status is the three-state system on the inbound list
# (Request / Confirmed / Invoiced). These are NOT the service booking
# statuses in STATUS_CHOICES below -- a file is Confirmed while the guide
# booking on it is still Requested, so collapsing the two vocabularies
# would answer a different question than the one asked.
FILE_STATUS_CHOICES = {
    'request': 'REQUEST', 'requested': 'REQUEST', 'new': 'REQUEST',
    'confirmed': 'CONFIRMED', 'confirm': 'CONFIRMED',
    'invoiced': 'INVOICED', 'invoice': 'INVOICED',
    'all': 'ALL',
}

# REQ-4.2 -- the wire values the endpoints expect for ?statuses=
STATUS_CHOICES = {
    'requested': 'REQUESTED',
    'confirmed': 'CONFIRMED',
    'waiting': 'WAITING_LIST',
    'cancelled': 'CANCELLED',
    'all': 'ALL',
}

# The categories that have a cut-off at all, derived from CATEGORIES rather
# than restated: Guides and Meet & Assist have no cut_off_date column, and a
# second hand-written list of the other three would be free to drift from it.
CUT_OFF_CATEGORIES = tuple(k for k, c in CATEGORIES.items() if c['cut_off'])


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


def _list_query(params, all_files_view=False):
    """Build the inbound list page's own query with ``params`` as its args.

    ``_build_inbound_list_query`` reads ``request.args``, so the filters have
    to arrive as a real query string. Reusing it rather than rewriting the
    filters is what keeps the assistant's list and the page's list from ever
    disagreeing about which files exist.
    """
    from app.routes import inbound as inbound_routes

    clean = {k: v for k, v in params.items() if v not in (None, '', [])}
    with current_app.test_request_context('/?' + urlencode(clean)):
        query, _queue = inbound_routes._build_inbound_list_query(all_files_view)
    return query


def _overlaps(query, period):
    """Narrow to files whose travel dates overlap the period.

    Overlap, not start-date: a tour running 28 Aug to 3 Sep belongs to both
    months, and testing the start alone drops it from one of them. Same test
    the list page's year/month filter uses.
    """
    from app.models.inbound import InboundRequest

    return query.filter(
        InboundRequest.from_date <= period.date_to,
        InboundRequest.to_date >= period.date_from,
    )


def _period_url_filters(period):
    """Express ``period`` as the list page's own filter args, when it can be.

    ``_build_inbound_list_query`` filters dates by whole calendar month or
    whole year only -- ``filter_year`` with an optional ``filter_month``. It
    has no from/to arguments, and adding some is not an option: that builder
    is shared with the list page, Export and Print, so widening it would
    change what people who never open the assistant see.

    A period therefore either round-trips exactly or not at all. Last two
    months, a custom span, anything crossing a month or year boundary cannot
    be carried in the URL, and the caller has to say the page is unfiltered
    rather than hand over a link that quietly shows a different set of files.

    Returns ``(params, exact)``.
    """
    if period is None:
        return {}, True

    start, end = period.date_from, period.date_to
    if start.year != end.year:
        return {}, False

    # Whole year first: January-December would otherwise fail the single-month
    # test and be reported as inexpressible when the page can express it.
    if start == date(start.year, 1, 1) and end == date(start.year, 12, 31):
        return {'filter_year': str(start.year)}, True

    if (start.month == end.month
            and start.day == 1
            and end.day == monthrange(start.year, start.month)[1]):
        return {'filter_year': str(start.year),
                'filter_month': str(start.month)}, True

    return {}, False


def _file_list_link(params, period=None, page_includes_deleted=False):
    """Build the file-list link for a tool result.

    Destination is ``/inbound/all-files`` rather than ``/inbound/``: that is
    the view with the Status column and the Year/Month filters, and the only
    one for which the all-files flag is read at all. The index derives that
    flag from its own path, so ``all_files_view=1`` in the query string did
    nothing to the page it was sent to -- it only rode along into the Export
    and Print links, which *do* read it, and widened those.

    ``page_includes_deleted`` says the page will show Deleted-queue files that
    the count beside it left out: the all-files view drops the Deleted-queue
    exclusion and no URL argument puts it back.

    Returns the fields to merge into the tool result.
    """
    date_params, period_exact = _period_url_filters(period)

    # /all-files renders no table until a search has been submitted.
    args = {'search': '1'}
    args.update({k: v for k, v in params.items() if v not in (None, '', [])})
    args.update(date_params)

    notes = []
    if not period_exact:
        notes.append(
            'The list page filters by whole month or whole year only, so this '
            'link could NOT be filtered to %s. It opens the unfiltered list: '
            'tell the user the page is not filtered to their period.'
            % (period.label if period is not None else 'the period',)
        )
    if page_includes_deleted:
        notes.append(
            'The list page also shows files in the Deleted queue, which this '
            'count excludes, so it may show more rows than the count.'
        )

    return {
        'navigate_url': (url_for('main.inbound_all_files_list')
                         + '?' + urlencode(args)),
        'list_url_period_applied': bool(period is None or period_exact),
        'list_url_note': ' '.join(notes) or None,
    }


# Relative-period words in the three scripts the assistant is asked in. Only
# ever used to answer "was a period mentioned at all", never to resolve one.
_PERIOD_WORDS = (
    'today', 'tonight', 'tomorrow', 'yesterday', 'week', 'month', 'year',
    'quarter', 'season', 'now', 'current', 'next', 'last', 'coming', 'past',
    'recent', 'upcoming', 'previous', 'this', 'ytd',
    # Latin-script Arabic
    'shahr', 'shaher', 'esboo', 'usbu', 'sana', 'yom', 'bukra', 'bokra',
    'embare', 'jay', 'jaye', 'madi',
    # Arabic script
    '\u0627\u0644\u064a\u0648\u0645', '\u0628\u0643\u0631\u0627',
    '\u063a\u062f\u0627', '\u0627\u0645\u0633',
    '\u0627\u0633\u0628\u0648\u0639', '\u0634\u0647\u0631',
    '\u0633\u0646\u0629', '\u0645\u0648\u0633\u0645',
    '\u0627\u0644\u0642\u0627\u062f\u0645',
    '\u0627\u0644\u0645\u0627\u0636\u064a',
    '\u0627\u0644\u062c\u0627\u064a', '\u0647\u0627\u0644',
)


def _period_mentioned(text):
    """Did this message mention a period AT ALL?

    Answers "is there anything date-shaped here", never "which period is it".
    Deliberately lopsided: a false yes only lets the period through exactly as
    before, while a false no would refuse a question the user really did ask,
    so anything remotely date-like counts as yes.

    It exists to catch a period the MODEL supplied that the user did not --
    carried over from an earlier turn. An inherited period answers a different
    question than the one asked, and reads exactly as confident as a correct
    one, which is what makes it worth refusing rather than guessing at.
    """
    from .dates import _ARABIC_DIGITS, _ARABIC_MONTHS, _MONTHS, _fold_arabic

    if not text:
        # Nothing to check against: let the caller through rather than block.
        return True

    raw = str(text)
    if any(ch.isdigit() for ch in raw):
        return True
    if any(ord(ch) in _ARABIC_DIGITS for ch in raw):
        return True

    lowered = raw.lower()
    if any(word in lowered for word in _PERIOD_WORDS):
        return True
    if any(name in lowered for name in _MONTHS):
        return True

    folded = _fold_arabic(raw)
    if any(name in folded for name in _ARABIC_MONTHS):
        return True

    return False


def _ask_for_period():
    """The one shape every tool uses when no period was given."""
    return {
        'ok': False,
        'error': 'Which period should I look at?',
        'needs_period': True,
        'hint': 'For example September, this week, last two months, '
                'or 01/03/2026 to 15/03/2026.',
    }


def _file_row(r):
    """One inbound file as the assistant reports it: number, agent, dates, status."""
    return {
        'id': r.id,
        'request_number': r.request_number,
        'agent': r.agent or '',
        'from_date': r.from_date.strftime('%Y-%m-%d') if r.from_date else '',
        'to_date': r.to_date.strftime('%Y-%m-%d') if r.to_date else '',
        'status': r.status or 'REQUEST',
        'url': url_for('inbound.view_request', id=r.id),
    }


def _range_from(date_phrase=None, date_from=None, date_to=None):
    """Resolve a period from either a phrase or an explicit pair.

    No phrase raises :class:`MissingPeriod` rather than standing in 'today'.
    A substituted period silently answers about a different window than the
    one asked about, and an empty result then reads as "nothing booked"
    instead of "you never said when".
    """
    if date_from and date_to:
        return resolve_date_range(str(date_from) + ' to ' + str(date_to))
    return resolve_date_range(date_phrase)


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

def find_inbound_tours(customer_name, date_phrase=None, status=None,
                       latest=False, limit=25):
    """REQ-2.1/2.2 -- inbound tours for a customer, plus the page deep link.

    The list page filters by ``agent`` (a name), which resolves through
    ``InboundRequest.agent`` -- the customer's name when the file is linked to
    one. Matching the FK *and* the free-text contact keeps files that predate
    the customer link from silently vanishing from the answer.

    ``date_phrase`` narrows to files whose travel dates *overlap* the period,
    the same test the list page's year/month filter uses -- a tour running
    28 Aug to 3 Sep belongs to both months, and asking by start date alone
    would drop it from one of them.

    ``latest`` returns only the most recently created file. Newest-created is
    what "the last file" means here: the one entered most recently, not the
    one travelling furthest out.

    ``status`` narrows to one file state. The concrete values that map to a
    state are read back through ``_map_status_for_filter`` rather than listed
    here: INVOICE, COMPLETED and INVOICED all mean Invoiced, and a second
    copy of that list here would drift from the list page's.
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

    status_key = (status or 'all').strip().lower()
    wire_status = FILE_STATUS_CHOICES.get(status_key)
    if wire_status is None:
        return {
            'ok': False,
            'error': 'Unknown file status "%s".' % (status,),
            'valid': sorted(set(FILE_STATUS_CHOICES.values())),
            'tours': [],
        }

    conditions = [_name_matches(customer_name, InboundRequest.contact_name)]
    if customer_ids:
        conditions.append(InboundRequest.customer_id.in_(customer_ids))

    base = InboundRequest.query.filter(db.or_(*conditions))

    if wire_status != 'ALL':
        from app.routes.inbound import _map_status_for_filter
        wanted = [
            value for (value,) in db.session.query(InboundRequest.status).distinct()
            if _map_status_for_filter(value) == wire_status
        ]
        base = base.filter(InboundRequest.status.in_(wanted or ['__none__']))

    period = None
    if date_phrase:
        try:
            period = resolve_date_range(date_phrase)
        except UnknownDatePhrase:
            return {
                'ok': False,
                'error': 'Could not work out the period from "%s".' % (date_phrase,),
                'hint': 'Try September, last two months, this week, '
                        'or 01/03/2026 to 15/03/2026.',
                'tours': [],
            }
        base = base.filter(
            InboundRequest.from_date <= period.date_to,
            InboundRequest.to_date >= period.date_from,
        )

    # Count before the limit: reporting len(rows) would say "25 tours" for a
    # customer with 90, which reads as a fact rather than as a page size.
    total = base.count()
    rows = (
        base.order_by(InboundRequest.created_at.desc(), InboundRequest.id.desc())
        .limit(1 if latest else limit)
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

    # The travel span has to describe the rows actually shown. Aggregating
    # over the whole matched set is right for a full list, but on a
    # 'latest' result it printed the span of every file the customer ever
    # had beside a single file's row -- two different facts, one line.
    if latest:
        dates = [d for r in rows for d in (r.from_date, r.to_date) if d]
        span_from, span_to = (min(dates), max(dates)) if dates else (None, None)
    else:
        span_from, span_to = base.with_entities(
            db.func.min(InboundRequest.from_date),
            db.func.max(InboundRequest.to_date),
        ).one()

    list_params = {'agent': customer_name}
    if wire_status != 'ALL':
        list_params['status'] = wire_status
    # This tool's own query never excluded the Deleted queue either, so the
    # all-files page is the matching scope here, not a widening.
    list_fields = _file_list_link(list_params, period)
    list_link = list_fields['navigate_url']
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
        # This list is one customer's files only. An empty result means
        # "not among this customer's files", never "no such file".
        'searched_scope': "only %s's files" % (customer_name,),
        'count': total,
        'returned': len(tours),
        # 'latest' is one deliberately chosen row, not a truncated page, so
        # it must not be announced as "showing 1 of 13".
        'latest': bool(latest),
        'period': period.to_dict() if period else None,
        'status_filter': status_key,
        'truncated': (not latest) and total > len(tours),
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
        # The question was about this customer's files, so the file list is
        # the primary link. A Run Down spanning every file they ever had
        # answers a different question.
        'navigate_url': list_link or run_down_link,
        'list_url_period_applied': list_fields['list_url_period_applied'],
        'list_url_note': list_fields['list_url_note'],
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
    except MissingPeriod:
        return {
            'ok': False,
            'error': 'Which period should I look at?',
            'needs_period': True,
            'hint': 'For example today, this week, September, '
                    'last two months, or 01/03/2026 to 15/03/2026.',
        }
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

def run_down_drilldown(category, status='all', date_phrase=None,
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

    # Default to every status when the user did not name one. This reverses
    # REQ-4.2's "default to Requested": defaulting to one status hid rows
    # that exist (a guide with a Requested and a Confirmed file in the same
    # month showed only the Requested one), and a partial answer is
    # indistinguishable from a complete one. A status filter is applied only
    # when the user actually names a status.
    status_key = (status or 'all').strip().lower()
    wire_status = STATUS_CHOICES.get(status_key)
    if wire_status is None:
        return {
            'ok': False,
            'error': 'Unknown status "%s".' % (status,),
            'valid': sorted(STATUS_CHOICES),
        }

    try:
        period = _range_from(date_phrase, date_from, date_to)
    except MissingPeriod:
        return {
            'ok': False,
            'error': 'Which period should I look at?',
            'needs_period': True,
            'hint': 'For example today, this week, September, '
                    'last two months, or 01/03/2026 to 15/03/2026.',
        }
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
            # Carried through so the file number can be a link, the same
            # way find_inbound_tours rows already are.
            'url': row.get('view_url', ''),
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


# --------------------------------------------------------------------------
# Cut-off -- deadlines that fall inside the period
# --------------------------------------------------------------------------

def run_down_cut_off(date_phrase=None, date_from=None, date_to=None,
                     category=None, files_only=False, limit=200,
                     asked_in=None):
    """Services whose cut-off DEADLINE falls inside the period.

    Selected on ``cut_off_date``, never on the service date. A cut-off is a
    deadline to act before, so a hotel checking in on 2 October with a 28
    September deadline belongs to September. That is also the only selection
    that can agree with the Run Down card: this reads the very rows that
    page's cut-off table reads, through ``run_down_cut_off_data``, instead of
    re-deriving them from a section query keyed on the service date. The
    section queries filter on check-in/service date, so filtering their rows
    for a cut-off would answer a different question and return a different
    set -- which is exactly how the summary and the drill-down came to
    contradict each other.

    Cut-off exists only for Accommodation, Transportation and Restaurant.
    Guides and Meet & Assist have no ``cut_off_date`` column at all, so asking
    for their cut-offs is answered as "does not apply", never as "none":
    reporting zero would state an absence the data cannot establish.
    """
    key, cfg = None, None
    if category:
        key, cfg = _resolve_category(category)
        if not cfg:
            return {
                'ok': False,
                'error': 'Unknown category "%s".' % (category,),
                'valid': sorted(CATEGORIES),
            }
        if not cfg['cut_off']:
            return {
                'ok': False,
                'error': '%s has no cut-off at all.' % (cfg['label'],),
                # Not a count of zero. The caller must say the category has no
                # cut-off concept, and must not report it as having none due.
                'not_applicable': True,
                'category': key,
                'label': cfg['label'],
                'cut_off_categories': [CATEGORIES[k]['label']
                                       for k in CUT_OFF_CATEGORIES],
            }

    # A period the user did not give in THIS message is not a period they
    # gave. Answering September because September was the last question is
    # silent context inheritance: the answer looks exactly as authoritative
    # as a correct one, and "no restaurant cut-offs" is then true of a month
    # nobody asked about.
    if date_phrase and asked_in is not None and not _period_mentioned(asked_in):
        return {
            'ok': False,
            'error': 'Which period should I look at?',
            'needs_period': True,
            'inherited_period_blocked': True,
            'attempted_period': date_phrase,
            'hint': 'They named no period in this message, so the period was '
                    'not carried over from the previous one. Ask which month '
                    'or date range they mean -- do not answer for "%s".'
                    % (date_phrase,),
        }

    try:
        period = _range_from(date_phrase, date_from, date_to)
    except MissingPeriod:
        return {
            'ok': False,
            'error': 'Which period should I look at?',
            'needs_period': True,
            'hint': 'For example today, this week, September, '
                    'last two months, or 01/03/2026 to 15/03/2026.',
        }
    except UnknownDatePhrase:
        return {
            'ok': False,
            'error': 'Could not work out the period from "%s".' % (date_phrase,),
            'hint': 'Try today, tomorrow, this week, this month, '
                    'or 01/03/2026 to 15/03/2026.',
        }

    scope_keys = [key] if key else list(CUT_OFF_CATEGORIES)
    params = period.as_params()

    categories, flagged, files = [], [], []
    for cat_key in scope_keys:
        cat_cfg = CATEGORIES[cat_key]
        payload = _call_view('run_down_cut_off_data',
                             dict(params, service=cat_key)) or {}
        rows = payload.get('rows') or []
        count = payload.get('total', len(rows))

        categories.append({'key': cat_key, 'label': cat_cfg['label'],
                           'count': count})
        if count:
            flagged.append({'key': cat_key, 'label': cat_cfg['label'],
                            'count': count})

        for row in rows:
            files.append({
                'request_number': row.get('request_number', ''),
                # Same view_url the Run Down cut-off table links to, so the
                # file number opens the file rather than being inert text.
                'url': row.get('view_url', ''),
                'category': cat_key,
                'category_label': cat_cfg['label'],
                'name': row.get('name') or '',
                'cut_off_date': row.get('cut_off_date', ''),
                'cut_off_date_display': row.get('cut_off_date_display', ''),
                'service_date_display': row.get('date_from_display', ''),
                # Both ends of the service, already dashed by the endpoint
                # when a record has no end date.
                'service_date_to_display': row.get('date_to_display', ''),
                'status': row.get('status', ''),
                'file_status': row.get('file_status', ''),
                'pax': row.get('pax'),
            })

    # Soonest deadline first, the order the Run Down cut-off table uses, held
    # across categories so the most urgent row is first whatever it belongs to.
    files.sort(key=lambda f: (f['cut_off_date'], f['category_label'],
                              f['request_number']))

    total = len(files)
    if limit:
        files = files[:limit]

    # The Run Down's cut-off table is hidden until a card's cut-off count is
    # clicked, so a bare link lands at the top of the page with the table
    # still collapsed. `cut_off` names the service to open, and run_down.js
    # opens and scrolls to it -- through showCutOffTable, the same function
    # the card click calls, so there is no second way to open that table.
    nav_params = dict(params)
    if flagged:
        nav_params['cut_off'] = flagged[0]['key']

    return {
        'ok': True,
        'period': period.to_dict(),
        'scope': key or 'all',
        'scope_label': cfg['label'] if cfg else 'all categories with a cut-off',
        # False -> show the counts and then the files; True -> the files alone.
        'files_only': bool(files_only),
        'categories': categories,
        'flagged': flagged,
        'urgent': bool(flagged),
        'count': total,
        'returned': len(files),
        'truncated': total > len(files),
        'files': files,
        'navigate_url': (url_for('inbound.run_down_plan')
                         + '?' + urlencode(nav_params)),
    }


# --------------------------------------------------------------------------
# General lists -- no customer required
# --------------------------------------------------------------------------

def list_inbound_files(date_phrase=None, agent=None, status=None,
                       deleted=False, limit=100):
    """Inbound files in a period, for everyone or for one agent.

    A period is required. "All files" with no period would return the whole
    system, and the answer to a question nobody asked is indistinguishable
    from the answer to the one they did ask.

    Deleted files are excluded unless ``deleted`` is set, matching the list
    page: the Deleted queue is a separate place there, not part of the list.
    """
    if not date_phrase:
        return _ask_for_period()
    try:
        period = resolve_date_range(date_phrase)
    except UnknownDatePhrase:
        return {
            'ok': False,
            'error': 'Could not work out the period from "%s".' % (date_phrase,),
            'hint': 'Try September, last two months, this week, '
                    'or 01/03/2026 to 15/03/2026.',
            'files': [],
        }

    status_key = (status or 'all').strip().lower()
    wire_status = FILE_STATUS_CHOICES.get(status_key)
    if wire_status is None:
        return {
            'ok': False,
            'error': 'Unknown file status "%s".' % (status,),
            'valid': sorted(set(FILE_STATUS_CHOICES.values())),
            'files': [],
        }

    from app.models.inbound import InboundRequest

    params = {'agent': agent}
    if wire_status != 'ALL':
        params['status'] = wire_status
    if deleted:
        params['queue'] = 'deleted'

    query = _overlaps(_list_query(params, all_files_view=bool(deleted)), period)
    total = query.count()
    rows = (
        query.order_by(InboundRequest.from_date.asc(), InboundRequest.id.asc())
        .limit(limit)
        .all()
    )
    files = [_file_row(r) for r in rows]

    by_status = {}
    for f in files:
        by_status[f['status']] = by_status.get(f['status'], 0) + 1

    list_params = {}
    if agent:
        list_params['agent'] = agent
    if wire_status != 'ALL':
        list_params['status'] = wire_status
    if deleted:
        list_params['queue'] = 'deleted'
    # A status filter, and the Deleted queue itself, each re-exclude the
    # Deleted queue on the page. Plain "all files" has nothing that does.
    list_fields = _file_list_link(
        list_params, period,
        page_includes_deleted=(wire_status == 'ALL' and not deleted),
    )

    return {
        'ok': True,
        'period': period.to_dict(),
        'agent_filter': agent or '',
        'status_filter': status_key,
        'deleted': bool(deleted),
        'count': total,
        'returned': len(files),
        'truncated': total > len(files),
        'by_status': by_status,
        'files': files,
        **list_fields,
    }


def list_customers(date_phrase=None, limit=100):
    """Customers with at least one file whose travel dates fall in the period.

    Counted from the files themselves rather than from the customer table: a
    customer with no file in the period was not dealt with in that period, and
    listing them would answer a different question.
    """
    if not date_phrase:
        return _ask_for_period()
    try:
        period = resolve_date_range(date_phrase)
    except UnknownDatePhrase:
        return {
            'ok': False,
            'error': 'Could not work out the period from "%s".' % (date_phrase,),
            'hint': 'Try September, last two months, or 01/03/2026 to 15/03/2026.',
            'customers': [],
        }

    from app.models.inbound import InboundRequest

    rows = _overlaps(_list_query({}), period).all()

    # InboundRequest.agent is a property (customer name, else contact name), so
    # the grouping happens here rather than in SQL.
    grouped = {}
    for r in rows:
        name = (r.agent or '').strip() or 'TBA'
        entry = grouped.setdefault(name, {
            'name': name,
            'customer_id': r.customer_id,
            'files': 0,
            'file_numbers': [],
        })
        entry['files'] += 1
        entry['file_numbers'].append(r.request_number)
        if entry['customer_id'] is None and r.customer_id:
            entry['customer_id'] = r.customer_id

    customers = sorted(grouped.values(), key=lambda c: (-c['files'], c['name'].lower()))
    for c in customers:
        c['url'] = (url_for('customer.view_customer', customer_id=c['customer_id'])
                    if c['customer_id'] else
                    _file_list_link({'agent': c['name']}, period)['navigate_url'])

    return {
        'ok': True,
        'period': period.to_dict(),
        'count': len(customers),
        'returned': min(len(customers), limit),
        'truncated': len(customers) > limit,
        'total_files': len(rows),
        'customers': customers[:limit],
        # Counted through _list_query with all_files_view False, so the count
        # leaves the Deleted queue out where the all-files page puts it back.
        **_file_list_link({}, period, page_includes_deleted=True),
    }


def find_file_by_number(number):
    """One file by its number, searched across the WHOLE system.

    Never scoped to a selected customer. A bare file number is its own
    question, and answering "no such file" after looking in one customer's
    files is a false negative that reads exactly like a true one.
    """
    from app.models.inbound import InboundRequest

    number = str(number or '').strip()
    if not number:
        return {'ok': False, 'error': 'A file number is required.', 'files': []}

    exact = InboundRequest.query.filter(
        InboundRequest.request_number == number).all()
    rows = exact or InboundRequest.query.filter(
        InboundRequest.request_number.contains(number)).limit(25).all()

    files = [_file_row(r) for r in rows]
    return {
        'ok': True,
        'query': number,
        'exact': bool(exact),
        # Named so the reply can say what was searched. "Not found" is only
        # honest when the scope was everything.
        'searched_scope': 'every inbound file in the system',
        'count': len(files),
        'files': files,
        # The scope here is deliberately everything, so the all-files view --
        # Deleted queue included -- is the right destination, not a widening.
        'navigate_url': files[0]['url'] if len(files) == 1 else (
            _file_list_link({'request_number': number})['navigate_url']),
    }


# --------------------------------------------------------------------------
# Suppliers -- guides, hotels, restaurants, transport, meet & assist, airlines
# --------------------------------------------------------------------------

# The assistant's words -> the hub page's type keys. The page map is the
# authority on which supplier_type values belong to each; this only translates
# what a person would say into the key that map is filed under.
SUPPLIER_TYPE_ALIASES = {
    'guide': 'guides', 'guides': 'guides',
    'hotel': 'accommodation', 'hotels': 'accommodation',
    'accommodation': 'accommodation',
    'transport': 'transportation', 'transportation': 'transportation',
    'transfer': 'transportation', 'bus': 'transportation',
    'restaurant': 'restaurant', 'restaurants': 'restaurant', 'meal': 'restaurant',
    'meet_assist': 'meet-assist', 'meet-assist': 'meet-assist',
    'meet and assist': 'meet-assist', 'ma': 'meet-assist',
    'airline': 'airline', 'airlines': 'airline', 'flight': 'airline',
    'other': 'others', 'others': 'others',
}


def search_suppliers(name=None, supplier_type=None, limit=25):
    """Find suppliers by name and/or type.

    Guides, hotels, restaurants, transport companies, Meet & Assist providers
    and airlines are SUPPLIERS, not customers -- searching the customer table
    for a guide's name correctly returns nothing, which reads as "no such
    person" when the person is right there under a different table.
    """
    from app.routes.finance import _SUPPLIER_TYPE_PAGE_MAP, _query_suppliers_for_type

    name = (name or '').strip()
    type_key = None
    if supplier_type:
        raw = str(supplier_type).strip().lower().replace('_', ' ')
        type_key = SUPPLIER_TYPE_ALIASES.get(raw) or SUPPLIER_TYPE_ALIASES.get(
            raw.replace(' ', '_'))
        if type_key is None:
            return {
                'ok': False,
                'error': 'Unknown supplier type "%s".' % (supplier_type,),
                'valid': sorted(set(SUPPLIER_TYPE_ALIASES.values())),
                'suppliers': [],
            }

    keys = [type_key] if type_key else list(_SUPPLIER_TYPE_PAGE_MAP)
    seen, suppliers = set(), []
    for key in keys:
        config, rows = _query_suppliers_for_type(key, name)
        for s in rows or []:
            if s.id in seen:
                continue
            seen.add(s.id)
            suppliers.append({
                'id': s.id,
                'name': s.name,
                'type': s.supplier_type or '',
                'type_label': config['label'] if config else '',
                'city': s.city or '',
                'phone': s.phone or '',
                'url': url_for('finance.supplier_details', supplier_id=s.id),
            })

    suppliers.sort(key=lambda x: x['name'].lower())
    return {
        'ok': True,
        'query': name,
        'type_filter': type_key or 'all',
        'searched_scope': ('every %s supplier' % _SUPPLIER_TYPE_PAGE_MAP[type_key]['label']
                           if type_key else 'every supplier of every type'),
        'count': len(suppliers),
        'returned': min(len(suppliers), limit),
        'truncated': len(suppliers) > limit,
        'suppliers': suppliers[:limit],
    }
