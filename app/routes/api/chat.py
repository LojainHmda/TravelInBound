"""Assistant API -- Phase 1.

Replaces the previous Booking-centric chat endpoints. The blueprint is still
named ``chat_api``: app/__init__.py discovers it by that name.
"""

import json
import time

from flask import Blueprint, jsonify, request
from flask_login import current_user, login_required

from app.extensions import csrf, db
from app.models.assistant_log import AssistantChatLog
from app.services.assistant import (
    AssistantUnavailable,
    TravelAssistant,
    clear_selected_customer,
    get_selected_customer,
    set_selected_customer,
)

chat_api = Blueprint('chat_api', __name__)


@chat_api.route('/api/assistant', methods=['POST'])
@login_required
@csrf.exempt
def assistant():
    """One assistant turn."""
    payload = request.get_json(silent=True) or {}
    message = (payload.get('message') or '').strip()
    if not message:
        return jsonify({'ok': False, 'error': 'Message is required.'}), 400

    history = payload.get('history')
    if not isinstance(history, list):
        history = []

    try:
        agent = TravelAssistant()
    except AssistantUnavailable:
        return jsonify({
            'ok': False,
            'error': 'assistant_unavailable',
            'reply': 'The assistant needs OPENAI_API_KEY to be configured.',
        }), 503

    session_key = (payload.get('session_key') or '')[:64] or None
    started = time.time()

    try:
        result = agent.ask(message, history=history)
    except Exception as exc:
        # The message reaches the user, so it must say what actually broke
        # rather than a generic failure they cannot act on.
        _log_turn(message, session_key, None, started, ok=False, error=str(exc))
        return jsonify({
            'ok': False,
            'error': str(exc),
            'reply': 'Something went wrong answering that: %s' % exc,
        }), 500

    _log_turn(message, session_key, result, started, ok=True)
    result['ok'] = True
    return jsonify(result)


def _log_turn(message, session_key, result, started, ok=True, error=None):
    """Record one turn. Never let logging break the answer the user is owed."""
    try:
        result = result or {}
        selected = result.get('selected_customer') or {}
        entry = AssistantChatLog(
            user_id=getattr(current_user, 'id', None),
            session_key=session_key,
            user_message=message,
            reply=result.get('reply'),
            tools_used=','.join(result.get('tools_used') or []) or None,
            tool_results=json.dumps(result.get('tool_results') or [], default=str),
            navigate_url=result.get('navigate_url'),
            selected_customer=selected.get('name') if isinstance(selected, dict) else None,
            ok=ok,
            error=error,
            duration_ms=int((time.time() - started) * 1000),
        )
        db.session.add(entry)
        db.session.commit()
    except Exception:
        db.session.rollback()


@chat_api.route('/api/assistant/log', methods=['GET'])
@login_required
def assistant_log():
    """Recent turns, newest first -- the input for a conversation review."""
    limit = min(request.args.get('limit', 100, type=int), 500)
    session_key = (request.args.get('session_key') or '').strip()

    query = AssistantChatLog.query
    if session_key:
        query = query.filter(AssistantChatLog.session_key == session_key)

    rows = query.order_by(AssistantChatLog.created_at.desc()).limit(limit).all()
    include = request.args.get('include_results', '1') != '0'
    return jsonify({
        'ok': True,
        'count': len(rows),
        'turns': [r.to_dict(include_results=include) for r in rows],
    })


@chat_api.route('/api/assistant/customer', methods=['POST'])
@login_required
@csrf.exempt
def select_customer():
    """REQ-1.2 -- pin the customer chosen from the result list."""
    payload = request.get_json(silent=True) or {}
    customer = payload.get('customer')
    if not isinstance(customer, dict) or not customer.get('name'):
        return jsonify({'ok': False, 'error': 'A customer object is required.'}), 400
    set_selected_customer(customer)
    return jsonify({'ok': True, 'selected_customer': get_selected_customer()})


@chat_api.route('/api/assistant/customer', methods=['DELETE'])
@login_required
@csrf.exempt
def deselect_customer():
    clear_selected_customer()
    return jsonify({'ok': True, 'selected_customer': None})


@chat_api.route('/api/assistant/context', methods=['GET'])
@login_required
def assistant_context():
    return jsonify({'ok': True, 'selected_customer': get_selected_customer()})
