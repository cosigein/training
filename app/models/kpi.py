from datetime import datetime
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy import text
from app.extensions import db

class Lens(db.Model):
    __tablename__ = "Lens"
    
    id = db.Column(db.String, primary_key=True, server_default=text("gen_random_uuid()"))
    name = db.Column(db.String, nullable=False)
    version = db.Column(db.String, default="1.0")
    description = db.Column(db.String)
    config = db.Column(JSONB, nullable=False)
    isActive = db.Column(db.Boolean, default=True)
    isDefault = db.Column(db.Boolean, default=False)
    organizationId = db.Column(db.String, db.ForeignKey("Organization.id", ondelete="SET NULL"))
    effectiveDate = db.Column(db.DateTime, default=datetime.utcnow)
    expiryDate = db.Column(db.DateTime)
    deprecated = db.Column(db.Boolean, default=False)
    createdBy = db.Column(db.String)
    parentLensId = db.Column(db.String, db.ForeignKey("Lens.id", ondelete="SET NULL"))
    
    createdAt = db.Column(db.DateTime, default=datetime.utcnow)
    updatedAt = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class daily_kpi(db.Model):
    __tablename__ = "daily_kpi"
    
    id = db.Column(db.String, primary_key=True, server_default=text("gen_random_uuid()"))
    vehicleId = db.Column(db.String, db.ForeignKey("Vehicle.id", ondelete="CASCADE"), nullable=False)
    organizationId = db.Column(db.String, db.ForeignKey("Organization.id", ondelete="CASCADE"), nullable=False)
    date = db.Column(db.Date, nullable=False)
    
    totalTimeInPark = db.Column(db.Integer, default=0)
    totalTimeInWorkshop = db.Column(db.Integer, default=0)
    totalTimeOperational = db.Column(db.Integer, default=0)
    totalDistanceKm = db.Column(db.Float, default=0.0)
    totalEvents = db.Column(db.Integer, default=0)
    clave0Minutes = db.Column(db.Integer, default=0)
    clave1Minutes = db.Column(db.Integer, default=0)
    clave2Minutes = db.Column(db.Integer, default=0)
    clave3Minutes = db.Column(db.Integer, default=0)
    clave4Minutes = db.Column(db.Integer, default=0)
    clave5Minutes = db.Column(db.Integer, default=0)
    
    createdAt = db.Column(db.DateTime, default=datetime.utcnow)
    updatedAt = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class VehicleKPI(db.Model):
    __tablename__ = "VehicleKPI"
    
    id = db.Column(db.String, primary_key=True, server_default=text("gen_random_uuid()"))
    vehicleId = db.Column(db.String, db.ForeignKey("Vehicle.id", ondelete="CASCADE"), nullable=False)
    date = db.Column(db.DateTime, nullable=False)
    
    clave2Minutes = db.Column(db.Integer, nullable=False)
    clave5Minutes = db.Column(db.Integer, nullable=False)
    outOfParkMinutes = db.Column(db.Integer, nullable=False)
    eventsHigh = db.Column(db.Integer, nullable=False)
    eventsModerate = db.Column(db.Integer, nullable=False)
    timeInWorkshop = db.Column(db.Integer, nullable=False)
    
    createdAt = db.Column(db.DateTime, default=datetime.utcnow)
    updatedAt = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class AdvancedVehicleKPI(db.Model):
    __tablename__ = "AdvancedVehicleKPI"
    
    id = db.Column(db.String, primary_key=True, server_default=text("gen_random_uuid()"))
    vehicleId = db.Column(db.String, db.ForeignKey("Vehicle.id", ondelete="CASCADE"), nullable=False)
    organizationId = db.Column(db.String, db.ForeignKey("Organization.id", ondelete="CASCADE"), nullable=False)
    date = db.Column(db.DateTime, nullable=False)
    
    tiempoEnParque = db.Column(db.Integer, default=0)
    tiempoEnTaller = db.Column(db.Integer, default=0)
    tiempoFueraParque = db.Column(db.Integer, default=0)
    tiempoEnZonaSensible = db.Column(db.Integer, default=0)
    eventosCriticos = db.Column(db.Integer, default=0)
    eventosPeligrosos = db.Column(db.Integer, default=0)
    eventosModerados = db.Column(db.Integer, default=0)
    eventosLeves = db.Column(db.Integer, default=0)
    maxVelocidadAlcanzada = db.Column(db.Numeric, default=0)
    velocidadPromedio = db.Column(db.Numeric, default=0)
    distanciaRecorrida = db.Column(db.Numeric, default=0)
    tiempoEnMovimiento = db.Column(db.Integer, default=0)
    tiempoDetenido = db.Column(db.Integer, default=0)
    
    createdAt = db.Column(db.DateTime, default=datetime.utcnow)
    updatedAt = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    calculatedAt = db.Column(db.DateTime, default=datetime.utcnow)
    isValid = db.Column(db.Boolean, default=True)
    calculationVersion = db.Column(db.String, default="1.0")

class ParkKPI(db.Model):
    __tablename__ = "ParkKPI"
    
    id = db.Column(db.String, primary_key=True, server_default=text("gen_random_uuid()"))
    parkId = db.Column(db.String, db.ForeignKey("Park.id", ondelete="CASCADE"), nullable=False)
    date = db.Column(db.DateTime, nullable=False)
    
    totalClave2 = db.Column(db.Integer, nullable=False)
    totalClave5 = db.Column(db.Integer, nullable=False)
    totalEventsHigh = db.Column(db.Integer, nullable=False)
    totalEventsModerate = db.Column(db.Integer, nullable=False)
    
    createdAt = db.Column(db.DateTime, default=datetime.utcnow)
    updatedAt = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class ProcessingEvent(db.Model):
    __tablename__ = "ProcessingEvent"
    
    id = db.Column(db.String, primary_key=True, server_default=text("gen_random_uuid()"))
    fileName = db.Column(db.String, nullable=False)
    filePath = db.Column(db.String, nullable=False)
    fileType = db.Column(db.String, nullable=False) # Enum ProcessingFileType reused
    vehicleId = db.Column(db.String, db.ForeignKey("Vehicle.id", ondelete="CASCADE"), nullable=False)
    organizationId = db.Column(db.String, db.ForeignKey("Organization.id", ondelete="CASCADE"), nullable=False)
    ingestionJobId = db.Column(db.String, db.ForeignKey("IngestionJob.id", ondelete="SET NULL"))
    
    status = db.Column(db.String, nullable=False) # Enum ProcessingStatus reused
    dataPointsProcessed = db.Column(db.Integer)
    processingTime = db.Column(db.Integer)
    errorMessage = db.Column(db.String)
    errorCode = db.Column(db.String)
    meta_data = db.Column('metadata', JSONB)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    createdAt = db.Column(db.DateTime, default=datetime.utcnow)
    updatedAt = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    steps = db.relationship("PipelineStep", back_populates="event")

class PipelineStep(db.Model):
    __tablename__ = "PipelineStep"
    
    id = db.Column(db.String, primary_key=True, server_default=text("gen_random_uuid()"))
    processingEventId = db.Column(db.String, db.ForeignKey("ProcessingEvent.id", ondelete="CASCADE"), nullable=False)
    phase = db.Column(db.String, nullable=False) # e.g. "ingestion", "processing.parsing"
    
    event = db.relationship("ProcessingEvent", back_populates="steps")
