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
    enrollments = db.relationship("Enrollment", back_populates="convocatoria", cascade="all, delete-orphan")
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
