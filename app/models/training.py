"""
Modelos del dominio Training (oposición de conductor de camión de bomberos).

Diseñados según el PDF "Training - Documentación completa" §2, §3, §9.
NO mezclar con los modelos de telemetría legacy (session.py, vehicle.py, event.py, etc.).
"""
from datetime import datetime
from enum import Enum
from sqlalchemy import text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from app.extensions import db


class ConvocatoriaStatus(Enum):
    OPEN = "OPEN"          # En curso, ranking actualizable diariamente
    PREVIEW = "PREVIEW"    # Admin pidió preview de cierre, sin compromiso
    CLOSING = "CLOSING"    # Admin #1 inició cierre, esperando confirmación de admin #2
    CLOSED = "CLOSED"      # Cerrada con acta firmada (revertible 24h por SUPER_ADMIN)
    LOCKED = "LOCKED"      # Cerrada irrevocablemente (pasó la ventana de 24h)


class EnrollmentStatus(Enum):
    ACTIVE = "ACTIVE"            # Inscripción válida, alumno puede hacer intentos
    COMPLETED = "COMPLETED"      # Alumno completó todos los intentos disponibles
    INVALIDATED = "INVALIDATED"  # Inscripción anulada por error o decisión administrativa


class Route(db.Model):
    """
    Catálogo de rutas (recorridos) por organización.

    Convocatoria.routePrincipal, Enrollment.routeId y Attempt.routeId siguen
    almacenando el `code` de la ruta como String — no hay FK formal, la
    integridad la garantiza la UI mediante selects poblados con rutas activas.

    Soft-delete: nunca DELETE real, solo `active=False`, para evitar dejar
    referencias huérfanas en convocatorias/inscripciones existentes.
    """
    __tablename__ = "Route"
    __table_args__ = (
        UniqueConstraint("code", "organizationId", name="uq_route_code_per_org"),
    )

    id = db.Column(db.String, primary_key=True, server_default=text("gen_random_uuid()"))
    organizationId = db.Column(db.String, db.ForeignKey("Organization.id", ondelete="CASCADE"), nullable=False)

    code = db.Column(db.String, nullable=False)              # identificador corto (RECORRIDO_A, PRINCIPAL...)
    name = db.Column(db.String, nullable=False)              # nombre legible
    description = db.Column(db.Text)

    distanceKm = db.Column(db.Float)                          # opcional
    durationMin = db.Column(db.Integer)                       # opcional, minutos esperados

    active = db.Column(db.Boolean, default=True, nullable=False)

    createdAt = db.Column(db.DateTime, default=datetime.utcnow)
    updatedAt = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Convocatoria(db.Model):
    """
    Una convocatoria es un proceso completo de oposición:
    abre → alumnos hacen intentos → ranking diario → cierre formal con acta.

    Invariantes (PDF §9):
    - Cierre requiere DOS admins distintos (closureInitiatedBy != closureConfirmedBy).
    - Una vez CLOSED, hay ventana de 24h para reversa por SUPER_ADMIN.
    - Una vez LOCKED, NADIE puede modificarla.
    - criteriaVersion / normalizerVersion / detectorVersion quedan congelados al crear cada Attempt.
    """
    __tablename__ = "Convocatoria"
    __table_args__ = (
        UniqueConstraint("name", "organizationId", name="uq_convocatoria_name_per_org"),
    )

    id = db.Column(db.String, primary_key=True, server_default=text("gen_random_uuid()"))

    # Identidad
    organizationId = db.Column(db.String, db.ForeignKey("Organization.id", ondelete="CASCADE"), nullable=False)
    name = db.Column(db.String, nullable=False)
    description = db.Column(db.Text)

    # Reglas de la convocatoria (V1: una sola ruta principal)
    routePrincipal = db.Column(db.String, nullable=False)
    plazas = db.Column(db.Integer, nullable=False)
    umbralMin = db.Column(db.Float, default=5.0)             # nota mínima 0-10 para considerarse APTO
    pesosPorFamilia = db.Column(JSONB, default=dict)         # {"estabilidad": 0.4, "velocidad": 0.3, ...}

    # Versionado pinned al ABRIR la convocatoria (PDF §12.4)
    criteriaVersion = db.Column(db.String, nullable=False)
    normalizerVersion = db.Column(db.String, nullable=False)
    detectorVersion = db.Column(db.String, nullable=False)

    # Ciclo de vida
    status = db.Column(db.Enum(ConvocatoriaStatus), default=ConvocatoriaStatus.OPEN, nullable=False)
    openedAt = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    closedAt = db.Column(db.DateTime)                        # NULL hasta cierre

    # Cierre 3 pasos (PDF §9.1)
    closureInitiatedAt = db.Column(db.DateTime)
    closureInitiatedBy = db.Column(db.String, db.ForeignKey("User.id", ondelete="SET NULL"))
    closureConfirmedBy = db.Column(db.String, db.ForeignKey("User.id", ondelete="SET NULL"))

    # Acta (PDF §9.1)
    finalRankingSnapshot = db.Column(JSONB)                  # ranking definitivo + APTO/NO_APTO
    acta = db.Column(db.LargeBinary)                         # PDF en bytea (V1)
    actaSignatureHash = db.Column(db.String)                 # SHA256 del PDF para inmutabilidad

    # Ventana de reversa (PDF §9.3)
    reverseWindowUntil = db.Column(db.DateTime)              # closedAt + 24h
    reversedAt = db.Column(db.DateTime)
    reversedBy = db.Column(db.String, db.ForeignKey("User.id", ondelete="SET NULL"))
    reversalReason = db.Column(db.Text)

    createdAt = db.Column(db.DateTime, default=datetime.utcnow)
    updatedAt = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relaciones
    organization = db.relationship("Organization", back_populates="convocatorias")
    enrollments = db.relationship("Enrollment", back_populates="convocatoria", cascade="all, delete-orphan", passive_deletes=True)
    rankings = db.relationship("Ranking", back_populates="convocatoria", cascade="all, delete-orphan", passive_deletes=True)
    initiator = db.relationship("User", foreign_keys=[closureInitiatedBy], back_populates="convocatorias_initiated")
    confirmer = db.relationship("User", foreign_keys=[closureConfirmedBy], back_populates="convocatorias_confirmed")
    reverser = db.relationship("User", foreign_keys=[reversedBy])


class Enrollment(db.Model):
    """
    Inscripción de un alumno en una convocatoria concreta.
    Un humano puede tener varias enrollments (varias convocatorias),
    pero NO dos enrollments en la misma convocatoria.
    """
    __tablename__ = "Enrollment"
    __table_args__ = (
        UniqueConstraint("convocatoriaId", "studentId", name="uq_enrollment_one_per_student_per_convocatoria"),
    )

    id = db.Column(db.String, primary_key=True, server_default=text("gen_random_uuid()"))

    convocatoriaId = db.Column(db.String, db.ForeignKey("Convocatoria.id", ondelete="CASCADE"), nullable=False)
    studentId = db.Column(db.String, db.ForeignKey("User.id", ondelete="CASCADE"), nullable=False)
    organizationId = db.Column(db.String, db.ForeignKey("Organization.id", ondelete="CASCADE"), nullable=False)

    routeId = db.Column(db.String)                           # ruta asignada (puede ser PRINCIPAL u otra)
    status = db.Column(db.Enum(EnrollmentStatus), default=EnrollmentStatus.ACTIVE, nullable=False)
    attemptsCount = db.Column(db.Integer, default=0)         # cuenta de attempts cerrados

    enrolledAt = db.Column(db.DateTime, default=datetime.utcnow)
    withdrawnAt = db.Column(db.DateTime)

    createdAt = db.Column(db.DateTime, default=datetime.utcnow)
    updatedAt = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relaciones
    convocatoria = db.relationship("Convocatoria", back_populates="enrollments")
    student = db.relationship("User", back_populates="enrollments")
    organization = db.relationship("Organization", back_populates="enrollments")


# ─────────────────────────────────────────────────────────────────────────────
# AttemptEvent — eventos de penalización detectados durante un intento (PDF §6.2)
# ─────────────────────────────────────────────────────────────────────────────

class AttemptEventType(Enum):
    HARSH_BRAKING = "HARSH_BRAKING"
    SPEEDING = "SPEEDING"
    DEVIATION = "DEVIATION"
    ACCELERATION_LATERAL = "ACCELERATION_LATERAL"
    HARSH_ACCELERATION = "HARSH_ACCELERATION"


class EventSeverity(Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class EventSource(Enum):
    DOBACK_ELITE = "DOBACK_ELITE"
    WEBFLEET = "WEBFLEET"


class AttemptEvent(db.Model):
    """
    Penalización detectada durante un intento.

    NO confundir con el modelo legacy `Event` (en `app/models/event.py`), que
    es del dominio fleet genérico. Este es del dominio Training: un evento que
    resta puntos al score de un Attempt concreto.

    Invariantes (PDF §6.2):
    - `source` y `confidence` son ortogonales (D8): source = de dónde vino,
      confidence = qué tan confiable es la detección.
    - `penaltyPoints` lo decide el detector con la criteria_version del Attempt.
    """
    __tablename__ = "AttemptEvent"

    id = db.Column(db.String, primary_key=True, server_default=text("gen_random_uuid()"))
    attemptId = db.Column(db.String, db.ForeignKey("Attempt.id", ondelete="CASCADE"), nullable=False)
    organizationId = db.Column(db.String, db.ForeignKey("Organization.id", ondelete="CASCADE"), nullable=False)

    type = db.Column(db.Enum(AttemptEventType), nullable=False)
    severity = db.Column(db.Enum(EventSeverity), nullable=False)
    source = db.Column(db.Enum(EventSource), nullable=False)
    confidence = db.Column(db.Float)         # 0..1
    penaltyPoints = db.Column(db.Float, default=0.0)

    timestamp = db.Column(db.DateTime, nullable=False)
    payload = db.Column(JSONB)               # detalles específicos del detector

    createdAt = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.Index("ix_attemptevent_attempt_ts", "attemptId", "timestamp"),
        db.Index("ix_attemptevent_type", "type"),
    )

    # Relaciones
    attempt = db.relationship("Attempt", back_populates="training_events")


# ─────────────────────────────────────────────────────────────────────────────
# Ranking — snapshot insert-only del ranking de una convocatoria (PDF §3.1, §3.2)
# ─────────────────────────────────────────────────────────────────────────────

class RankingStatus(Enum):
    PROVISIONAL = "PROVISIONAL"   # snapshot diario mientras la convocatoria está OPEN
    DEFINITIVE = "DEFINITIVE"     # snapshot final al cierre (CLOSED/LOCKED)


class Ranking(db.Model):
    """
    Snapshot del ranking. **Insert-only**: nunca se hace UPDATE ni DELETE.
    El cron de las 06:00 AM (Europe/Madrid) genera un snapshot por convocatoria
    OPEN. Al cierre, se inserta un último snapshot con `status=DEFINITIVE`.

    Invariantes (PDF §3.2):
    - Insert-only: enforced a nivel servicio/cron (sin UPDATE/DELETE).
    - El ranking final (DEFINITIVE) no se modifica salvo `voidedAt/voidedBy/voidedReason`
      en una reversa de cierre.
    """
    __tablename__ = "Ranking"

    id = db.Column(db.String, primary_key=True, server_default=text("gen_random_uuid()"))

    convocatoriaId = db.Column(db.String, db.ForeignKey("Convocatoria.id", ondelete="CASCADE"), nullable=False)
    attemptId = db.Column(db.String, db.ForeignKey("Attempt.id", ondelete="SET NULL"))
    enrollmentId = db.Column(db.String, db.ForeignKey("Enrollment.id", ondelete="SET NULL"))
    studentId = db.Column(db.String, db.ForeignKey("User.id", ondelete="SET NULL"))

    score = db.Column(db.Float, nullable=False)             # snapshot del score
    rank = db.Column(db.Integer, nullable=False)            # puesto 1, 2, 3, ...
    status = db.Column(db.Enum(RankingStatus), default=RankingStatus.PROVISIONAL, nullable=False)
    snapshotAt = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # Solo se setea cuando un cierre es revertido (PDF §9.3)
    voidedAt = db.Column(db.DateTime)
    voidedBy = db.Column(db.String, db.ForeignKey("User.id", ondelete="SET NULL"))
    voidedReason = db.Column(db.Text)

    createdAt = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.Index("ix_ranking_convocatoria_snapshot", "convocatoriaId", "snapshotAt"),
        db.Index("ix_ranking_convocatoria_status", "convocatoriaId", "status"),
    )

    # Relaciones
    convocatoria = db.relationship("Convocatoria", back_populates="rankings")


# ─────────────────────────────────────────────────────────────────────────────
# TrainingAuditLog — audit trail tipado de acciones administrativas (PDF §8.5)
# ─────────────────────────────────────────────────────────────────────────────

class AuditAction(Enum):
    # Convocatoria
    CONVOCATORIA_CREATED = "CONVOCATORIA_CREATED"
    CONVOCATORIA_EDITED = "CONVOCATORIA_EDITED"
    CONVOCATORIA_CLOSURE_INITIATED = "CONVOCATORIA_CLOSURE_INITIATED"
    CONVOCATORIA_CLOSURE_CONFIRMED = "CONVOCATORIA_CLOSURE_CONFIRMED"
    CONVOCATORIA_CLOSURE_ABORTED = "CONVOCATORIA_CLOSURE_ABORTED"
    CONVOCATORIA_CLOSURE_REVERSED = "CONVOCATORIA_CLOSURE_REVERSED"
    # Enrollment
    ENROLLMENT_CREATED = "ENROLLMENT_CREATED"
    ENROLLMENT_REMOVED = "ENROLLMENT_REMOVED"
    # Attempt
    ATTEMPT_CREATED = "ATTEMPT_CREATED"
    ATTEMPT_CLOSED = "ATTEMPT_CLOSED"
    ATTEMPT_INVALIDATED = "ATTEMPT_INVALIDATED"
    SCORE_CALCULATED = "SCORE_CALCULATED"
    # Ranking
    RANKING_PUBLISHED = "RANKING_PUBLISHED"
    # GDPR
    GDPR_EXPORT_REQUESTED = "GDPR_EXPORT_REQUESTED"
    GDPR_FORGET_REQUESTED = "GDPR_FORGET_REQUESTED"
    GDPR_FORGET_APPROVED = "GDPR_FORGET_APPROVED"
    # Sistema
    USER_ROLE_CHANGED = "USER_ROLE_CHANGED"
    LOGIN_FAILED = "LOGIN_FAILED"


class TrainingAuditLog(db.Model):
    """
    Audit trail inmutable de acciones críticas del dominio Training.

    NO confundir con el modelo legacy `AuditLog` (`app/models/audit.py`), que
    tiene un dominio distinto (decisiones de calidad de datos).

    Invariantes (PDF §8.5):
    - Insert-only — sin UPDATE ni DELETE.
    - Si el INSERT falla, la acción que se quería auditar también debe fallar
      (no hay acción sin trazabilidad).
    """
    __tablename__ = "TrainingAuditLog"

    id = db.Column(db.String, primary_key=True, server_default=text("gen_random_uuid()"))

    actorId = db.Column(db.String, db.ForeignKey("User.id", ondelete="SET NULL"))
    actorRole = db.Column(db.String)         # snapshot del rol al momento (no FK)

    action = db.Column(db.Enum(AuditAction), nullable=False)
    resourceType = db.Column(db.String, nullable=False)   # "Convocatoria", "Attempt", ...
    resourceId = db.Column(db.String, nullable=False)     # uuid del recurso afectado
    delta = db.Column(JSONB)                              # qué cambió

    ipAddress = db.Column(db.String)
    userAgent = db.Column(db.String)
    organizationId = db.Column(db.String, db.ForeignKey("Organization.id", ondelete="SET NULL"))

    createdAt = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        db.Index("ix_traininglog_actor", "actorId"),
        db.Index("ix_traininglog_action_ts", "action", "createdAt"),
        db.Index("ix_traininglog_resource", "resourceType", "resourceId"),
    )


# ─────────────────────────────────────────────────────────────────────────────
# RfidCard — tarjeta física que identifica al alumno en el kiosko (PDF §5.4)
# ─────────────────────────────────────────────────────────────────────────────

class RfidCard(db.Model):
    """
    Tarjeta RFID asignada a un alumno. Una tarjeta puede revocarse y reasignarse:
    el campo `active=false` o `revokedAt != null` la inhabilita.

    Invariante:
    - Solo puede existir UNA tarjeta activa con un `uid` dado a la vez.
      Implementado como índice único parcial (ver `__table_args__`).
    """
    __tablename__ = "RfidCard"

    id = db.Column(db.String, primary_key=True, server_default=text("gen_random_uuid()"))
    uid = db.Column(db.String, nullable=False)              # ID físico del lector
    organizationId = db.Column(db.String, db.ForeignKey("Organization.id", ondelete="CASCADE"), nullable=False)
    assignedTo = db.Column(db.String, db.ForeignKey("User.id", ondelete="SET NULL"))
    assignedAt = db.Column(db.DateTime)
    revokedAt = db.Column(db.DateTime)
    active = db.Column(db.Boolean, default=True, nullable=False)

    createdAt = db.Column(db.DateTime, default=datetime.utcnow)
    updatedAt = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        db.Index(
            "ix_rfid_uid_active_unique",
            "uid",
            unique=True,
            postgresql_where=db.text('active = true AND "revokedAt" IS NULL'),
        ),
        db.Index("ix_rfid_assigned", "assignedTo"),
    )

    student = db.relationship("User", foreign_keys=[assignedTo])


# ─────────────────────────────────────────────────────────────────────────────
# AuditRequest — solicitud formal de auditoría de un intento (PDF §8, T12)
# ─────────────────────────────────────────────────────────────────────────────

class AuditStatus(Enum):
    PENDING = "PENDING"           # Recibida, sin revisar
    REVIEWING = "REVIEWING"       # Manager la está revisando
    CONFIRMED = "CONFIRMED"       # Auditoría confirma el resultado original
    REEVALUATED = "REEVALUATED"   # Se generó un nuevo attempt
    REJECTED = "REJECTED"         # Solicitud sin mérito


class AuditRequest(db.Model):
    """
    Solicitud formal de revisión de un Attempt. La genera el alumno (o el admin)
    cuando considera que el score calculado tiene un error.

    Invariantes:
    - `reason` debe tener al menos 30 caracteres.
    - Insert-only en cuanto a `originalAttemptId` y `enrollmentId`.
    - `resolution` se rellena al pasar a CONFIRMED / REEVALUATED / REJECTED.
    """
    __tablename__ = "AuditRequest"

    id = db.Column(db.String, primary_key=True, server_default=text("gen_random_uuid()"))
    organizationId = db.Column(db.String, db.ForeignKey("Organization.id", ondelete="CASCADE"), nullable=False)

    originalAttemptId = db.Column(db.String, db.ForeignKey("Attempt.id", ondelete="SET NULL"))
    enrollmentId = db.Column(db.String, db.ForeignKey("Enrollment.id", ondelete="SET NULL"))
    requestedBy = db.Column(db.String, db.ForeignKey("User.id", ondelete="SET NULL"))  # alumno o admin

    reason = db.Column(db.Text, nullable=False)              # ≥30 chars
    status = db.Column(db.Enum(AuditStatus), default=AuditStatus.PENDING, nullable=False)

    reviewedBy = db.Column(db.String, db.ForeignKey("User.id", ondelete="SET NULL"))
    reviewedAt = db.Column(db.DateTime)
    resolution = db.Column(db.Text)

    filedAfterClose = db.Column(db.Boolean, default=False)   # si se presentó tras cierre de conv

    createdAt = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updatedAt = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        db.Index("ix_auditrequest_org_status", "organizationId", "status"),
        db.Index("ix_auditrequest_attempt", "originalAttemptId"),
        db.Index("ix_auditrequest_enrollment", "enrollmentId"),
    )

    original_attempt = db.relationship("Attempt", foreign_keys=[originalAttemptId])
    enrollment = db.relationship("Enrollment", foreign_keys=[enrollmentId])
    requester = db.relationship("User", foreign_keys=[requestedBy])
    reviewer = db.relationship("User", foreign_keys=[reviewedBy])


# ─────────────────────────────────────────────────────────────────────────────
# GdprDataExport — solicitud de exportación de datos personales (GDPR art. 20)
# ─────────────────────────────────────────────────────────────────────────────

class GdprStatus(Enum):
    PENDING = "PENDING"
    GENERATING = "GENERATING"
    READY = "READY"
    EXPIRED = "EXPIRED"
    ERROR = "ERROR"


class GdprForgetStatus(Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class GdprDataExport(db.Model):
    """Exportación de datos personales solicitada por un alumno (GDPR art. 20)."""
    __tablename__ = "GdprDataExport"

    id = db.Column(db.String, primary_key=True, server_default=text("gen_random_uuid()"))
    studentId = db.Column(db.String, db.ForeignKey("User.id", ondelete="CASCADE"), nullable=False)
    organizationId = db.Column(db.String, db.ForeignKey("Organization.id", ondelete="CASCADE"), nullable=False)

    requestedAt = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    status = db.Column(db.Enum(GdprStatus), default=GdprStatus.PENDING, nullable=False)
    generatedAt = db.Column(db.DateTime)
    exportData = db.Column(db.LargeBinary)  # ZIP en bytea (V1)
    expiresAt = db.Column(db.DateTime)      # requestedAt + 7 días

    __table_args__ = (
        db.Index("ix_gdprexport_student_status", "studentId", "status"),
    )

    student = db.relationship("User", foreign_keys=[studentId])


class GdprForgetRequest(db.Model):
    """Solicitud de borrado/anonimización por un alumno (GDPR art. 17)."""
    __tablename__ = "GdprForgetRequest"

    id = db.Column(db.String, primary_key=True, server_default=text("gen_random_uuid()"))
    studentId = db.Column(db.String, db.ForeignKey("User.id", ondelete="SET NULL"))
    organizationId = db.Column(db.String, db.ForeignKey("Organization.id", ondelete="CASCADE"), nullable=False)

    reason = db.Column(db.Text)
    status = db.Column(db.Enum(GdprForgetStatus), default=GdprForgetStatus.PENDING, nullable=False)
    approvedBy = db.Column(db.String, db.ForeignKey("User.id", ondelete="SET NULL"))
    approvedAt = db.Column(db.DateTime)

    requestedAt = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        db.Index("ix_gdprforget_org_status", "organizationId", "status"),
    )

    student = db.relationship("User", foreign_keys=[studentId])
    approver = db.relationship("User", foreign_keys=[approvedBy])
