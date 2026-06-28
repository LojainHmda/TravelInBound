"""add guide expense and payment sheet tables

Revision ID: a1b2c3d4e5f6
Revises: fb3c46c6b670
Create Date: 2026-06-28 23:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a1b2c3d4e5f6'
down_revision = 'fb3c46c6b670'
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing = set(inspector.get_table_names())

    if 'guide_expense_sheet' not in existing:
        op.create_table(
            'guide_expense_sheet',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('request_id', sa.Integer(), nullable=False),
            sa.Column('guide_name', sa.String(200), nullable=True),
            sa.Column('currency', sa.String(3), nullable=True, server_default=sa.text("'JOD'")),
            sa.Column('notes', sa.Text(), nullable=True),
            sa.Column('total_advance', sa.Float(), nullable=True, server_default=sa.text('0')),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(['request_id'], ['inbound_request.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('request_id'),
        )

    if 'guide_expense_sheet_item' not in existing:
        op.create_table(
            'guide_expense_sheet_item',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('sheet_id', sa.Integer(), nullable=False),
            sa.Column('date', sa.Date(), nullable=True),
            sa.Column('description', sa.String(500), nullable=False),
            sa.Column('category', sa.String(100), nullable=True),
            sa.Column('amount', sa.Float(), nullable=False, server_default=sa.text('0')),
            sa.Column('currency', sa.String(3), nullable=True, server_default=sa.text("'JOD'")),
            sa.Column('notes', sa.Text(), nullable=True),
            sa.Column('sort_order', sa.Integer(), nullable=True, server_default=sa.text('0')),
            sa.ForeignKeyConstraint(['sheet_id'], ['guide_expense_sheet.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id'),
        )

    if 'guide_payment_sheet' not in existing:
        op.create_table(
            'guide_payment_sheet',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('request_id', sa.Integer(), nullable=False),
            sa.Column('guide_name', sa.String(200), nullable=True),
            sa.Column('currency', sa.String(3), nullable=True, server_default=sa.text("'JOD'")),
            sa.Column('total_days', sa.Integer(), nullable=True),
            sa.Column('daily_rate', sa.Float(), nullable=True),
            sa.Column('total_guide_fee', sa.Float(), nullable=True, server_default=sa.text('0')),
            sa.Column('advance_paid', sa.Float(), nullable=True, server_default=sa.text('0')),
            sa.Column('balance_due', sa.Float(), nullable=True, server_default=sa.text('0')),
            sa.Column('notes', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(['request_id'], ['inbound_request.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('request_id'),
        )

    if 'guide_payment_sheet_item' not in existing:
        op.create_table(
            'guide_payment_sheet_item',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('sheet_id', sa.Integer(), nullable=False),
            sa.Column('description', sa.String(500), nullable=False),
            sa.Column('quantity', sa.Float(), nullable=True, server_default=sa.text('1')),
            sa.Column('unit', sa.String(50), nullable=True),
            sa.Column('rate', sa.Float(), nullable=True, server_default=sa.text('0')),
            sa.Column('amount', sa.Float(), nullable=True, server_default=sa.text('0')),
            sa.Column('notes', sa.Text(), nullable=True),
            sa.Column('sort_order', sa.Integer(), nullable=True, server_default=sa.text('0')),
            sa.ForeignKeyConstraint(['sheet_id'], ['guide_payment_sheet.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id'),
        )


def downgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing = set(inspector.get_table_names())

    if 'guide_payment_sheet_item' in existing:
        op.drop_table('guide_payment_sheet_item')
    if 'guide_payment_sheet' in existing:
        op.drop_table('guide_payment_sheet')
    if 'guide_expense_sheet_item' in existing:
        op.drop_table('guide_expense_sheet_item')
    if 'guide_expense_sheet' in existing:
        op.drop_table('guide_expense_sheet')
