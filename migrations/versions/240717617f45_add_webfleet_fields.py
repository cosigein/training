"""add_webfleet_fields

Revision ID: 240717617f45
Revises: dd415d61647d
Create Date: 2026-05-08 08:54:07.983097

Agrega campos para la integración con Webfleet (D-WF-001):
- Vehicle.webfleetObjectNo: mapeo al objectno de Webfleet.connect.
- Attempt.webfleetSyncedAt + webfleetSyncSource: trazabilidad del último sync.

NOTA: Alembic auto-generó drops de tablas legacy (AuditRequest, AuditLog,
Incident, WeeklyReport, DeliverableVehicle, DailyReview) que no están en
los modelos pero sí en BD. Esos drops fueron eliminados manualmente porque
son destructivos y NO los pidió esta migración.
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '240717617f45'
down_revision = 'dd415d61647d'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('Attempt', schema=None) as batch_op:
        batch_op.add_column(sa.Column('webfleetSyncedAt', sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column('webfleetSyncSource', sa.String(), nullable=True))

    with op.batch_alter_table('Vehicle', schema=None) as batch_op:
        batch_op.add_column(sa.Column('webfleetObjectNo', sa.String(), nullable=True))
        batch_op.create_index(
            batch_op.f('ix_Vehicle_webfleetObjectNo'),
            ['webfleetObjectNo'],
            unique=True,
        )


def downgrade():
    with op.batch_alter_table('Vehicle', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_Vehicle_webfleetObjectNo'))
        batch_op.drop_column('webfleetObjectNo')

    with op.batch_alter_table('Attempt', schema=None) as batch_op:
        batch_op.drop_column('webfleetSyncSource')
        batch_op.drop_column('webfleetSyncedAt')
