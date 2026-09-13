"""Relative date-phrase resolution for the assistant (REQ-3.1).

The Run Down API takes ISO ``%Y-%m-%d`` (see ``_parse_run_down_dates``), while
the Run Down *screen* shows DD/MM/YYYY. Everything here emits ISO so the two
can never be confused -- a swapped day/month silently returns a wrong but
entirely plausible count.
"""

import re
from calendar import monthrange
from difflib import get_close_matches
from datetime import date, datetime, timedelta

__all__ = ['resolve_date_range', 'DateRange', 'UnknownDatePhrase',
           'MissingPeriod']


class UnknownDatePhrase(ValueError):
    """Raised when a phrase cannot be mapped to a period."""


class MissingPeriod(UnknownDatePhrase):
    """Raised when no period was given at all.

    Distinct from :class:`UnknownDatePhrase` so the caller can ask which
    period instead of quietly substituting today. A substituted period
    answers a different question than the one asked, and the answer looks
    exactly as confident as a correct one.
    """


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

# Spelled-out counts: "last two months" is how the period is actually
# spoken, and a digits-only rule rejects it outright.
_WORD_NUMBERS = {
    'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5, 'six': 6,
    'seven': 7, 'eight': 8, 'nine': 9, 'ten': 10, 'eleven': 11, 'twelve': 12,
}


def _resolve_month(word):
    """Month number for a name, tolerating a misspelling.

    An exact name wins outright; a close match is only considered when no
    exact one exists, so "march" can never be dragged to another month.

    0.80 is the cutoff that still catches every misspelling tried
    (julay, Jully, mrach, septmber, agust, febuary, ocotber, aprl) while
    rejecting "juno". It does still accept "maya" and "marcy", so this
    must only ever be applied to a date phrase -- never to a name field.
    """
    if word in _MONTHS:
        return _MONTHS[word]
    if len(word) < 3:
        return None
    close = get_close_matches(word, _MONTH_NAMES, n=1, cutoff=0.80)
    return _MONTHS[close[0]] if close else None


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


def _shift_months(anchor, n):
    """Move ``anchor`` by ``n`` calendar months, clamping the day.

    31 March shifted back two months is 31 January, but shifted back one has
    no 31st to land on; clamping to that month's last day keeps the range
    continuous instead of raising.
    """
    total = (anchor.year * 12 + anchor.month - 1) + n
    year, month = divmod(total, 12)
    month += 1
    return date(year, month, min(anchor.day, monthrange(year, month)[1]))


def resolve_date_range(phrase, today=None):
    """Map a natural date phrase to an inclusive ISO range.

    Returns a :class:`DateRange`. Raises :class:`UnknownDatePhrase` when the
    phrase carries no resolvable period -- the caller should ask rather than
    quietly defaulting to today, which would answer a different question than
    the one asked.
    """
    today = today or date.today()
    if not phrase or not str(phrase).strip():
        raise MissingPeriod('no period given')

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

    # "next 7 days" / "last 14 days" / "last two months" / "next 3 months"
    m = re.fullmatch(
        r'(?:the\s+)?(next|coming|last|past|previous)\s+(\d{1,3}|[a-z]+)\s+(days?|months?)',
        text,
    )
    if m:
        direction, count_word, unit = m.group(1), m.group(2), m.group(3)
        n = int(count_word) if count_word.isdigit() else _WORD_NUMBERS.get(count_word)
        if not n:
            raise UnknownDatePhrase(phrase)
        forward = direction in ('next', 'coming')
        if unit.startswith('day'):
            if forward:
                return DateRange(today, today + timedelta(days=n - 1), f'next {n} days')
            return DateRange(today - timedelta(days=n - 1), today, f'last {n} days')
        # Months are anchored to today rather than snapped to whole calendar
        # months: "last two months" is a span ending now, which is what the
        # phrase means when someone asks what has just happened.
        if forward:
            return DateRange(today, _shift_months(today, n), f'next {n} months')
        return DateRange(_shift_months(today, -n), today, f'last {n} months')

    # "may", "may 2026", "march 2027" -> that whole calendar month. A bare
    # month always means the current year, read at runtime: pushing a past
    # month forward answers about a year nobody mentioned, and the count that
    # comes back is wrong but entirely plausible.
    m = re.fullmatch(r'([a-z]+)(?:\s+(\d{4}))?', text)
    if m:
        month = _resolve_month(m.group(1))
        if month:
            year = int(m.group(2)) if m.group(2) else today.year
            anchor = date(year, month, 1)
            s, e = _month_bounds(anchor)
            return DateRange(s, e, f'{anchor:%B %Y}')

    # a bare weekday name -> the next occurrence, today counting as itself
    if text in _WEEKDAYS:
        delta = (_WEEKDAYS[text] - today.weekday()) % 7
        d = today + timedelta(days=delta)
        return DateRange(d, d, text)

    raise UnknownDatePhrase(phrase)
