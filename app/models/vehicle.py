from datetime import datetime
from enum import Enum
from sqlalchemy.dialects.postgresql import JSONB, TIMESTAMP
from sqlalchemy import text
from app.extensions import db

class VehicleStatus(Enum):
    ACTIVE = "ACTIVE"
    MAINTENANCE = "MAINTENANCE"
    INACTIVE = "INACTIVE"
    REPAIR = "REPAIR"

class VehicleType(Enum):
    TRUCK = "TRUCK"
    VAN = "VAN"
    CAR = "CAR"
    BUS = "BUS"
    MOTORCYCLE = "MOTORCYCLE"
    ESCALA = "ESCALA"
    BRP = "BRP"
    FORESTAL = "FORESTAL"
    FIRE_TRUCK = "FIRE_TRUCK"
    OTHER = "OTHER"

class MaintenanceType(Enum):
    PREVENTIVE = "PREVENTIVE"
    CORRECTIVE = "CORRECTIVE"
    INSPECTION = "INSPECTION"
    REPAIR = "REPAIR"
    OTHER = "OTHER"

class MaintenanceStatus(Enum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"

class MaintenancePriority(Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

class Fleet(db.Model):
    """
    Nuevo modelo para agrupar vehículos, según el plan de migración.
    """
    __tablename__ = "Fleet"
    
    id = db.Column(db.String, primary_key=True, server_default=text("gen_random_uuid()"))
    name = db.Column(db.String, nullable=False)
    description = db.Column(db.String)
    organizationId = db.Column(db.String, db.ForeignKey("Organization.id", ondelete="CASCADE"), nullable=False)
    createdAt = db.Column(db.DateTime, default=datetime.utcnow)
    updatedAt = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    vehicles = db.relationship("Vehicle", back_populates="fleet")

class Vehicle(db.Model):
    __tablename__ = "Vehicle"
    
    id = db.Column(db.String, primary_key=True, server_default=text("gen_random_uuid()"))
    name = db.Column(db.String, nullable=False)
    model = db.Column(db.String, nullable=False)
    licensePlate = db.Column(db.String, unique=True, nullable=False)
    brand = db.Column(db.String)
    organizationId = db.Column(db.String, db.ForeignKey("Organization.id", ondelete="CASCADE"), nullable=False)
    userId = db.Column(db.String, db.ForeignKey("User.id", ondelete="SET NULL"))
    fleetId = db.Column(db.String, db.ForeignKey("Fleet.id", ondelete="SET NULL"))
    identifier = db.Column(db.String, unique=True, nullable=False)
    type = db.Column(db.Enum(VehicleType), nullable=False)
    status = db.Column(db.Enum(VehicleStatus), default=VehicleStatus.ACTIVE)
    active = db.Column(db.Boolean, default=True)
    # Mapeo a Webfleet (D-WF-001). Cuando se setea, los Attempts del vehículo
    # se sincronizan con la API de Webfleet.connect (show_tracks).
    webfleetObjectNo = db.Column(db.String, unique=True, nullable=True, index=True)
    # Identificador del dispositivo Doback Elite instalado en el vehículo (ej: "n023").
    # Se setea manualmente desde la UI de Manager → Vehículos.
    dobackIdentifier = db.Column(db.String(20), nullable=True, index=True)
    # Datos en vivo de Webfleet — se actualizan cada 10 min por el worker.
    webfleetData     = db.Column(JSONB, nullable=True)   # snapshot completo del showObjectReport
    webfleetLastSeen = db.Column(db.DateTime, nullable=True)  # cuándo lo vio Webfleet por última vez
    webfleetVisible  = db.Column(db.Boolean, default=True, nullable=False)  # False = desaparecido de Webfleet
    createdAt = db.Column(db.DateTime, default=datetime.utcnow)
    updatedAt = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    configuration = db.relationship("VehicleConfiguration", back_populates="vehicle", uselist=False)
    maintenance_records = db.relationship("MaintenanceRecord", back_populates="vehicle")
    maintenance_schedules = db.relationship("MaintenanceSchedule", back_populates="vehicle")
    realtime_positions = db.relationship("RealtimePosition", back_populates="vehicle")
    fleet = db.relationship("Fleet", back_populates="vehicles")
    attempts = db.relationship("Attempt", back_populates="vehicle")

class VehicleConfiguration(db.Model):
    __tablename__ = "VehicleConfiguration"
    
    id = db.Column(db.String, primary_key=True, server_default=text("gen_random_uuid()"))
    vehicleId = db.Column(db.String, db.ForeignKey("Vehicle.id", ondelete="CASCADE"), unique=True, nullable=False)
    stabilityThresholds = db.Column(JSONB, nullable=False)
    telemetryThresholds = db.Column(JSONB, nullable=False)
    maintenanceSchedule = db.Column(JSONB, nullable=False)
    cgHeight = db.Column(db.Float, default=1.6)
    mass = db.Column(db.Float, default=12000)
    maxSpeed = db.Column(db.Float, default=120)
    trackWidth = db.Column(db.Float, default=2.1)
    wheelbase = db.Column(db.Float, default=4.5)
    wheelbaseFrontal = db.Column(db.Float, default=1.1)
    coeff = db.Column(db.Float)
    alpha = db.Column(db.Float)
    alphav = db.Column(db.Float)
    firmwareVersion = db.Column(db.String)
    calibrationDate = db.Column(db.DateTime)
    authToken = db.Column(db.String) # Device token para WebSocket (hash bcrypt)
    authTokenExpiresAt = db.Column(db.DateTime) # null = no expira
    createdAt = db.Column(db.DateTime, default=datetime.utcnow)
    updatedAt = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    vehicle = db.relationship("Vehicle", back_populates="configuration")

class MaintenanceRecord(db.Model):
    __tablename__ = "MaintenanceRecord"
    
    id = db.Column(db.String, primary_key=True, server_default=text("gen_random_uuid()"))
    vehicleId = db.Column(db.String, db.ForeignKey("Vehicle.id", ondelete="CASCADE"), nullable=False)
    userId = db.Column(db.String, db.ForeignKey("User.id", ondelete="SET NULL"))
    tipo = db.Column(db.Enum(MaintenanceType), nullable=False)
    descripcion = db.Column(db.String, nullable=False)
    fecha = db.Column(db.DateTime, nullable=False)
    kilometraje = db.Column(db.Float)
    costo = db.Column(db.Float)
    estado = db.Column(db.Enum(MaintenanceStatus), default=MaintenanceStatus.PENDING)
    prioridad = db.Column(db.Enum(MaintenancePriority), default=MaintenancePriority.MEDIUM)
    notas = db.Column(db.String)
    partes = db.Column(JSONB)
    createdAt = db.Column(db.DateTime, default=datetime.utcnow)
    updatedAt = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    vehicle = db.relationship("Vehicle", back_populates="maintenance_records")

class MaintenanceSchedule(db.Model):
    __tablename__ = "MaintenanceSchedule"
    
    id = db.Column(db.String, primary_key=True, server_default=text("gen_random_uuid()"))
    vehicleId = db.Column(db.String, db.ForeignKey("Vehicle.id", ondelete="CASCADE"), nullable=False)
    type = db.Column(db.String, nullable=False)
    interval = db.Column(db.String, nullable=False)
    intervalValue = db.Column(db.Integer, default=1)
    lastPerformed = db.Column(db.DateTime)
    nextDue = db.Column(db.DateTime, nullable=False)
    isActive = db.Column(db.Boolean, default=True)
    description = db.Column(db.String)
    department = db.Column(db.String)
    createdAt = db.Column(db.DateTime, default=datetime.utcnow)
    updatedAt = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    vehicle = db.relationship("Vehicle", back_populates="maintenance_schedules")

class RealtimePosition(db.Model):
    __tablename__ = "RealtimePosition"
    
    id = db.Column(db.String, primary_key=True, server_default=text("gen_random_uuid()"))
    vehicleId = db.Column(db.String, db.ForeignKey("Vehicle.id", ondelete="CASCADE"), nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False)
    lat = db.Column(db.Float, nullable=False)
    lon = db.Column(db.Float, nullable=False)
    alt = db.Column(db.Float)
    speed = db.Column(db.Float)
    hdop = db.Column(db.Float)
    source = db.Column(db.String, nullable=False)
    
    vehicle = db.relationship("Vehicle", back_populates="realtime_positions")
