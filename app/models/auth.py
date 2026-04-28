from datetime import datetime
import uuid
from enum import Enum
from flask_login import UserMixin
from sqlalchemy.dialects.postgresql import JSONB, UUID, TIMESTAMP
from sqlalchemy import text
from app.extensions import db

class UserRole(Enum):
    SUPER_ADMIN = "SUPER_ADMIN"
    ADMIN = "ADMIN"
    MANAGER = "MANAGER"
    STUDENT = "STUDENT"
    OPERATOR = "OPERATOR"   # legacy, sin uso en Training — pendiente de remover
    VIEWER = "VIEWER"       # legacy, sin uso en Training — pendiente de remover

class ReportSchedule(Enum):
    DAILY = "DAILY"
    WEEKLY = "WEEKLY"
    MONTHLY = "MONTHLY"

class Organization(db.Model):
    __tablename__ = "Organization"
    
    id = db.Column(db.String, primary_key=True, server_default=text("gen_random_uuid()"))
    name = db.Column(db.String, nullable=False)
    apiKey = db.Column(db.String, unique=True, nullable=False)
    apiKeyHash = db.Column(db.String, unique=True)
    apiKeyPrefix = db.Column(db.String)
    formacionHabilitada = db.Column(db.Boolean, default=False)
    viewMode = db.Column(db.String, default="STANDARD")
    anonymize = db.Column(db.Boolean, default=False)
    createdAt = db.Column(db.DateTime, default=datetime.utcnow)
    updatedAt = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    config = db.relationship("OrganizationConfig", back_populates="organization", uselist=False)
    users = db.relationship("User", back_populates="organization")
    drivers = db.relationship("Driver", back_populates="organization")
    attempts = db.relationship("Attempt", back_populates="organization", cascade="all, delete-orphan")
    convocatorias = db.relationship("Convocatoria", back_populates="organization", cascade="all, delete-orphan")
    enrollments = db.relationship("Enrollment", back_populates="organization", cascade="all, delete-orphan")

class OrganizationConfig(db.Model):
    __tablename__ = "OrganizationConfig"
    
    id = db.Column(db.String, primary_key=True, server_default=text("gen_random_uuid()"))
    organizationId = db.Column(db.String, db.ForeignKey("Organization.id", ondelete="CASCADE"), unique=True, nullable=False)
    reportSchedule = db.Column(db.Enum(ReportSchedule), default=ReportSchedule.MONTHLY)
    notificationSettings = db.Column(JSONB, nullable=False)
    stabilityThresholds = db.Column(JSONB, nullable=False)
    telemetryThresholds = db.Column(JSONB, nullable=False)
    automatedReportsEnabled = db.Column(db.Boolean, default=False)
    automatedReportsFrequency = db.Column(db.String)
    automatedReportsLastSent = db.Column(db.DateTime)
    automatedReportsRecipients = db.Column(JSONB, default=[]) # String[] translates to JSONB or ARRAY in PG
    fleetmindEnabled = db.Column(db.Boolean, default=True)
    fleetmindWeights = db.Column(JSONB)
    createdAt = db.Column(db.DateTime, default=datetime.utcnow)
    updatedAt = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    organization = db.relationship("Organization", back_populates="config")

class User(db.Model, UserMixin):
    __tablename__ = "User"
    
    id = db.Column(db.String, primary_key=True, server_default=text("gen_random_uuid()"))
    email = db.Column(db.String, unique=True, nullable=False)
    name = db.Column(db.String, nullable=False)
    password = db.Column(db.String, nullable=False)
    organizationId = db.Column(db.String, db.ForeignKey("Organization.id", ondelete="RESTRICT"))
    role = db.Column(db.Enum(UserRole), default=UserRole.VIEWER)
    status = db.Column(db.String, default="ACTIVE")
    permissions = db.Column(JSONB, default=[])
    managedParks = db.Column(JSONB, default=[])  # legacy
    managedConvocatorias = db.Column(JSONB, default=[])  # IDs de convocatorias supervisadas (rol MANAGER)
    studentProfileId = db.Column(db.String, nullable=True)  # id de perfil de alumno (rol STUDENT)
    lastLoginAt = db.Column(db.DateTime)
    passwordChangedAt = db.Column(db.DateTime)
    failedLoginAttempts = db.Column(db.Integer, default=0)
    lockedUntil = db.Column(db.DateTime)
    googleId = db.Column(db.String, unique=True)
    viewModeOverride = db.Column(db.String)
    createdAt = db.Column(db.DateTime, default=datetime.utcnow)
    updatedAt = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    organization = db.relationship("Organization", back_populates="users")
    config = db.relationship("UserConfig", back_populates="user", uselist=False)
    instructed_drivers = db.relationship("Driver", back_populates="instructor")
    attempts_uploaded = db.relationship("Attempt", back_populates="uploaded_by", foreign_keys="Attempt.uploadedById")
    attempts_as_student = db.relationship("Attempt", back_populates="student", foreign_keys="Attempt.studentId")
    enrollments = db.relationship("Enrollment", back_populates="student", cascade="all, delete-orphan", foreign_keys="Enrollment.studentId")
    convocatorias_initiated = db.relationship("Convocatoria", back_populates="initiator", foreign_keys="Convocatoria.closureInitiatedBy")
    convocatorias_confirmed = db.relationship("Convocatoria", back_populates="confirmer", foreign_keys="Convocatoria.closureConfirmedBy")

class UserConfig(db.Model):
    __tablename__ = "UserConfig"
    
    id = db.Column(db.String, primary_key=True, server_default=text("gen_random_uuid()"))
    userId = db.Column(db.String, db.ForeignKey("User.id", ondelete="CASCADE"), unique=True, nullable=False)
    notificationPreferences = db.Column(JSONB, nullable=False)
    reportPreferences = db.Column(JSONB, nullable=False)
    language = db.Column(db.String, default="es")
    timezone = db.Column(db.String, default="UTC")
    createdAt = db.Column(db.DateTime, default=datetime.utcnow)
    updatedAt = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = db.relationship("User", back_populates="config")

class OperationalKey(db.Model):
    __tablename__ = "OperationalKey"
    
    id = db.Column(db.String, primary_key=True, server_default=text("(gen_random_uuid())::text"))
    sessionId = db.Column(db.String, nullable=False) # Relation added when Session model exists
    keyType = db.Column(db.Integer, nullable=False)
    startTime = db.Column(TIMESTAMP(timezone=True, precision=6), nullable=False)
    endTime = db.Column(TIMESTAMP(timezone=True, precision=6))
    duration = db.Column(db.Integer)
    startLat = db.Column(db.Float)
    startLon = db.Column(db.Float)
    endLat = db.Column(db.Float)
    endLon = db.Column(db.Float)
    rotativoState = db.Column(db.Boolean)
    geofenceId = db.Column(db.String)
    details = db.Column(JSONB)
    geofenceName = db.Column(db.String)
    keyTypeName = db.Column(db.String(20))
    createdAt = db.Column(TIMESTAMP(timezone=True, precision=6), default=datetime.utcnow)
    updatedAt = db.Column(TIMESTAMP(timezone=True, precision=6), default=datetime.utcnow, onupdate=datetime.utcnow)

class Driver(db.Model):
    __tablename__ = "conductores"
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    name = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(200))
    phone = db.Column(db.String(50))
    dni = db.Column(db.String(20))
    license_type = db.Column(db.String(50))
    license_number = db.Column(db.String(50))
    license_expiry = db.Column(db.Date)
    status = db.Column(db.String(50), default="activo")
    level = db.Column(db.String(50), default="novato")
    notes = db.Column(db.Text)
    photo_url = db.Column(db.String)
    organization_id = db.Column(db.String, db.ForeignKey("Organization.id", ondelete="CASCADE"), nullable=False)
    instructor_id = db.Column(db.String, db.ForeignKey("User.id", ondelete="SET NULL"))
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    organization = db.relationship("Organization", back_populates="drivers")
    instructor = db.relationship("User", back_populates="instructed_drivers")
    attempts = db.relationship("Attempt", back_populates="conductor")
