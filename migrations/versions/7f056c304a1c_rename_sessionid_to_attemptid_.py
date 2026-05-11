"""rename_sessionId_to_attemptId_measurements

Revision ID: 7f056c304a1c
Revises: 6502cf35be9b
Create Date: 2026-05-11 10:57:42.974243

"""
from alembic import op
import sqlalchemy as sa

revision = '7f056c304a1c'
down_revision = '6502cf35be9b'
branch_labels = None
depends_on = None

TABLES = [
    'GpsMeasurement',
    'CanMeasurement',
    'StabilityMeasurement',
    'RotativoMeasurement',
    'DataQualityMetrics',
    'Evidence',
]


def upgrade():
    for table in TABLES:
        with op.batch_alter_table(table, schema=None) as batch_op:
            batch_op.alter_column('sessionId', new_column_name='attemptId')

    with op.batch_alter_table('ArchivoSubido', schema=None) as batch_op:
        batch_op.alter_column('sessionId', new_column_name='attemptId')


def downgrade():
    for table in TABLES:
        with op.batch_alter_table(table, schema=None) as batch_op:
            batch_op.alter_column('attemptId', new_column_name='sessionId')

    with op.batch_alter_table('ArchivoSubido', schema=None) as batch_op:
        batch_op.alter_column('attemptId', new_column_name='sessionId')
