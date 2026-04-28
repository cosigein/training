from datetime import datetime
from enum import Enum
from sqlalchemy.dialects.postgresql import JSONB, TIMESTAMP, UUID
from sqlalchemy import text
from app.extensions import db

class SessionStatus(Enum):
    ACTIVE = "ACTIVE"
    COMPLETED = "COMPLETED"
    ERROR = "ERROR"
    PROCESSING = "PROCESSING"

class SessionType(Enum):
    ROUTINE = "ROUTINE"
    TRAINING = "TRAINING"
    EMERGENCY = "EMERGENCY"
    TEST = "TEST"

class TrainingStatus(Enum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    INVALIDATED = "INVALIDATED"

class Session(db.Model):
    __tablename__ = "Session"
    
    id = db.Column(db.String, primary_key=True, server_default=text("gen_random_uuid()"))
    vehicleId = db.Column(db.String, db.ForeignKey("Vehicle.id", ondelete="CASCADE"), nullable=False)
    userId = db.Column(db.String, db.ForeignKey("User.id", ondelete="SET NULL"))
    organizationId = db.Column(db.String, db.ForeignKey("Organization.id", ondelete="CASCADE"), nullable=False)
    parkId = db.Column(db.String, db.ForeignKey("Park.id", ondelete="SET NULL"))
    zoneId = db.Column(db.String, db.ForeignKey("Zone.id", ondelete="SET NULL"))
    
    startTime = db.Column(db.DateTime, nullable=False)
    endTime = db.Column(db.DateTime)
    sequence = db.Column(db.Integer, nullable=False)
    sessionNumber = db.Column(db.Integer, nullable=False)
    status = db.Column(db.Enum(SessionStatus), default=SessionStatus.ACTIVE)
    type = db.Column(db.Enum(SessionType), default=SessionType.ROUTINE)
    source = db.Column(db.String, nullable=False)
    
    weatherConditions = db.Column(JSONB)
    matcheddistance = db.Column(db.Float)
    matchedduration = db.Column(db.Float)
    matchedgeometry = db.Column(db.String)
    matchedconfidence = db.Column(db.Float)
    processingversion = db.Column(db.String(20), default="1.0")
    
    # Training related fields (maintained for DB compatibility)
    trainingMetadata = db.Column(JSONB)
    conductorId = db.Column(UUID(as_uuid=True), db.ForeignKey("conductores.id", ondelete="SET NULL"))
    trainingRouteId = db.Column(db.String)
    trainingStudentId = db.Column(db.String)
    trainingStatus = db.Column(db.Enum(TrainingStatus))
    trainingInvalidatedAt = db.Column(db.DateTime)
    trainingInvalidatedById = db.Column(db.String)
    trainingInvalidationReason = db.Column(db.String)
    trainingKioskCode = db.Column(db.String)
    
    createdAt = db.Column(db.DateTime, default=datetime.utcnow)
    updatedAt = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    @property
    def distance(self):
        return self.matcheddistance or 0.0

    # Relationships
    vehicle = db.relationship("Vehicle", back_populates="sessions")
    organization = db.relationship("Organization", back_populates="sessions")
    user = db.relationship("User", back_populates="sessions")
    gps_measurements = db.relationship("GpsMeasurement", back_populates="session")
    can_measurements = db.relationship("CanMeasurement", back_populates="session")
    stability_measurements = db.relationship("StabilityMeasurement", back_populates="session")
    rotativo_measurements = db.relationship("RotativoMeasurement", back_populates="session")
    quality_metrics = db.relationship("DataQualityMetrics", back_populates="session", uselist=False)
    upload_logs = db.relationship("SessionUploadLog", back_populates="session")
    evidence = db.relationship("Evidence", back_populates="session")
    conductor = db.relationship("Driver", back_populates="sessions")

class GpsMeasurement(db.Model):
    __tablename__ = "GpsMeasurement"
    
    id = db.Column(db.String, primary_key=True, server_default=text("gen_random_uuid()"))
    sessionId = db.Column(db.String, db.ForeignKey("Session.id", ondelete="CASCADE"), nullable=False)
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
    
    session = db.relationship("Session", back_populates="gps_measurements")

class CanMeasurement(db.Model):
    __tablename__ = "CanMeasurement"
    
    id = db.Column(db.String, primary_key=True, server_default=text("gen_random_uuid()"))
    sessionId = db.Column(db.String, db.ForeignKey("Session.id", ondelete="CASCADE"), nullable=False)
    
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
    
    session = db.relationship("Session", back_populates="can_measurements")

class StabilityMeasurement(db.Model):
    __tablename__ = "StabilityMeasurement"
    
    id = db.Column(db.String, primary_key=True, server_default=text("gen_random_uuid()"))
    sessionId = db.Column(db.String, db.ForeignKey("Session.id", ondelete="CASCADE"), nullable=False)
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
    
    session = db.relationship("Session", back_populates="stability_measurements")

class RotativoMeasurement(db.Model):
    __tablename__ = "RotativoMeasurement"
    
    id = db.Column(db.String, primary_key=True, server_default=text("gen_random_uuid()"))
    sessionId = db.Column(db.String, db.ForeignKey("Session.id", ondelete="CASCADE"), nullable=False)
    organizationId = db.Column(db.String, db.ForeignKey("Organization.id", ondelete="CASCADE"))
    
    timestamp = db.Column(db.DateTime, nullable=False)
    state = db.Column(db.String, nullable=False)
    key = db.Column(db.Integer)
    
    createdAt = db.Column(db.DateTime, default=datetime.utcnow)
    updatedAt = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    session = db.relationship("Session", back_populates="rotativo_measurements")

class DataQualityMetrics(db.Model):
    __tablename__ = "DataQualityMetrics"
    
    id = db.Column(db.String, primary_key=True, server_default=text("(gen_random_uuid())::text"))
    sessionId = db.Column(db.String, db.ForeignKey("Session.id", ondelete="CASCADE"), unique=True, nullable=False)
    
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
    
    session = db.relationship("Session", back_populates="quality_metrics")

class Evidence(db.Model):
    __tablename__ = "Evidence"
    
    id = db.Column(db.String, primary_key=True, server_default=text("gen_random_uuid()"))
    sessionId = db.Column(db.String, db.ForeignKey("Session.id", ondelete="CASCADE"), nullable=False)
    gpsMeasurementId = db.Column(db.String, db.ForeignKey("GpsMeasurement.id", ondelete="SET NULL"))
    stabilityMeasurementId = db.Column(db.String, db.ForeignKey("StabilityMeasurement.id", ondelete="SET NULL"))
    eventId = db.Column(db.String) # Reference to Event model
    
    type = db.Column(db.String, nullable=False)
    confidence = db.Column(db.Float, nullable=False)
    method = db.Column(db.String, nullable=False)
    source = db.Column(JSONB)
    validated = db.Column(JSONB)
    meta_data = db.Column('metadata', JSONB)
    
    createdAt = db.Column(db.DateTime, default=datetime.utcnow)
    
    session = db.relationship("Session", back_populates="evidence")

class SessionUploadLog(db.Model):
    __tablename__ = "SessionUploadLog"
    
    id = db.Column(db.String, primary_key=True, server_default=text("gen_random_uuid()"))
    sessionId = db.Column(db.String, db.ForeignKey("Session.id", ondelete="CASCADE"), nullable=False)
    userId = db.Column(db.String, db.ForeignKey("User.id", ondelete="CASCADE"), nullable=False)
    
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String, nullable=False)
    error = db.Column(db.String)
    source = db.Column(db.String, nullable=False)
    
    session = db.relationship("Session", back_populates="upload_logs")
