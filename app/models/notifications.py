from datetime import datetime
from enum import Enum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy import text
from app.extensions import db

class NotificationChannel(Enum):
    EMAIL = "EMAIL"
    PUSH = "PUSH"
    IN_APP = "IN_APP"
    SMS = "SMS"

class NotificationStatus(Enum):
    PENDING = "PENDING"
    SENT = "SENT"
    DELIVERED = "DELIVERED"
    READ = "READ"
    FAILED = "FAILED"

class NotificationType(Enum):
    EVENT = "EVENT"
    SYSTEM = "SYSTEM"
    MAINTENANCE = "MAINTENANCE"
    ALERT = "ALERT"

class Alert(db.Model):
    __tablename__ = "Alert"
    
    id = db.Column(db.String, primary_key=True, server_default=text("gen_random_uuid()"))
    type = db.Column(db.String, nullable=False)
    severity = db.Column(db.String, nullable=False)
    title = db.Column(db.String, nullable=False)
    description = db.Column(db.String, nullable=False)
    vehicleId = db.Column(db.String, db.ForeignKey("Vehicle.id", ondelete="SET NULL"))
    vehicleName = db.Column(db.String)
    location = db.Column(JSONB)
    organizationId = db.Column(db.String, db.ForeignKey("Organization.id", ondelete="CASCADE"), nullable=False)
    
    acknowledged = db.Column(db.Boolean, default=False)
    acknowledgedBy = db.Column(db.String)
    acknowledgedAt = db.Column(db.DateTime)
    escalationLevel = db.Column(db.Integer, default=0)
    autoResolved = db.Column(db.Boolean, default=False)
    resolvedAt = db.Column(db.DateTime)
    meta_data = db.Column('metadata', JSONB)
    
    createdAt = db.Column(db.DateTime, default=datetime.utcnow)
    updatedAt = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class AlertRule(db.Model):
    __tablename__ = "AlertRule"
    
    id = db.Column(db.String, primary_key=True, server_default=text("gen_random_uuid()"))
    name = db.Column(db.String, nullable=False)
    description = db.Column(db.String)
    type = db.Column(db.String, nullable=False)
    conditions = db.Column(JSONB, nullable=False)
    severity = db.Column(db.String, nullable=False)
    enabled = db.Column(db.Boolean, default=True)
    organizationId = db.Column(db.String, db.ForeignKey("Organization.id", ondelete="CASCADE"), nullable=False)
    escalationConfig = db.Column(JSONB)
    notificationConfig = db.Column(JSONB)
    
    createdAt = db.Column(db.DateTime, default=datetime.utcnow)
    updatedAt = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Notification(db.Model):
    __tablename__ = "Notification"
    
    id = db.Column(db.String, primary_key=True, server_default=text("gen_random_uuid()"))
    userId = db.Column(db.String, db.ForeignKey("User.id", ondelete="CASCADE"), nullable=False)
    type = db.Column(db.Enum(NotificationType), nullable=False)
    channel = db.Column(db.Enum(NotificationChannel), nullable=False)
    message = db.Column(db.String, nullable=False)
    status = db.Column(db.Enum(NotificationStatus), default=NotificationStatus.PENDING)
    
    sentAt = db.Column(db.DateTime)
    receivedAt = db.Column(db.DateTime)
    
    createdAt = db.Column(db.DateTime, default=datetime.utcnow)
    updatedAt = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
