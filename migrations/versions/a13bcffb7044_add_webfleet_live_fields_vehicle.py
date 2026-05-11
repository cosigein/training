"""add_webfleet_live_fields_vehicle

Revision ID: a13bcffb7044
Revises: 05ecfc2a6886
Create Date: 2026-05-11 10:15:08.204646

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = 'a13bcffb7044'
down_revision = '05ecfc2a6886'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('Vehicle', schema=None) as batch_op:
        batch_op.add_column(sa.Column('webfleetData', postgresql.JSONB(astext_type=sa.Text()), nullable=True))
        batch_op.add_column(sa.Column('webfleetLastSeen', sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column('webfleetVisible', sa.Boolean(), nullable=False, server_default=sa.true()))


def downgrade():
    with op.batch_alter_table('Vehicle', schema=None) as batch_op:
        batch_op.drop_column('webfleetVisible')
        batch_op.drop_column('webfleetLastSeen')
        batch_op.drop_column('webfleetData')
