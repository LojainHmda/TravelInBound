"""OpenAI tool-calling loop for the Phase 1 assistant.

The model never sees the database. It picks a tool and arguments; the tools in
``tools.py`` do the work by calling the very view functions the Run Down page
calls, and the model's only remaining job is to phrase the result. That split
is deliberate: a number the model invented and a number the page computed are
indistinguishable in chat, so the model is never given the chance to invent one.
"""

import json
import os
from datetime import date

from flask import session

from . import tools

__all__ = ['TravelAssistant', 'AssistantUnavailable']

MODEL = 'gpt-4o'
MAX_TOOL_ROUNDS = 5
_SESSION_KEY = 'assistant_customer'


class AssistantUnavailable(RuntimeError):
    """No API key configured."""


TOOL_SCHEMAS = [
    {
        'type': 'function',
        'function': {
            'name': 'search_customers',
            'description': (
                'Search customers by name, company or email. Use whenever the '
                'user names a customer or asks to find one. Returns a list for '
                'the user to choose from.'
            ),
            'parameters': {
                'type': 'object',
                'properties': {
                    'name': {'type': 'string', 'description': 'Full or partial customer name.'},
                },
                'required': ['name'],
            },
        },
    },
    {
        'type': 'function',
        'function': {
            'name': 'find_inbound_tours',
            'description': (
                'List inbound tour files for a customer. Use after a customer '
                'is selected, or when the user asks for a customer\'s tours, '
                'files, requests or bookings. A "request" is a file, not a '
                'status.'
            ),
            'parameters': {
                'type': 'object',
                'properties': {
                    'customer_name': {'type': 'string'},
                    'date_phrase': {
                        'type': 'string',
                        'description': (
                            'Period exactly as the user said it, when they gave '
                            'one: September, last two months, this week, or '
                            '"01/03/2026 to 15/03/2026". Omit it entirely when '
                            'they named no period - never invent one.'
                        ),
                    },
                    'status': {
                        'type': 'string',
                        'enum': ['request', 'confirmed', 'invoiced', 'all'],
                        'description': (
                            'The FILE status, passed ONLY when the user names '
                            'one. These are the inbound list states (Request, '
                            'Confirmed, Invoiced), not the service booking '
                            'statuses used by run_down_drilldown. Omit it and '
                            'every status is returned.'
                        ),
                    },
                    'latest': {
                        'type': 'boolean',
                        'description': (
                            'True only when the user asked for a single file - '
                            '"the last file", "the most recent one", "their '
                            'newest booking". Returns the most recently created '
                            'file. Never guess which file is "last" yourself.'
                        ),
                    },
                },
                'required': ['customer_name'],
            },
        },
    },
    {
        'type': 'function',
        'function': {
            'name': 'run_down_summary',
            'description': (
                'Run Down counts for every service category over a period. Use '
                'for "what is happening today", "run down for this week", or '
                'any request for an overview. Always returns all five '
                'categories, including empty ones. '
                'DO NOT use this for a cut-off question in ANY language or '
                'script -- it returns no files and lists Guides and Meet & '
                'Assist, which have no cut-off at all. Cut-off questions go '
                'to run_down_cut_off.'
            ),
            'parameters': {
                'type': 'object',
                'properties': {
                    'date_phrase': {
                        'type': 'string',
                        'description': (
                            'The period exactly as the user said it: today, '
                            'tomorrow, this week, this month, September, last '
                            'two months, next 7 days, or an explicit range like '
                            '"01/03/2026 to 15/03/2026". Omit it when the user '
                            'named no period - the tool will ask them. Never '
                            'substitute today on their behalf.'
                        ),
                    },
                },
            },
        },
    },
    {
        'type': 'function',
        'function': {
            'name': 'run_down_drilldown',
            'description': (
                'Rows for ONE Run Down category, grouped by location. Use for '
                '"show accommodation requests", "which hotels in Amman are '
                'waiting", etc. '
                'NEVER use this for a cut-off question, in any language or '
                'script. It carries NO cut-off data whatsoever, so it can '
                'neither find a cut-off nor establish that none exists, and '
                'answering from it produces a false denial. A cut-off is a '
                'supplier DEADLINE DATE, NOT the Waiting status -- never map '
                'a cut-off question onto status=waiting. Cut-off questions go '
                'to run_down_cut_off.'
            ),
            'parameters': {
                'type': 'object',
                'properties': {
                    'category': {
                        'type': 'string',
                        'enum': ['accommodation', 'transportation', 'guide',
                                 'restaurant', 'meet_assist'],
                    },
                    'status': {
                        'type': 'string',
                        'enum': ['requested', 'confirmed', 'waiting', 'cancelled', 'all'],
                        'description': (
                            'Pass this ONLY when the user names a status out '
                            'loud: requested, confirmed, cancelled or waiting. '
                            'Omit it otherwise and every status is returned. '
                            'The words "request", "requests" and "file" mean '
                            'the tour file itself, NOT the Requested status. '
                            '"Cut off" is NEVER a status: it is a deadline '
                            'date and has its own tool. Never translate a '
                            'cut-off question into status=waiting.'
                        ),
                    },
                    'date_phrase': {'type': 'string'},
                    'city': {'type': 'string', 'description': 'City filter, if the user named one.'},
                    'name': {
                        'type': 'string',
                        'description': (
                            'The specific hotel, restaurant, guide, transport '
                            'company or Meet & Assist name, when the user named '
                            'one -- e.g. "guide Sami" means name="Sami". '
                            'Matched exactly, so pass the name as the user said '
                            'it. Put ONLY the name here: a month or period that '
                            'followed the name belongs in date_phrase, even '
                            'when the user wrote no "in" between them and even '
                            'when it is misspelt -- "guide Mousa julay" means '
                            'name="Mousa", date_phrase="julay".'
                        ),
                    },
                },
                'required': ['category'],
            },
        },
    },
    {
        'type': 'function',
        'function': {
            'name': 'run_down_cut_off',
            'description': (
                'Services whose cut-off DEADLINE falls inside a period, with '
                'the files that carry them. THE ONLY TOOL FOR CUT-OFF '
                'QUESTIONS, whatever language or script the user writes in. '
                'Route to this tool whenever the question contains any of: '
                'English "cut off", "cutoff", "cut-off", "deadline"; '
                'Latin-script Arabic "cut off", "kat of", "katof", '
                '"akher maw3ed", "akhir mawed", "mohla", "muhla", '
                '"deadline" (e.g. "shu 3ndi cut off date la shahr 9"); '
                'Arabic script \u0643\u062a \u0623\u0648\u0641, '
                '\u0643\u0627\u062a \u0623\u0648\u0641, '
                '\u0627\u0644\u0643\u062a \u0623\u0648\u0641, '
                '\u0643\u062a\u0648\u0641, '
                '\u0627\u0644\u0645\u0648\u0639\u062f '
                '\u0627\u0644\u0646\u0647\u0627\u0626\u064a, '
                '\u0645\u0648\u0639\u062f '
                '\u0646\u0647\u0627\u0626\u064a, '
                '\u0622\u062e\u0631 \u0645\u0648\u0639\u062f, '
                '\u0627\u0644\u0645\u0648\u0639\u062f '
                '\u0627\u0644\u0623\u062e\u064a\u0631, '
                '\u0645\u0647\u0644\u0629, '
                '\u0627\u0644\u0645\u0647\u0644\u0629, '
                '\u0622\u062e\u0631 \u0645\u0647\u0644\u0629, '
                '\u0627\u0644\u062d\u062f '
                '\u0627\u0644\u0623\u062e\u064a\u0631, '
                '\u062f\u064a\u062f\u0644\u0627\u064a\u0646, '
                '\u0622\u062e\u0631 \u0645\u0648\u0639\u062f '
                '\u0644\u0644\u0625\u0644\u063a\u0627\u0621. '
                'A cut-off question in Arabic script is the SAME question as '
                'in English and must reach this same tool -- never '
                'run_down_summary, never run_down_drilldown. '
                'Only Accommodation, Transportation and Restaurant have a '
                'cut-off; for Guides and Meet & Assist the tool answers '
                '"does not apply", which is NOT a count of zero.'
            ),
            'parameters': {
                'type': 'object',
                'properties': {
                    'date_phrase': {
                        'type': 'string',
                        'description': (
                            'The period exactly as the user said it. Omit it '
                            'when they named none - the tool will ask.'
                        ),
                    },
                    'category': {
                        'type': 'string',
                        'enum': ['accommodation', 'transportation',
                                 'restaurant', 'guide', 'meet_assist'],
                        'description': (
                            'Pass ONLY when the user named a category, e.g. '
                            '"cut off for accommodation". Omit it for a bare '
                            '"what cut-offs are there" so every category with '
                            'a cut-off is covered.'
                        ),
                    },
                    'files_only': {
                        'type': 'boolean',
                        'description': (
                            'True when the user asked WHICH FILES have a '
                            'cut-off ("which files have cut off in '
                            'September") - the reply is then the file list '
                            'alone. False, the default, when they asked what '
                            'cut-offs there ARE - the reply is the counts and '
                            'then the files.'
                        ),
                    },
                },
            },
        },
    },
    {
        'type': 'function',
        'function': {
            'name': 'list_inbound_files',
            'description': (
                'List inbound tour FILES in a period -- for everyone, or for '
                'one agent. Use for "all files in September", "all bookings in '
                'June", "the requested files this month". This is the right '
                'tool whenever no customer was named. It returns file number, '
                'agent, travel dates and status. Do NOT use run_down_summary '
                'for a request for files: that returns service counts, which '
                'is a different question.'
            ),
            'parameters': {
                'type': 'object',
                'properties': {
                    'date_phrase': {
                        'type': 'string',
                        'description': (
                            'Period exactly as the user said it. Required - if '
                            'they named no period, call this anyway without it '
                            'and the tool will ask them which period.'
                        ),
                    },
                    'agent': {
                        'type': 'string',
                        'description': (
                            'Agent or customer name, only if the user named '
                            'one. Omit for "all files".'
                        ),
                    },
                    'status': {
                        'type': 'string',
                        'enum': ['request', 'confirmed', 'invoiced', 'all'],
                        'description': (
                            'FILE status, passed ONLY when the user names one. '
                            'Omit and every status is returned.'
                        ),
                    },
                    'deleted': {
                        'type': 'boolean',
                        'description': (
                            'True ONLY when the user explicitly asks for '
                            'deleted or trashed files. They are excluded '
                            'otherwise.'
                        ),
                    },
                },
            },
        },
    },
    {
        'type': 'function',
        'function': {
            'name': 'list_customers',
            'description': (
                'List the customers who have at least one file travelling in a '
                'period. Use for "all customers I dealt with in September", '
                '"which agents have files this month".'
            ),
            'parameters': {
                'type': 'object',
                'properties': {
                    'date_phrase': {
                        'type': 'string',
                        'description': (
                            'Period exactly as the user said it. Call without '
                            'it if they named none and the tool will ask.'
                        ),
                    },
                },
            },
        },
    },
    {
        'type': 'function',
        'function': {
            'name': 'find_file_by_number',
            'description': (
                'Look up ONE file by its file number, e.g. "show me file '
                '2608015", "open 2609002". Searches every file in the system. '
                'ALWAYS use this for a bare file number - never search a '
                "customer's files for it, even when a customer is selected."
            ),
            'parameters': {
                'type': 'object',
                'properties': {
                    'number': {
                        'type': 'string',
                        'description': 'The file number as the user typed it.',
                    },
                },
                'required': ['number'],
            },
        },
    },
    {
        'type': 'function',
        'function': {
            'name': 'search_suppliers',
            'description': (
                'Find SUPPLIERS by name and/or type: guides, hotels, '
                'restaurants, transport companies, Meet & Assist providers and '
                'airlines. Use this -- never search_customers -- when the user '
                'names a guide, hotel, restaurant, transport company or '
                'airline. A guide is not a customer.'
            ),
            'parameters': {
                'type': 'object',
                'properties': {
                    'name': {
                        'type': 'string',
                        'description': 'Supplier name or part of it.',
                    },
                    'supplier_type': {
                        'type': 'string',
                        'enum': ['guides', 'accommodation', 'transportation',
                                 'restaurant', 'meet-assist', 'airline', 'others'],
                        'description': (
                            'Narrow to one type when the user said which, e.g. '
                            '"guide Sami" means supplier_type="guides".'
                        ),
                    },
                },
            },
        },
    },
]

_DISPATCH = {
    'search_customers': lambda a: tools.search_customers(a.get('name', '')),
    'find_inbound_tours': lambda a: tools.find_inbound_tours(
        a.get('customer_name', ''),
        date_phrase=a.get('date_phrase'),
        status=a.get('status'),
        latest=bool(a.get('latest')),
    ),
    'run_down_summary': lambda a: tools.run_down_summary(a.get('date_phrase')),
    'list_inbound_files': lambda a: tools.list_inbound_files(
        date_phrase=a.get('date_phrase'),
        agent=a.get('agent'),
        status=a.get('status'),
        deleted=bool(a.get('deleted')),
    ),
    'list_customers': lambda a: tools.list_customers(
        date_phrase=a.get('date_phrase'),
    ),
    'find_file_by_number': lambda a: tools.find_file_by_number(a.get('number', '')),
    'search_suppliers': lambda a: tools.search_suppliers(
        name=a.get('name'),
        supplier_type=a.get('supplier_type'),
    ),
    'run_down_cut_off': lambda a: tools.run_down_cut_off(
        date_phrase=a.get('date_phrase'),
        category=a.get('category'),
        files_only=bool(a.get('files_only')),
        # Injected by ask(), not by the model: the tool checks the period it
        # was handed against the message it was supposedly taken from.
        asked_in=a.get('_asked_in'),
    ),
    'run_down_drilldown': lambda a: tools.run_down_drilldown(
        a.get('category', ''),
        status=a.get('status') or 'all',
        date_phrase=a.get('date_phrase'),
        city=a.get('city'),
        hotel_name=a.get('name'),
    ),
}


def _system_prompt():
    today = date.today()
    selected = get_selected_customer()
    lines = [
        'You are the operations assistant for a Jordan inbound tour company.',
        'Today is %s (%s).' % (today.strftime('%A %d %B %Y'), today.strftime('%d/%m/%Y')),
        '',
        'Rules:',
        '- Never state a count, name or date that did not come from a tool result.',
        '  If you do not have it, call a tool or say you do not know.',
        '- A number the USER put in the question is not a tool result. Never '
        'repeat it back as fact. If they say "the four files" and the tool '
        'returned five, say five and tell them the count differs from what '
        'they expected -- never restate their number to agree with them.',
        '- Dates shown to the user are DD/MM/YYYY. Never show ISO dates.',
        '- For a Run Down summary, report every category, including ones with '
        'zero activity - say "no activity" rather than leaving them out.',
        '- ROUTING, before anything else about cut-offs: any question about a '
        'cut-off or a deadline goes to run_down_cut_off, in EVERY language '
        'and script -- English "cut off"/"cutoff"/"deadline", Latin-script '
        'Arabic ("cut off", "kat of", "akher maw3ed", "mohla"), and Arabic '
        'script (\u0643\u062a \u0623\u0648\u0641, '
        '\u0627\u0644\u0645\u0648\u0639\u062f '
        '\u0627\u0644\u0646\u0647\u0627\u0626\u064a, '
        '\u0622\u062e\u0631 \u0645\u0648\u0639\u062f, '
        '\u0645\u0647\u0644\u0629, '
        '\u062f\u064a\u062f\u0644\u0627\u064a\u0646). The script the user '
        'typed in NEVER changes which tool answers. Do not use '
        'run_down_summary for it (no files, and it lists categories that have '
        'no cut-off) and never run_down_drilldown (it has no cut-off data and '
        'will produce a false denial). A cut-off is a deadline DATE, not the '
        'Waiting status.',
        '- When you asked which period and the user replies with a bare number '
        '1-12 ("8", "\u0669"), that is the MONTH. Pass it as the month name '
        'or as "month 8" -- a bare "8" on its own is rejected as ambiguous, '
        'and re-asking a question they already answered is worse than reading '
        'it the obvious way.',
        '- Cut-off: the ONLY categories you may call urgent are the ones listed '
        'in the tool result\'s "flagged" array. If "flagged" is empty, or '
        '"urgent" is false, say nothing about cut-offs at all -- do not write '
        '"urgent", "attention needed" or similar. A cut_off of 0 is not a '
        'cut-off. A cut_off of null means cut-off does not apply to that '
        'category (Guides and Meet & Assist), which is also not a cut-off.',
        '- NEVER state that something does not exist because a tool result did '
        'not mention it. A missing field means THAT TOOL DOES NOT KNOW, never '
        'that the thing is absent. run_down_drilldown carries no cut-off data '
        'whatsoever, so it can never establish that a cut-off does or does not '
        'exist -- if you were asked about cut-offs, call run_down_cut_off. Only '
        'a run_down_cut_off result, or a run_down_summary cut_off number, may '
        'be used to say a cut-off exists or does not.',
        '- Report EVERY category that has a cut-off in the period, not just the '
        'one asked about. If "flagged" holds more than one entry, name them '
        'all: a deadline the user was not told about is one they cannot act '
        'on. Give each category its own count.',
        '- When a cut-off result has "not_applicable": true, say that category '
        'has no cut-off at all. Do NOT say it has none due, has zero, or is '
        'clear -- Guides and Meet & Assist have no cut-off field to be zero.',
        '- Status (the service booking) and File Status (the tour file) are '
        'different fields. Never merge them.',
        '- "Request", "requests" and "file" mean the tour file itself. They '
        'are NOT the Requested status. Pass a status filter only when the '
        'user actually says requested, confirmed, cancelled or waiting; '
        'otherwise omit it and report every status.',
        '- If the user gave no period, do not invent one and do not assume '
        'today. Call the tool without a period and ask them which period '
        'they mean when it asks.',
        '- NEVER carry a period over from an earlier question. A period is '
        'theirs only if they said it in the message you are answering RIGHT '
        'NOW. "Cut off for restaurants" after a question about September is '
        'a question with NO period -- call the tool without date_phrase and '
        'ask which period, exactly as you would if September had never been '
        'mentioned. Answering for a silently inherited period is the same '
        'error as inventing one: "no restaurant cut-offs" is then true of a '
        'month nobody asked about, and reads as confident as a real answer. '
        'If a result carries "inherited_period_blocked", do NOT retry with '
        'the same period -- ask them.',
        '- Whenever your answer is scoped to a period, say which period it '
        'was, in words, every time. An answer that does not name its period '
        'cannot be checked by the person reading it.',
        '- Never name a "last", "latest" or "most recent" item yourself by '
        'picking one out of a list. Ask the tool for it, and if the tool did '
        'not return it, say so.',
        '- Never call a set uniform when the tool split it into more than '
        'one group. If "groups" holds several labels, the rows are not all '
        'the same: give the split exactly as the data has it, or say nothing '
        'about the distribution and let the table show it.',
        '- When several customers match, list them and ask which one.',
        '- Guides, hotels, restaurants, transport companies and airlines '
        'are SUPPLIERS, not customers. Use search_suppliers for them. '
        'Never report a guide as missing because the customer search '
        'found nothing.',
        '- A bare file number is its own question. Look it up with '
        'find_file_by_number, across the whole system, even when a '
        'customer is selected. Never narrow it to that customer.',
        '- Never say something does not exist unless the tool that looked '
        'for it searched everywhere. When a result carries '
        '"searched_scope", say what was searched: "it is not among '
        'Black Tomato\'s files" is true, "there is no such file" is not.',
        '- A request for FILES is not a request for the Run Down. Use '
        'list_inbound_files for files and run_down_summary only when the '
        'user asks for the run down or for service counts.',
        '- NEVER output a table, and never list every row. The interface '
        'renders the tool data as a real table directly beneath your reply, so '
        'a table in your text is duplicated and renders as raw pipes.',
        '- Reply in at most two short sentences: say what the period was and '
        'what stands out (the busiest category, anything flagged). Let the '
        'table carry the per-row numbers.',
        '- NEVER write a URL, link or markdown link. The interface renders the '
        'navigation link itself; any address you write would be invented. '
        'This holds ESPECIALLY when the result is empty: with no rows to '
        'describe there is a pull to offer a link instead, and "[Open Run '
        'Down](http://...)" is exactly the shape that has reached users as '
        'dead literal text. An empty result is a complete answer on its own '
        '-- say the period and that nothing falls in it, and stop. The button '
        'is already there.',
        '- The navigation link does not always carry the filters you were asked '
        'about. If a result has "list_url_period_applied": false, the page it '
        'opens is NOT filtered to the period -- say so plainly in your reply. '
        'If a result carries "list_url_note", tell the user what it says. '
        'Never let them believe the page is narrowed when it is not: a link '
        'that silently shows a different set of files than the count beside '
        'it is worse than no link.',
        '- When a tool returns a count, state the number ("90 files"), never a '
        'vague quantity like "a large number". If "truncated" is true, say the '
        'total and that only the most recent are shown.',
    ]
    if selected:
        lines += [
            '',
            'The user has selected customer "%s"%s. Use this customer for '
            'follow-up questions that do not name another one, and SAY SO '
            'in your reply whenever you do ("for Black Tomato") -- a '
            'narrowed answer that does not admit it was narrowed reads as '
            'a complete one. Never apply it to a bare file number, and '
            'never to a request that names no customer such as "all files '
            'in September".'
            % (selected.get('name', ''),
               ' (id %s)' % selected['id'] if selected.get('id') else ''),
        ]
    return '\n'.join(lines)


# --------------------------------------------------------------------------
# REQ-1.2 -- selected customer context, kept server-side in the session
# --------------------------------------------------------------------------

def get_selected_customer():
    value = session.get(_SESSION_KEY)
    return value if isinstance(value, dict) else None


def set_selected_customer(customer):
    if customer:
        session[_SESSION_KEY] = {
            'id': customer.get('id'),
            'name': customer.get('name', ''),
        }
        session.modified = True


def clear_selected_customer():
    session.pop(_SESSION_KEY, None)
    session.modified = True


class TravelAssistant:
    def __init__(self):
        api_key = os.environ.get('OPENAI_API_KEY')
        if not api_key:
            raise AssistantUnavailable('OPENAI_API_KEY is not configured.')
        from openai import OpenAI
        self.client = OpenAI(api_key=api_key)
        self.model = MODEL

    def ask(self, user_message, history=None):
        """Run one turn. Returns {reply, data, navigate_url, tools_used}."""
        messages = [{'role': 'system', 'content': _system_prompt()}]
        for turn in (history or [])[-8:]:
            role = turn.get('role')
            content = (turn.get('content') or '').strip()
            if role in ('user', 'assistant') and content:
                messages.append({'role': role, 'content': content})
        messages.append({'role': 'user', 'content': user_message})

        collected, used = [], []

        for _ in range(MAX_TOOL_ROUNDS):
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=TOOL_SCHEMAS,
                tool_choice='auto',
            )
            choice = completion.choices[0].message

            if not choice.tool_calls:
                return self._finish(choice.content or '', collected, used)

            messages.append({
                'role': 'assistant',
                'content': choice.content,
                'tool_calls': [{
                    'id': tc.id,
                    'type': 'function',
                    'function': {'name': tc.function.name, 'arguments': tc.function.arguments},
                } for tc in choice.tool_calls],
            })

            for call in choice.tool_calls:
                name = call.function.name
                try:
                    args = json.loads(call.function.arguments or '{}')
                except ValueError:
                    args = {}

                # This turn's own words, so a tool can tell a period the user
                # gave from one the model carried over. Set here rather than
                # taken from the model: it is evidence, not an argument, and a
                # model-supplied value would defeat the check it feeds.
                args['_asked_in'] = user_message

                handler = _DISPATCH.get(name)
                if handler is None:
                    result = {'ok': False, 'error': 'Unknown tool "%s".' % name}
                else:
                    try:
                        result = handler(args)
                    except Exception as exc:  # surfaced to the user, not swallowed
                        result = {'ok': False, 'error': '%s failed: %s' % (name, exc)}

                # A single unambiguous customer hit becomes the active context.
                if name == 'search_customers' and result.get('ok'):
                    hits = result.get('customers') or []
                    if len(hits) == 1:
                        set_selected_customer(hits[0])

                used.append(name)
                collected.append({'tool': name, 'result': result})
                messages.append({
                    'role': 'tool',
                    'tool_call_id': call.id,
                    'content': json.dumps(result, default=str),
                })

        # Ran out of rounds: answer from what we have rather than looping.
        final = self.client.chat.completions.create(
            model=self.model,
            messages=messages + [{
                'role': 'user',
                'content': 'Summarise what you found so far. Do not call more tools.',
            }],
        )
        return self._finish(final.choices[0].message.content or '', collected, used)

    @staticmethod
    def _finish(reply, collected, used):
        navigate_url, data = None, None
        for item in collected:
            result = item.get('result') or {}
            if result.get('navigate_url') and not navigate_url:
                navigate_url = result['navigate_url']
            if result.get('ok'):
                data = result
        return {
            'reply': reply.strip(),
            'data': data,
            'tool_results': collected,
            'tools_used': used,
            'navigate_url': navigate_url,
            'selected_customer': get_selected_customer(),
        }
