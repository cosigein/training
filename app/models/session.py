"""
Modelo central del dominio Training: Attempt (intento de evaluación).

NOTA: el archivo se mantiene como `session.py` por inercia (el blueprint URL es
`/sessions/`), pero las clases internas son del dominio Training:
  - Attempt        (ex-Session)
  - GpsMeasurement, StabilityMeasurement, RotativoMeasurement, CanMeasurement (RawSamples)
  - DataQualityMetrics
  - Evidence
  - AttemptUploadLog (ex-SessionUploadLog)

Invariantes (PDF §6, §12):
- Una vez `closedAt` está poblado, `score` y `scoreBreakdown` NO cambian (frozen).
- `criteriaVersionPinned`, `normalizerVersionPinned`, `detectorVersionPinned` se
  capturan al crear el Attempt y NO se modifican nunca.
"""
from datetime import datetime
from enum import Enum
from sqlalchemy.dialects.postgresql import JSONB, TIMESTAMP, UUID
from sqlalchemy import text
from app.extensions import db


class AttemptStatus(Enum):
    OPEN = "OPEN"                              # En curso (kiosko activo)
    PROCESSING = "PROCESSING"                  # Datos llegando, scoring corriendo
    CLOSED = "CLOSED"                          # Cerrado, score frozen
    ABANDONED = "ABANDONED"                    # Alumno no completó (cuenta como 0)
    ABORTED_TECHNICAL = "ABORTED_TECHNICAL"    # Fallo del sistema (NO cuenta)
    INVALIDATED = "INVALIDATED"                # Anulado por error administrativo


class Attempt(db.Model):
    __tablename__ = "Attempt"

    id = db.Column(db.String, primary_key=True, server_default=text("gen_random_uuid()"))

    # Identidad y org
    organizationId = db.Column(db.String, db.ForeignKey("Organization.id", ondelete="CASCADE"), nullable=False)
    vehicleId = db.Column(db.String, db.ForeignKey("Vehicle.id", ondelete="CASCADE"), nullable=False)
    uploadedById = db.Column(db.String, db.ForeignKey("User.id", ondelete="SET NULL"))   # quién hizo el upload

    # Vínculo Training (denormalizado para queries rápidas de ranking)
    enrollmentId = db.Column(db.String, db.ForeignKey("Enrollment.id", ondelete="SET NULL"))
    convocatoriaId = db.Column(db.String, db.ForeignKey("Convocatoria.id", ondelete="SET NULL"))
    studentId = db.Column(db.String, db.ForeignKey("User.id", ondelete="SET NULL"))
    routeId = db.Column(db.String)
    kioskCode = db.Column(db.String)
    attemptNumber = db.Column(db.Integer, default=1)

    # Tiempos
    startTime = db.Column(db.DateTime, nullable=False)
    endTime = db.Column(db.DateTime)
    closedAt = db.Column(db.DateTime)            # frozen_at del PDF — cuando deja de ser modificable
    sequence = db.Column(db.Integer, nullable=False)
    sessionNumber = db.Column(db.Integer, nullable=False)

    # Estado
    status = db.Column(db.Enum(AttemptStatus), default=AttemptStatus.OPEN, nullable=False)
    source = db.Column(db.String, nullable=False)   # "kiosk" | "file_import" | "webfleet"

    # Scoring (PDF §6)
    scoreRaw = db.Column(db.Float)                  # nota antes de penalizaciones
    score = db.Column(db.Float)                     # nota final 0-10
    scoreBreakdown = db.Column(JSONB)               # {familia: nota, ...} audit trail
    scoreExplanation = db.Column(db.Text)           # explicación pedagógica granular
    dataQuality = db.Column(JSONB)                  # {gaps: [], confidenceScore: 0.95, ...}

    # Versionado pinned al CREAR (PDF §12.4) — INMUTABLE
    criteriaVersionPinned = db.Column(db.String)
    normalizerVersionPinned = db.Column(db.String)
    detectorVersionPinned = db.Column(db.String)

    # Telemetría matched (legacy fleet — útil para distancia/duración del recorrido)
    weatherConditions = db.Column(JSONB)
    matcheddistance = db.Column(db.Float)
    matchedduration = db.Column(db.Float)
    matchedgeometry = db.Column(db.String)
    matchedconfidence = db.Column(db.Float)
    processingversion = db.Column(db.String(20), default="1.0")

    # Invalidación administrativa
    invalidatedAt = db.Column(db.DateTime)
    invalidatedBy = db.Column(db.String, db.ForeignKey("User.id", ondelete="SET NULL"))
    invalidatedReason = db.Column(db.String)

    # Audit trail
    auditLog = db.Column(JSONB, default=list)

    # Legacy: vínculo a Driver (instructor humano), nullable; no se usa en Training puro
    conductorId = db.Column(UUID(as_uuid=True), db.ForeignKey("conductores.id", ondelete="SET NULL"))

    createdAt = db.Column(db.DateTime, default=datetime.utcnow)
    updatedAt = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __init__(self, **kwargs):
        super(Attempt, self).__init__(**kwargs)


    @property
    def distance(self):
        return self.matcheddistance or 0.0

    # Relationships
    organization = db.relationship("Organization", back_populates="attempts")
    vehicle = db.relationship("Vehicle", back_populates="attempts")
    uploaded_by = db.relationship("User", foreign_keys=[uploadedById], back_populates="attempts_uploaded")
    student = db.relationship("User", foreign_keys=[studentId], back_populates="attempts_as_student")
    invalidator = db.relationship("User", foreign_keys=[invalidatedBy])
    enrollment = db.relationship("Enrollment", backref="attempts")
    convocatoria = db.relationship("Convocatoria", backref="attempts")
    conductor = db.relationship("Driver", back_populates="attempts")

    gps_measurements = db.relationship("GpsMeasurement", back_populates="attempt", cascade="all, delete-orphan")
    can_measurements = db.relationship("CanMeasurement", back_populates="attempt", cascade="all, delete-orphan")
    stability_measurements = db.relationship("StabilityMeasurement", back_populates="attempt", cascade="all, delete-orphan")
    rotativo_measurements = db.relationship("RotativoMeasurement", back_populates="attempt", cascade="all, delete-orphan")
    quality_metrics = db.relationship("DataQualityMetrics", back_populates="attempt", uselist=False, cascade="all, delete-orphan")
    upload_logs = db.relationship("AttemptUploadLog", back_populates="attempt", cascade="all, delete-orphan")
    evidence = db.relationship("Evidence", back_populates="attempt", cascade="all, delete-orphan")
    training_events = db.relationship("AttemptEvent", back_populates="attempt", cascade="all, delete-orphan", passive_deletes=True)


# Aliases legacy para no romper imports existentes durante el refactor incremental.
# Eliminar cuando todos los call-sites usen Attempt directamente.
Session = Attempt
SessionStatus = AttemptStatus


class GpsMeasurement(db.Model):
    __tablename__ = "GpsMeasurement"

    id = db.Column(db.String, primary_key=True, server_default=text("gen_random_uuid()"))
    attemptId = db.Column(db.String, db.ForeignKey("Attempt.id", ondelete="CASCADE"), nullable=False)
    organizationId = db.Column(db.String, db.ForeignKey("Organization.id", ondelete="CASCADE"))

    timestamp = db.Column(db.DateTime, nullable=False)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    altitude = db.Column(db.Float, nullable=False)
    speed = db.Column(db.Float, nullable=False)
    satellites = db.Column(db.Integer, nullable=False)
    quality = db.Column(db.String)
    hdop = db.Column(db.Float)
    fix = db.Column(db.String)
    heading = db.Column(db.Float)
    accuracy = db.Column(db.Float)
    confidence = db.Column(db.Float)

    createdAt = db.Column(db.DateTime, default=datetime.utcnow)
    updatedAt = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    attempt = db.relationship("Attempt", back_populates="gps_measurements")


class CanMeasurement(db.Model):
    __tablename__ = "CanMeasurement"

    id = db.Column(db.String, primary_key=True, server_default=text("gen_random_uuid()"))
    attemptId = db.Column(db.String, db.ForeignKey("Attempt.id", ondelete="CASCADE"), nullable=False)

    timestamp = db.Column(db.DateTime, nullable=False)
    engineRpm = db.Column(db.Float, nullable=False)
    vehicleSpeed = db.Column(db.Float, nullable=False)
    fuelSystemStatus = db.Column(db.Float, nullable=False)
    temperature = db.Column(db.Float)
    absActive = db.Column(db.Boolean)
    brakePressure = db.Column(db.Float)
    espActive = db.Column(db.Boolean)
    gearPosition = db.Column(db.Integer)
    steeringAngle = db.Column(db.Float)
    throttlePosition = db.Column(db.Float)

    createdAt = db.Column(db.DateTime, default=datetime.utcnow)
    updatedAt = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    attempt = db.relationship("Attempt", back_populates="can_measurements")


class StabilityMeasurement(db.Model):
    __tablename__ = "StabilityMeasurement"

    id = db.Column(db.String, primary_key=True, server_default=text("gen_random_uuid()"))
    attemptId = db.Column(db.String, db.ForeignKey("Attempt.id", ondelete="CASCADE"), nullable=False)
    organizationId = db.Column(db.String, db.ForeignKey("Organization.id", ondelete="CASCADE"))

    timestamp = db.Column(db.DateTime, nullable=False)
    ax = db.Column(db.Float, nullable=False)
    ay = db.Column(db.Float, nullable=False)
    az = db.Column(db.Float, nullable=False)
    gx = db.Column(db.Float, nullable=False)
    gy = db.Column(db.Float, nullable=False)
    gz = db.Column(db.Float, nullable=False)
    roll = db.Column(db.Float)
    pitch = db.Column(db.Float)
    yaw = db.Column(db.Float)

    isDRSHigh = db.Column(db.Boolean, default=False)
    isLTRCritical = db.Column(db.Boolean, default=False)
    isLateralGForceHigh = db.Column(db.Boolean, default=False)
    temperature = db.Column(db.Float)
    accmag = db.Column(db.Float, default=0)
    si = db.Column(db.Float, default=0)
    confidence = db.Column(db.Float)

    createdAt = db.Column(db.DateTime, default=datetime.utcnow)
    updatedAt = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    attempt = db.relationship("Attempt", back_populates="stability_measurements")


class RotativoMeasurement(db.Model):
    __tablename__ = "RotativoMeasurement"

    id = db.Column(db.String, primary_key=True, server_default=text("gen_random_uuid()"))
    attemptId = db.Column(db.String, db.ForeignKey("Attempt.id", ondelete="CASCADE"), nullable=False)
    organizationId = db.Column(db.String, db.ForeignKey("Organization.id", ondelete="CASCADE"))

    timestamp = db.Column(db.DateTime, nullable=False)
    state = db.Column(db.String, nullable=False)
    key = db.Column(db.Integer)

    createdAt = db.Column(db.DateTime, default=datetime.utcnow)
    updatedAt = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    attempt = db.relationship("Attempt", back_populates="rotativo_measurements")


class DataQualityMetrics(db.Model):
    __tablename__ = "DataQualityMetrics"

    id = db.Column(db.String, primary_key=True, server_default=text("(gen_random_uuid())::text"))
    attemptId = db.Column(db.String, db.ForeignKey("Attempt.id", ondelete="CASCADE"), unique=True, nullable=False)

    gpsTotal = db.Column(db.Integer, default=0)
    gpsValidas = db.Column(db.Integer, default=0)
    gpsSinSenal = db.Column(db.Integer, default=0)
    gpsInterpoladas = db.Column(db.Integer, default=0)
    porcentajeGPSValido = db.Column(db.Float, default=0.0)
    estabilidadTotal = db.Column(db.Integer, default=0)
    estabilidadValidas = db.Column(db.Integer, default=0)
    rotativoTotal = db.Column(db.Integer, default=0)
    rotativoValidas = db.Column(db.Integer, default=0)
    problemas = db.Column(JSONB, default=[])

    createdAt = db.Column(db.DateTime, default=datetime.utcnow)

    attempt = db.relationship("Attempt", back_populates="quality_metrics")


class Evidence(db.Model):
    __tablename__ = "Evidence"

    id = db.Column(db.String, primary_key=True, server_default=text("gen_random_uuid()"))
    attemptId = db.Column(db.String, db.ForeignKey("Attempt.id", ondelete="CASCADE"), nullable=False)
    gpsMeasurementId = db.Column(db.String, db.ForeignKey("GpsMeasurement.id", ondelete="SET NULL"))
    stabilityMeasurementId = db.Column(db.String, db.ForeignKey("StabilityMeasurement.id", ondelete="SET NULL"))
    eventId = db.Column(db.String)

    type = db.Column(db.String, nullable=False)
    confidence = db.Column(db.Float, nullable=False)
    method = db.Column(db.String, nullable=False)
    source = db.Column(JSONB)
    validated = db.Column(JSONB)
    meta_data = db.Column('metadata', JSONB)

    createdAt = db.Column(db.DateTime, default=datetime.utcnow)

    attempt = db.relationship("Attempt", back_populates="evidence")


class AttemptUploadLog(db.Model):
    __tablename__ = "AttemptUploadLog"

    id = db.Column(db.String, primary_key=True, server_default=text("gen_random_uuid()"))
    attemptId = db.Column(db.String, db.ForeignKey("Attempt.id", ondelete="CASCADE"), nullable=False)
    userId = db.Column(db.String, db.ForeignKey("User.id", ondelete="CASCADE"), nullable=False)

    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String, nullable=False)
    error = db.Column(db.String)
    source = db.Column(db.String, nullable=False)

    attempt = db.relationship("Attempt", back_populates="upload_logs")


# Alias legacy
SessionUploadLog = AttemptUploadLog
