from datetime import datetime
from enum import Enum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy import text
from app.extensions import db

class DeliverableStatus(Enum):
    OK = "OK"
    REVISAR = "REVISAR"
    ERROR = "ERROR"

class IncidentSeverity(Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

class IncidentStatus(Enum):
    OPEN = "OPEN"
    IN_PROGRESS = "IN_PROGRESS"
    CLOSED = "CLOSED"

class AuditLog(db.Model):
    __tablename__ = "AuditLog"
    
    id = db.Column(db.String, primary_key=True, server_default=text("gen_random_uuid()"))
    decision = db.Column(db.String, nullable=False)
    who = db.Column(db.String)
    when = db.Column(db.DateTime, default=datetime.utcnow)
    what = db.Column(JSONB, nullable=False)
    why = db.Column(db.String)
    confidence = db.Column(db.Float)
    organizationId = db.Column(db.String, db.ForeignKey("Organization.id", ondelete="SET NULL"))
    attemptId = db.Column(db.String, db.ForeignKey("Attempt.id", ondelete="CASCADE"))
    
    createdAt = db.Column(db.DateTime, default=datetime.utcnow)

class DeliverableVehicle(db.Model):
    __tablename__ = "DeliverableVehicle"
    
    id = db.Column(db.String, primary_key=True, server_default=text("gen_random_uuid()"))
    name = db.Column(db.String, nullable=False)
    licensePlate = db.Column(db.String, nullable=False)
    identifier = db.Column(db.String, nullable=False)
    organizationId = db.Column(db.String, db.ForeignKey("Organization.id", ondelete="CASCADE"), nullable=False)
    active = db.Column(db.Boolean, default=True)
    
    createdAt = db.Column(db.DateTime, default=datetime.utcnow)
    updatedAt = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    daily_reviews = db.relationship("DailyReview", back_populates="vehicle")
    incidents = db.relationship("Incident", back_populates="vehicle")

class DailyReview(db.Model):
    __tablename__ = "DailyReview"
    
    id = db.Column(db.String, primary_key=True, server_default=text("gen_random_uuid()"))
    reviewDate = db.Column(db.Date, nullable=False)
    vehicleId = db.Column(db.String, db.ForeignKey("DeliverableVehicle.id", ondelete="CASCADE"), nullable=False)
    organizationId = db.Column(db.String, db.ForeignKey("Organization.id", ondelete="CASCADE"), nullable=False)
    
    fileUploaded = db.Column(db.Enum(DeliverableStatus), default=DeliverableStatus.REVISAR)
    fileSizeStatus = db.Column(db.Enum(DeliverableStatus), default=DeliverableStatus.REVISAR)
    stabilityStatus = db.Column(db.Enum(DeliverableStatus), default=DeliverableStatus.REVISAR)
    eventsStatus = db.Column(db.Enum(DeliverableStatus), default=DeliverableStatus.REVISAR)
    gpsStatus = db.Column(db.Enum(DeliverableStatus), default=DeliverableStatus.REVISAR)
    rotativeStatus = db.Column(db.Enum(DeliverableStatus), default=DeliverableStatus.REVISAR)
    canStatus = db.Column(db.Enum(DeliverableStatus), default=DeliverableStatus.REVISAR)
    overallStatus = db.Column(db.Enum(DeliverableStatus), default=DeliverableStatus.REVISAR)
    
    incidentsText = db.Column(db.String)
    actionsText = db.Column(db.String)
    reviewedBy = db.Column(db.String)
    reviewedAt = db.Column(db.DateTime)
    
    createdAt = db.Column(db.DateTime, default=datetime.utcnow)
    updatedAt = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    vehicle = db.relationship("DeliverableVehicle", back_populates="daily_reviews")

class Incident(db.Model):
    __tablename__ = "Incident"
    
    id = db.Column(db.String, primary_key=True, server_default=text("gen_random_uuid()"))
    vehicleId = db.Column(db.String, db.ForeignKey("DeliverableVehicle.id", ondelete="CASCADE"), nullable=False)
    organizationId = db.Column(db.String, db.ForeignKey("Organization.id", ondelete="CASCADE"), nullable=False)
    
    date = db.Column(db.Date, nullable=False)
    severity = db.Column(db.Enum(IncidentSeverity), nullable=False)
    description = db.Column(db.String, nullable=False)
    action = db.Column(db.String)
    status = db.Column(db.Enum(IncidentStatus), default=IncidentStatus.OPEN)
    
    closedAt = db.Column(db.DateTime)
    closedBy = db.Column(db.String)
    
    createdAt = db.Column(db.DateTime, default=datetime.utcnow)
    updatedAt = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    vehicle = db.relationship("DeliverableVehicle", back_populates="incidents")

class WeeklyReport(db.Model):
    __tablename__ = "WeeklyReport"
    
    id = db.Column(db.String, primary_key=True, server_default=text("gen_random_uuid()"))
    weekStartDate = db.Column(db.Date, nullable=False)
    weekEndDate = db.Column(db.Date, nullable=False)
    organizationId = db.Column(db.String, db.ForeignKey("Organization.id", ondelete="CASCADE"), nullable=False)
    
    workSummary = db.Column(db.String, nullable=False)
    incidentsSummary = db.Column(db.String, nullable=False)
    openIncidents = db.Column(db.String, nullable=False)
    workPlan = db.Column(db.String, nullable=False)
    generatedBy = db.Column(db.String)
    generatedAt = db.Column(db.DateTime, default=datetime.utcnow)
    
    createdAt = db.Column(db.DateTime, default=datetime.utcnow)
    updatedAt = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
