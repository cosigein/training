from datetime import datetime
from enum import Enum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy import text
from app.extensions import db

class EventType(Enum):
    GPS = "GPS"
    STABILITY = "STABILITY"
    SPEED = "SPEED"
    GEOFENCE = "GEOFENCE"
    ROTATIVO = "ROTATIVO"
    CAN = "CAN"
    MAINTENANCE = "MAINTENANCE"
    SYSTEM = "SYSTEM"

class EventStatus(Enum):
    ACTIVE = "ACTIVE"
    RESOLVED = "RESOLVED"
    IGNORED = "IGNORED"
    ACKNOWLEDGED = "ACKNOWLEDGED"

class EventConditionType(Enum):
    THRESHOLD = "THRESHOLD"
    RANGE = "RANGE"
    MATCH = "MATCH"

class EventConditionOperator(Enum):
    GREATER_THAN = "GREATER_THAN"
    LESS_THAN = "LESS_THAN"
    EQUALS = "EQUALS"
    NOT_EQUALS = "NOT_EQUALS"
    BETWEEN = "BETWEEN"

class EventLogicOperator(Enum):
    AND = "AND"
    OR = "OR"

class GestorDeEvento(db.Model):
    __tablename__ = "GestorDeEvento"
    
    id = db.Column(db.String, primary_key=True, server_default=text("gen_random_uuid()"))
    name = db.Column(db.String, nullable=False)
    description = db.Column(db.String)
    type = db.Column(db.Enum(EventType), nullable=False)
    status = db.Column(db.Enum(EventStatus), default=EventStatus.ACTIVE)
    isPredefined = db.Column(db.Boolean, default=False)
    logicOperator = db.Column(db.Enum(EventLogicOperator), default=EventLogicOperator.AND)
    timeWindowStart = db.Column(db.DateTime)
    timeWindowEnd = db.Column(db.DateTime)
    createdById = db.Column(db.String, db.ForeignKey("User.id", ondelete="SET NULL"))
    organizationId = db.Column(db.String, db.ForeignKey("Organization.id", ondelete="CASCADE"), nullable=False)
    version = db.Column(db.String, default="1.0.0")
    autoEvaluate = db.Column(db.Boolean, default=False)
    
    createdAt = db.Column(db.DateTime, default=datetime.utcnow)
    updatedAt = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    conditions = db.relationship("EventCondition", back_populates="gestor")
    visible_variables = db.relationship("EventoVariableVisible", back_populates="gestor")
    ejecuciones = db.relationship("EjecucionEvento", back_populates="gestor")

class Event(db.Model):
    __tablename__ = "Event"
    
    id = db.Column(db.String, primary_key=True, server_default=text("gen_random_uuid()"))
    type = db.Column(db.Enum(EventType), nullable=False)
    status = db.Column(db.Enum(EventStatus), nullable=False)
    organizationId = db.Column(db.String, db.ForeignKey("Organization.id", ondelete="CASCADE"), nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False)
    data = db.Column(JSONB, nullable=False)
    displayData = db.Column(JSONB, nullable=False)
    confidence = db.Column(db.Float)
    source = db.Column(db.String)
    zoneId = db.Column(db.String, db.ForeignKey("Zone.id", ondelete="SET NULL"))
    parkId = db.Column(db.String, db.ForeignKey("Park.id", ondelete="SET NULL"))
    
    createdAt = db.Column(db.DateTime, default=datetime.utcnow)
    updatedAt = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    vehicles = db.relationship("Vehicle", secondary="EventVehicle")

class EventVehicle(db.Model):
    __tablename__ = "EventVehicle"
    
    id = db.Column(db.String, primary_key=True, server_default=text("gen_random_uuid()"))
    eventId = db.Column(db.String, db.ForeignKey("Event.id", ondelete="CASCADE"), nullable=False)
    vehicleId = db.Column(db.String, db.ForeignKey("Vehicle.id", ondelete="CASCADE"), nullable=False)
    
    createdAt = db.Column(db.DateTime, default=datetime.utcnow)
    updatedAt = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class EjecucionEvento(db.Model):
    __tablename__ = "EjecucionEvento"
    
    id = db.Column(db.String, primary_key=True, server_default=text("gen_random_uuid()"))
    eventId = db.Column(db.String, db.ForeignKey("GestorDeEvento.id", ondelete="CASCADE"), nullable=False)
    vehicleId = db.Column(db.String, db.ForeignKey("Vehicle.id", ondelete="CASCADE"), nullable=False)
    sessionId = db.Column(db.String, db.ForeignKey("Session.id", ondelete="CASCADE"))
    
    triggeredAt = db.Column(db.DateTime, default=datetime.utcnow)
    data = db.Column(JSONB, nullable=False)
    displayData = db.Column(JSONB, nullable=False)
    location = db.Column(JSONB)
    status = db.Column(db.Enum(EventStatus), default=EventStatus.ACTIVE)
    
    createdAt = db.Column(db.DateTime, default=datetime.utcnow)
    updatedAt = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    gestor = db.relationship("GestorDeEvento", back_populates="ejecuciones")
    acciones = db.relationship("AccionDisparada", back_populates="ejecucion")

class AccionDisparada(db.Model):
    __tablename__ = "AccionDisparada"
    
    id = db.Column(db.String, primary_key=True, server_default=text("gen_random_uuid()"))
    ejecucionId = db.Column(db.String, db.ForeignKey("EjecucionEvento.id", ondelete="CASCADE"), nullable=False)
    tipoAccion = db.Column(db.String, nullable=False)
    resultado = db.Column(db.String, nullable=False)
    ejecutadoEn = db.Column(db.DateTime, default=datetime.utcnow)
    
    createdAt = db.Column(db.DateTime, default=datetime.utcnow)
    updatedAt = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    ejecucion = db.relationship("EjecucionEvento", back_populates="acciones")

class EventCondition(db.Model):
    __tablename__ = "EventCondition"
    
    id = db.Column(db.String, primary_key=True, server_default=text("gen_random_uuid()"))
    eventId = db.Column(db.String, db.ForeignKey("GestorDeEvento.id", ondelete="CASCADE"), nullable=False)
    type = db.Column(db.Enum(EventConditionType), nullable=False)
    variable = db.Column(db.String, nullable=False)
    operator = db.Column(db.Enum(EventConditionOperator), nullable=False)
    value = db.Column(db.Float, nullable=False)
    value2 = db.Column(db.Float)
    unit = db.Column(db.String)
    
    createdAt = db.Column(db.DateTime, default=datetime.utcnow)
    updatedAt = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    gestor = db.relationship("GestorDeEvento", back_populates="conditions")

class EventoVariableVisible(db.Model):
    __tablename__ = "EventoVariableVisible"
    
    id = db.Column(db.String, primary_key=True, server_default=text("gen_random_uuid()"))
    eventoId = db.Column(db.String, db.ForeignKey("GestorDeEvento.id", ondelete="CASCADE"), nullable=False)
    nombre = db.Column(db.String, nullable=False)
    orden = db.Column(db.Integer, nullable=False)
    
    createdAt = db.Column(db.DateTime, default=datetime.utcnow)
    updatedAt = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    gestor = db.relationship("GestorDeEvento", back_populates="visible_variables")
