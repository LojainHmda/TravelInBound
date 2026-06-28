"""add inbound_invoice_line table

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-06-28 23:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b2c3d4e5f6a7'
down_revision = 'a1b2c3d4e5f6'
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing = set(inspector.get_table_names())

    if 'inbound_invoice_line' not in existing:
        op.create_table(
            'inbound_invoice_line',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('request_id', sa.Integer(), nullable=False),
            sa.Column('invoice_type', sa.String(20), nullable=False, server_default=sa.text("'customer'")),
            sa.Column('line_order', sa.Integer(), nullable=True, server_default=sa.text('0')),
            sa.Column('description', sa.String(500), nullable=False),
            sa.Column('quantity', sa.Float(), nullable=True, server_default=sa.text('1')),
            sa.Column('unit_price', sa.Float(), nullable=True, server_default=sa.text('0')),
            sa.Column('currency', sa.String(3), nullable=True, server_default=sa.text("'USD'")),
            sa.Column('line_total', sa.Float(), nullable=True, server_default=sa.text('0')),
            sa.Column('category', sa.String(100), nullable=True),
            sa.Column('notes', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(['request_id'], ['inbound_request.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id'),
        )


def downgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing = set(inspector.get_table_names())

    if 'inbound_invoice_line' in existing:
        op.drop_table('inbound_invoice_line')
