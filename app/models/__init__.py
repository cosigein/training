from .auth import Organization, OrganizationConfig, User, UserConfig, OperationalKey
from .vehicle import Vehicle, Fleet, VehicleConfiguration, MaintenanceRecord, MaintenanceSchedule, RealtimePosition
from .session import Attempt, AttemptStatus, AttemptUploadLog, GpsMeasurement, CanMeasurement, StabilityMeasurement, RotativoMeasurement, DataQualityMetrics, Evidence, Session, SessionUploadLog, SessionStatus  # Session/SessionStatus/SessionUploadLog son aliases legacy
from .event import Event, EventVehicle, GestorDeEvento, EjecucionEvento, AccionDisparada, EventCondition, EventoVariableVisible
from .ingestion import IngestionJob, IngestionHistory, ArchivoSubido, FileState, DailyProcessingReport
from .audit import AuditLog, DailyReview, Incident, WeeklyReport, DeliverableVehicle
from .notifications import Alert, AlertRule, Notification
from .training import (
    Convocatoria, Enrollment, ConvocatoriaStatus, EnrollmentStatus,
    AttemptEvent, AttemptEventType, EventSeverity, EventSource,
    Ranking, RankingStatus,
    TrainingAuditLog, AuditAction,
)
