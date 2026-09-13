"""Relative date-phrase resolution for the assistant (REQ-3.1).

The Run Down API takes ISO ``%Y-%m-%d`` (see ``_parse_run_down_dates``), while
the Run Down *screen* shows DD/MM/YYYY. Everything here emits ISO so the two
can never be confused -- a swapped day/month silently returns a wrong but
entirely plausible count.
"""

import re
from calendar import monthrange
from datetime import date, datetime, timedelta

__all__ = ['resolve_date_range', 'DateRange', 'UnknownDatePhrase']


class UnknownDatePhrase(ValueError):
    """Raised when a phrase cannot be mapped to a period."""


class DateRange:
    __slots__ = ('date_from', 'date_to', 'label')

    def __init__(self, date_from, date_to, label):
        if date_from > date_to:
            date_from, date_to = date_to, date_from
        self.date_from = date_from
        self.date_to = date_to
        self.label = label

    def as_params(self):
        return {
            'date_from': self.date_from.strftime('%Y-%m-%d'),
            'date_to': self.date_to.strftime('%Y-%m-%d'),
        }

    def to_dict(self):
        d = self.as_params()
        d['label'] = self.label
        return d

    def __repr__(self):
        return f'<DateRange {self.date_from}..{self.date_to} {self.label!r}>'


# Accepted explicit formats. ISO first: it is what the API speaks. The
# day-first forms are what a user types, and are unambiguous only when the
# day exceeds 12 -- so DD/MM is tried before MM/DD to match the UI's own
# reading rather than US convention.
_EXPLICIT_FORMATS = ('%Y-%m-%d', '%d/%m/%Y', '%d-%m-%Y', '%d/%m/%y', '%d.%m.%Y')

_WEEKDAYS = {
    'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3,
    'friday': 4, 'saturday': 5, 'sunday': 6,
}

_MONTH_NAMES = (
    'january', 'february', 'march', 'april', 'may', 'june',
    'july', 'august', 'september', 'october', 'november', 'december',
)
# Full names and the usual three-letter abbreviations ("sept" included).
_MONTHS = {name: i for i, name in enumerate(_MONTH_NAMES, start=1)}
_MONTHS.update({name[:3]: i for i, name in enumerate(_MONTH_NAMES, start=1)})
_MONTHS['sept'] = 9


def _parse_explicit(text):
    text = text.strip()
    for fmt in _EXPLICIT_FORMATS:
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    return None


def _week_bounds(anchor):
    """Monday-Sunday, matching how operations talk about a working week."""
    start = anchor - timedelta(days=anchor.weekday())
    return start, start + timedelta(days=6)


def _month_bounds(anchor):
    start = anchor.replace(day=1)
    return start, anchor.replace(day=monthrange(anchor.year, anchor.month)[1])


def resolve_date_range(phrase, today=None):
    """Map a natural date phrase to an inclusive ISO range.

    Returns a :class:`DateRange`. Raises :class:`UnknownDatePhrase` when the
    phrase carries no resolvable period -- the caller should ask rather than
    quietly defaulting to today, which would answer a different question than
    the one asked.
    """
    today = today or date.today()
    if not phrase or not str(phrase).strip():
        raise UnknownDatePhrase('empty date phrase')

    text = ' '.join(str(phrase).lower().split())
    text = text.replace('&', ' and ').strip(' ?.!')

    # --- explicit ranges: "01/03/2026 to 15/03/2026", "2026-03-01..2026-03-15"
    range_sep = re.split(r'\s+(?:to|until|till|through|thru)\s+|\.\.|\s+-\s+', text, maxsplit=1)
    if len(range_sep) == 2:
        a, b = _parse_explicit(range_sep[0]), _parse_explicit(range_sep[1])
        if a and b:
            return DateRange(a, b, f'{a:%d/%m/%Y} - {b:%d/%m/%Y}')

    # --- a single explicit date means that one day
    single = _parse_explicit(text)
    if single:
        return DateRange(single, single, f'{single:%d/%m/%Y}')

    if text in ('today', 'toady', 'this day'):
        return DateRange(today, today, 'today')
    if text == 'tomorrow':
        d = today + timedelta(days=1)
        return DateRange(d, d, 'tomorrow')
    if text == 'yesterday':
        d = today - timedelta(days=1)
        return DateRange(d, d, 'yesterday')

    if text in ('this week', 'the week', 'current week', 'week'):
        s, e = _week_bounds(today)
        return DateRange(s, e, 'this week')
    if text in ('next week', 'the coming week', 'coming week'):
        s, e = _week_bounds(today + timedelta(days=7))
        return DateRange(s, e, 'next week')
    if text in ('last week', 'previous week', 'past week'):
        s, e = _week_bounds(today - timedelta(days=7))
        return DateRange(s, e, 'last week')

    if text in ('this month', 'the month', 'current month', 'month'):
        s, e = _month_bounds(today)
        return DateRange(s, e, 'this month')
    if text in ('next month', 'the coming month', 'coming month'):
        nxt = (today.replace(day=1) + timedelta(days=32)).replace(day=1)
        s, e = _month_bounds(nxt)
        return DateRange(s, e, 'next month')
    if text in ('last month', 'previous month', 'past month'):
        prev = today.replace(day=1) - timedelta(days=1)
        s, e = _month_bounds(prev)
        return DateRange(s, e, 'last month')

    # "next 7 days" / "coming 3 days" / "last 14 days"
    m = re.fullmatch(r'(?:the\s+)?(next|coming|last|past|previous)\s+(\d{1,3})\s+days?', text)
    if m:
        direction, n = m.group(1), int(m.group(2))
        if n == 0:
            raise UnknownDatePhrase(phrase)
        if direction in ('next', 'coming'):
            return DateRange(today, today + timedelta(days=n - 1), f'next {n} days')
        return DateRange(today - timedelta(days=n - 1), today, f'last {n} days')

    # "may", "may 2026", "march 2027" -> that whole calendar month. Without a
    # year, pick the upcoming occurrence: operations ask about work ahead.
    m = re.fullmatch(r'([a-z]+)(?:\s+(\d{4}))?', text)
    if m and m.group(1) in _MONTHS:
        month = _MONTHS[m.group(1)]
        if m.group(2):
            year = int(m.group(2))
        else:
            year = today.year if month >= today.month else today.year + 1
        anchor = date(year, month, 1)
        s, e = _month_bounds(anchor)
        return DateRange(s, e, f'{anchor:%B %Y}')

    # a bare weekday name -> the next occurrence, today counting as itself
    if text in _WEEKDAYS:
        delta = (_WEEKDAYS[text] - today.weekday()) % 7
        d = today + timedelta(days=delta)
        return DateRange(d, d, text)

    raise UnknownDatePhrase(phrase)
