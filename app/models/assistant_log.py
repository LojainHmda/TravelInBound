"""Assistant conversation log.

One row per completed assistant turn. This exists so a conversation can be
reviewed after the fact: without it the widget's history lives only in a
JavaScript variable and disappears on reload, which makes "why did it answer
that?" unanswerable.

The tool results are stored alongside the reply on purpose -- the reply is
prose the model wrote, while the tool payload is the data it was given, and
grading the assistant means comparing the two.
"""

import json
from datetime import datetime

from app.extensions import db


class AssistantChatLog(db.Model):
    __tablename__ = 'assistant_chat_log'

    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True, index=True)

    # A browser-generated id so turns can be stitched back into conversations.
    session_key = db.Column(db.String(64), nullable=True, index=True)

    user_message = db.Column(db.Text, nullable=False)
    reply = db.Column(db.Text, nullable=True)

    tools_used = db.Column(db.String(255), nullable=True)   # comma-separated
    tool_results = db.Column(db.Text, nullable=True)        # JSON
    navigate_url = db.Column(db.Text, nullable=True)
    selected_customer = db.Column(db.String(255), nullable=True)

    ok = db.Column(db.Boolean, default=True, nullable=False)
    error = db.Column(db.Text, nullable=True)
    duration_ms = db.Column(db.Integer, nullable=True)

    user = db.relationship('User', backref='assistant_chat_logs', lazy=True)

    def to_dict(self, include_results=True):
        data = {
            'id': self.id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'user_id': self.user_id,
            'session_key': self.session_key,
            'user_message': self.user_message,
            'reply': self.reply,
            'tools_used': (self.tools_used or '').split(',') if self.tools_used else [],
            'navigate_url': self.navigate_url,
            'selected_customer': self.selected_customer,
            'ok': self.ok,
            'error': self.error,
            'duration_ms': self.duration_ms,
        }
        if include_results and self.tool_results:
            try:
                data['tool_results'] = json.loads(self.tool_results)
            except ValueError:
                data['tool_results'] = None
        return data

    def __repr__(self):
        return '<AssistantChatLog %s %r>' % (self.id, (self.user_message or '')[:40])
