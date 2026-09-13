"""add assistant_chat_log table

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-09-13 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c3d4e5f6a7b8'
down_revision = 'b2c3d4e5f6a7'
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing = set(inspector.get_table_names())

    if 'assistant_chat_log' not in existing:
        op.create_table(
            'assistant_chat_log',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('user_id', sa.Integer(), nullable=True),
            sa.Column('session_key', sa.String(64), nullable=True),
            sa.Column('user_message', sa.Text(), nullable=False),
            sa.Column('reply', sa.Text(), nullable=True),
            sa.Column('tools_used', sa.String(255), nullable=True),
            sa.Column('tool_results', sa.Text(), nullable=True),
            sa.Column('navigate_url', sa.Text(), nullable=True),
            sa.Column('selected_customer', sa.String(255), nullable=True),
            sa.Column('ok', sa.Boolean(), nullable=False),
            sa.Column('error', sa.Text(), nullable=True),
            sa.Column('duration_ms', sa.Integer(), nullable=True),
            sa.ForeignKeyConstraint(['user_id'], ['user.id']),
            sa.PrimaryKeyConstraint('id'),
        )
        op.create_index('ix_assistant_chat_log_created_at', 'assistant_chat_log', ['created_at'])
        op.create_index('ix_assistant_chat_log_user_id', 'assistant_chat_log', ['user_id'])
        op.create_index('ix_assistant_chat_log_session_key', 'assistant_chat_log', ['session_key'])


def downgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing = set(inspector.get_table_names())

    if 'assistant_chat_log' in existing:
        op.drop_index('ix_assistant_chat_log_session_key', table_name='assistant_chat_log')
        op.drop_index('ix_assistant_chat_log_user_id', table_name='assistant_chat_log')
        op.drop_index('ix_assistant_chat_log_created_at', table_name='assistant_chat_log')
        op.drop_table('assistant_chat_log')
