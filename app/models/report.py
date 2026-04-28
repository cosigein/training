from datetime import datetime
from enum import Enum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy import text
from app.extensions import db

class ReportFrequency(Enum):
    DAILY = "DAILY"
    WEEKLY = "WEEKLY"
    MONTHLY = "MONTHLY"

class ReportFormat(Enum):
    PDF = "PDF"
    XLSX = "XLSX"
    CSV = "CSV"
    JSON = "JSON"

class ReportStatus(Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    EXPIRED = "EXPIRED"

class ReportType(Enum):
    SESSION = "SESSION"
    VEHICLE = "VEHICLE"
    FLEET = "FLEET"
    KPI = "KPI"
    AUDIT = "AUDIT"
    MAINTENANCE = "MAINTENANCE"
    GEOFENCE = "GEOFENCE"
    EVENT = "EVENT"

class Report(db.Model):
    __tablename__ = "Report"
    
    id = db.Column(db.String, primary_key=True, server_default=text("gen_random_uuid()"))
    organizationId = db.Column(db.String, db.ForeignKey("Organization.id", ondelete="CASCADE"), nullable=False)
    requestedById = db.Column(db.String, db.ForeignKey("User.id", ondelete="SET NULL"))
    
    filePath = db.Column(db.String)
    sizeBytes = db.Column(db.Integer)
    params = db.Column(JSONB, nullable=False)
    status = db.Column(db.Enum(ReportStatus), default=ReportStatus.PENDING)
    expiresAt = db.Column(db.DateTime, nullable=False)
    sha256 = db.Column(db.String)
    
    createdAt = db.Column(db.DateTime, default=datetime.utcnow)
    updatedAt = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class ScheduledReport(db.Model):
    __tablename__ = "ScheduledReport"
    
    id = db.Column(db.String, primary_key=True, server_default=text("gen_random_uuid()"))
    userId = db.Column(db.String, db.ForeignKey("User.id", ondelete="CASCADE"), nullable=False)
    organizationId = db.Column(db.String, db.ForeignKey("Organization.id", ondelete="CASCADE"), nullable=False)
    createdBy = db.Column(db.String, db.ForeignKey("User.id", ondelete="CASCADE"), nullable=False)
    
    name = db.Column(db.String, nullable=False)
    description = db.Column(db.String)
    frequency = db.Column(db.Enum(ReportFrequency), nullable=False)
    dayOfWeek = db.Column(db.Integer)
    dayOfMonth = db.Column(db.Integer)
    timeOfDay = db.Column(db.String, nullable=False)
    timezone = db.Column(db.String, default="Europe/Madrid")
    
    filters = db.Column(JSONB, nullable=False)
    reportType = db.Column(db.Enum(ReportType), nullable=False)
    format = db.Column(db.Enum(ReportFormat), nullable=False)
    recipients = db.Column(JSONB, default=[])
    
    isActive = db.Column(db.Boolean, default=True)
    lastRunAt = db.Column(db.DateTime)
    nextRunAt = db.Column(db.DateTime, nullable=False)
    lastStatus = db.Column(db.String)
    lastError = db.Column(db.String)
    
    createdAt = db.Column(db.DateTime, default=datetime.utcnow)
    updatedAt = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class InformeGenerado(db.Model):
    __tablename__ = "InformeGenerado"
    
    id = db.Column(db.String, primary_key=True, server_default=text("gen_random_uuid()"))
    userId = db.Column(db.String, db.ForeignKey("User.id", ondelete="SET NULL"))
    sessionId = db.Column(db.String, db.ForeignKey("Session.id", ondelete="CASCADE"))
    vehicleId = db.Column(db.String, db.ForeignKey("Vehicle.id", ondelete="SET NULL"))
    ejecucionEventoId = db.Column(db.String, db.ForeignKey("EjecucionEvento.id", ondelete="SET NULL"))
    
    tipo = db.Column(db.Enum(ReportType), nullable=False)
    formato = db.Column(db.Enum(ReportFormat), nullable=False)
    urlPdf = db.Column(db.String, nullable=False)
    generadoEn = db.Column(db.DateTime, default=datetime.utcnow)
    
    createdAt = db.Column(db.DateTime, default=datetime.utcnow)
    updatedAt = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
