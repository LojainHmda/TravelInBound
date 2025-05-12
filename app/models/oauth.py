from app import db
from flask_dance.consumer.storage.sqla import OAuthConsumerMixin
from sqlalchemy import UniqueConstraint

# OAuth model required for Replit Auth
class OAuth(OAuthConsumerMixin, db.Model):
    __tablename__ = 'oauth'
    
    user_id = db.Column(db.String, db.ForeignKey('user.id'))
    browser_session_key = db.Column(db.String, nullable=False)
    
    __table_args__ = (UniqueConstraint(
        'user_id',
        'browser_session_key',
        'provider',
        name='uq_user_browser_session_key_provider',
    ),)