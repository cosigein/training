"""add_doback_identifier_vehicle

Revision ID: c7ee2266219c
Revises: a13bcffb7044
Create Date: 2026-05-11 10:23:15.354376

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'c7ee2266219c'
down_revision = 'a13bcffb7044'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('Vehicle', schema=None) as batch_op:
        batch_op.add_column(sa.Column('dobackIdentifier', sa.String(length=20), nullable=True))
        batch_op.create_index(batch_op.f('ix_Vehicle_dobackIdentifier'), ['dobackIdentifier'], unique=False)


def downgrade():
    with op.batch_alter_table('Vehicle', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_Vehicle_dobackIdentifier'))
        batch_op.drop_column('dobackIdentifier')

    op.create_table('AuditRequest',
    sa.Column('id', sa.VARCHAR(), server_default=sa.text('gen_random_uuid()'), autoincrement=False, nullable=False),
    sa.Column('organizationId', sa.VARCHAR(), autoincrement=False, nullable=False),
    sa.Column('originalAttemptId', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('enrollmentId', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('requestedBy', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('reason', sa.TEXT(), autoincrement=False, nullable=False),
    sa.Column('status', postgresql.ENUM('PENDING', 'REVIEWING', 'CONFIRMED', 'REEVALUATED', 'REJECTED', name='auditstatus'), autoincrement=False, nullable=False),
    sa.Column('reviewedBy', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('reviewedAt', postgresql.TIMESTAMP(), autoincrement=False, nullable=True),
    sa.Column('resolution', sa.TEXT(), autoincrement=False, nullable=True),
    sa.Column('filedAfterClose', sa.BOOLEAN(), autoincrement=False, nullable=True),
    sa.Column('createdAt', postgresql.TIMESTAMP(), autoincrement=False, nullable=False),
    sa.Column('updatedAt', postgresql.TIMESTAMP(), autoincrement=False, nullable=True),
    sa.ForeignKeyConstraint(['enrollmentId'], ['Enrollment.id'], name=op.f('AuditRequest_enrollmentId_fkey'), ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['organizationId'], ['Organization.id'], name=op.f('AuditRequest_organizationId_fkey'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['originalAttemptId'], ['Attempt.id'], name=op.f('AuditRequest_originalAttemptId_fkey'), ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['requestedBy'], ['User.id'], name=op.f('AuditRequest_requestedBy_fkey'), ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['reviewedBy'], ['User.id'], name=op.f('AuditRequest_reviewedBy_fkey'), ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id', name=op.f('AuditRequest_pkey'))
    )
    with op.batch_alter_table('AuditRequest', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_auditrequest_org_status'), ['organizationId', 'status'], unique=False)
        batch_op.create_index(batch_op.f('ix_auditrequest_enrollment'), ['enrollmentId'], unique=False)
        batch_op.create_index(batch_op.f('ix_auditrequest_attempt'), ['originalAttemptId'], unique=False)

    op.create_table('DeliverableVehicle',
    sa.Column('id', sa.VARCHAR(), server_default=sa.text('gen_random_uuid()'), autoincrement=False, nullable=False),
    sa.Column('name', sa.VARCHAR(), autoincrement=False, nullable=False),
    sa.Column('licensePlate', sa.VARCHAR(), autoincrement=False, nullable=False),
    sa.Column('identifier', sa.VARCHAR(), autoincrement=False, nullable=False),
    sa.Column('organizationId', sa.VARCHAR(), autoincrement=False, nullable=False),
    sa.Column('active', sa.BOOLEAN(), autoincrement=False, nullable=True),
    sa.Column('createdAt', postgresql.TIMESTAMP(), autoincrement=False, nullable=True),
    sa.Column('updatedAt', postgresql.TIMESTAMP(), autoincrement=False, nullable=True),
    sa.ForeignKeyConstraint(['organizationId'], ['Organization.id'], name=op.f('DeliverableVehicle_organizationId_fkey'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('DeliverableVehicle_pkey'))
    )
    op.create_table('Incident',
    sa.Column('id', sa.VARCHAR(), server_default=sa.text('gen_random_uuid()'), autoincrement=False, nullable=False),
    sa.Column('vehicleId', sa.VARCHAR(), autoincrement=False, nullable=False),
    sa.Column('organizationId', sa.VARCHAR(), autoincrement=False, nullable=False),
    sa.Column('date', sa.DATE(), autoincrement=False, nullable=False),
    sa.Column('severity', postgresql.ENUM('LOW', 'MEDIUM', 'HIGH', 'CRITICAL', name='incidentseverity'), autoincrement=False, nullable=False),
    sa.Column('description', sa.VARCHAR(), autoincrement=False, nullable=False),
    sa.Column('action', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('status', postgresql.ENUM('OPEN', 'IN_PROGRESS', 'CLOSED', name='incidentstatus'), autoincrement=False, nullable=True),
    sa.Column('closedAt', postgresql.TIMESTAMP(), autoincrement=False, nullable=True),
    sa.Column('closedBy', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('createdAt', postgresql.TIMESTAMP(), autoincrement=False, nullable=True),
    sa.Column('updatedAt', postgresql.TIMESTAMP(), autoincrement=False, nullable=True),
    sa.ForeignKeyConstraint(['organizationId'], ['Organization.id'], name=op.f('Incident_organizationId_fkey'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['vehicleId'], ['DeliverableVehicle.id'], name=op.f('Incident_vehicleId_fkey'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('Incident_pkey'))
    )
    op.create_table('WeeklyReport',
    sa.Column('id', sa.VARCHAR(), server_default=sa.text('gen_random_uuid()'), autoincrement=False, nullable=False),
    sa.Column('weekStartDate', sa.DATE(), autoincrement=False, nullable=False),
    sa.Column('weekEndDate', sa.DATE(), autoincrement=False, nullable=False),
    sa.Column('organizationId', sa.VARCHAR(), autoincrement=False, nullable=False),
    sa.Column('workSummary', sa.VARCHAR(), autoincrement=False, nullable=False),
    sa.Column('incidentsSummary', sa.VARCHAR(), autoincrement=False, nullable=False),
    sa.Column('openIncidents', sa.VARCHAR(), autoincrement=False, nullable=False),
    sa.Column('workPlan', sa.VARCHAR(), autoincrement=False, nullable=False),
    sa.Column('generatedBy', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('generatedAt', postgresql.TIMESTAMP(), autoincrement=False, nullable=True),
    sa.Column('createdAt', postgresql.TIMESTAMP(), autoincrement=False, nullable=True),
    sa.Column('updatedAt', postgresql.TIMESTAMP(), autoincrement=False, nullable=True),
    sa.ForeignKeyConstraint(['organizationId'], ['Organization.id'], name=op.f('WeeklyReport_organizationId_fkey'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('WeeklyReport_pkey'))
    )
    op.create_table('AuditLog',
    sa.Column('id', sa.VARCHAR(), server_default=sa.text('gen_random_uuid()'), autoincrement=False, nullable=False),
    sa.Column('decision', sa.VARCHAR(), autoincrement=False, nullable=False),
    sa.Column('who', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('when', postgresql.TIMESTAMP(), autoincrement=False, nullable=True),
    sa.Column('what', postgresql.JSONB(astext_type=sa.Text()), autoincrement=False, nullable=False),
    sa.Column('why', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('confidence', sa.DOUBLE_PRECISION(precision=53), autoincrement=False, nullable=True),
    sa.Column('organizationId', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('attemptId', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('createdAt', postgresql.TIMESTAMP(), autoincrement=False, nullable=True),
    sa.ForeignKeyConstraint(['attemptId'], ['Attempt.id'], name=op.f('AuditLog_attemptId_fkey'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['organizationId'], ['Organization.id'], name=op.f('AuditLog_organizationId_fkey'), ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id', name=op.f('AuditLog_pkey'))
    )
    op.create_table('DailyReview',
    sa.Column('id', sa.VARCHAR(), server_default=sa.text('gen_random_uuid()'), autoincrement=False, nullable=False),
    sa.Column('reviewDate', sa.DATE(), autoincrement=False, nullable=False),
    sa.Column('vehicleId', sa.VARCHAR(), autoincrement=False, nullable=False),
    sa.Column('organizationId', sa.VARCHAR(), autoincrement=False, nullable=False),
    sa.Column('fileUploaded', postgresql.ENUM('OK', 'REVISAR', 'ERROR', name='deliverablestatus'), autoincrement=False, nullable=True),
    sa.Column('fileSizeStatus', postgresql.ENUM('OK', 'REVISAR', 'ERROR', name='deliverablestatus'), autoincrement=False, nullable=True),
    sa.Column('stabilityStatus', postgresql.ENUM('OK', 'REVISAR', 'ERROR', name='deliverablestatus'), autoincrement=False, nullable=True),
    sa.Column('eventsStatus', postgresql.ENUM('OK', 'REVISAR', 'ERROR', name='deliverablestatus'), autoincrement=False, nullable=True),
    sa.Column('gpsStatus', postgresql.ENUM('OK', 'REVISAR', 'ERROR', name='deliverablestatus'), autoincrement=False, nullable=True),
    sa.Column('rotativeStatus', postgresql.ENUM('OK', 'REVISAR', 'ERROR', name='deliverablestatus'), autoincrement=False, nullable=True),
    sa.Column('canStatus', postgresql.ENUM('OK', 'REVISAR', 'ERROR', name='deliverablestatus'), autoincrement=False, nullable=True),
    sa.Column('overallStatus', postgresql.ENUM('OK', 'REVISAR', 'ERROR', name='deliverablestatus'), autoincrement=False, nullable=True),
    sa.Column('incidentsText', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('actionsText', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('reviewedBy', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('reviewedAt', postgresql.TIMESTAMP(), autoincrement=False, nullable=True),
    sa.Column('createdAt', postgresql.TIMESTAMP(), autoincrement=False, nullable=True),
    sa.Column('updatedAt', postgresql.TIMESTAMP(), autoincrement=False, nullable=True),
    sa.ForeignKeyConstraint(['organizationId'], ['Organization.id'], name=op.f('DailyReview_organizationId_fkey'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['vehicleId'], ['DeliverableVehicle.id'], name=op.f('DailyReview_vehicleId_fkey'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('DailyReview_pkey'))
    )
    # ### end Alembic commands ###
