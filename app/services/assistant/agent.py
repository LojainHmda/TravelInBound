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
                'files or bookings.'
            ),
            'parameters': {
                'type': 'object',
                'properties': {
                    'customer_name': {'type': 'string'},
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
                'categories, including empty ones.'
            ),
            'parameters': {
                'type': 'object',
                'properties': {
                    'date_phrase': {
                        'type': 'string',
                        'description': (
                            'The period exactly as the user said it: today, '
                            'tomorrow, this week, this month, next 7 days, or '
                            'an explicit range like "01/03/2026 to 15/03/2026". '
                            'Defaults to today when the user gave no period.'
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
                'waiting", etc.'
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
                            'Status filter. Omit unless the user indicated one '
                            '- it defaults to requested.'
                        ),
                    },
                    'date_phrase': {'type': 'string'},
                    'city': {'type': 'string', 'description': 'City filter, if the user named one.'},
                    'hotel_name': {
                        'type': 'string',
                        'description': 'Hotel/restaurant/guide/company name, if the user named one.',
                    },
                },
                'required': ['category'],
            },
        },
    },
]

_DISPATCH = {
    'search_customers': lambda a: tools.search_customers(a.get('name', '')),
    'find_inbound_tours': lambda a: tools.find_inbound_tours(a.get('customer_name', '')),
    'run_down_summary': lambda a: tools.run_down_summary(a.get('date_phrase')),
    'run_down_drilldown': lambda a: tools.run_down_drilldown(
        a.get('category', ''),
        status=a.get('status') or 'requested',
        date_phrase=a.get('date_phrase'),
        city=a.get('city'),
        hotel_name=a.get('hotel_name'),
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
        '- Dates shown to the user are DD/MM/YYYY. Never show ISO dates.',
        '- For a Run Down summary, report every category, including ones with '
        'zero activity - say "no activity" rather than leaving them out.',
        '- Cut-off: the ONLY categories you may call urgent are the ones listed '
        'in the tool result\'s "flagged" array. If "flagged" is empty, or '
        '"urgent" is false, say nothing about cut-offs at all -- do not write '
        '"urgent", "attention needed" or similar. A cut_off of 0 is not a '
        'cut-off. A cut_off of null means cut-off does not apply to that '
        'category (Guides and Meet & Assist), which is also not a cut-off.',
        '- Status (the service booking) and File Status (the tour file) are '
        'different fields. Never merge them.',
        '- When several customers match, list them and ask which one.',
        '- NEVER output a table, and never list every row. The interface '
        'renders the tool data as a real table directly beneath your reply, so '
        'a table in your text is duplicated and renders as raw pipes.',
        '- Reply in at most two short sentences: say what the period was and '
        'what stands out (the busiest category, anything flagged). Let the '
        'table carry the per-row numbers.',
        '- NEVER write a URL, link or markdown link. The interface renders the '
        'navigation link itself; any address you write would be invented.',
        '- When a tool returns a count, state the number ("90 files"), never a '
        'vague quantity like "a large number". If "truncated" is true, say the '
        'total and that only the most recent are shown.',
    ]
    if selected:
        lines += [
            '',
            'The user has selected customer "%s"%s. Use this customer for '
            'follow-up questions that do not name another one.'
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
