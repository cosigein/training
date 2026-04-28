from datetime import datetime
from enum import Enum
from sqlalchemy.dialects.postgresql import JSONB, ARRAY
from sqlalchemy import text
from app.extensions import db

class ProcessingFileType(Enum):
    GPS = "GPS"
    CAN = "CAN"
    STABILITY = "STABILITY"
    ROTATIVO = "ROTATIVO"
    VIDEO = "VIDEO"
    ZIP = "ZIP"
    CSV = "CSV"
    OTHER = "OTHER"

class IngestionJobStatus(Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"

class ProcessingStatus(Enum):
    SUCCESS = "SUCCESS"
    PARTIAL = "PARTIAL"
    ERROR = "ERROR"
    PENDING = "PENDING"

class IngestionJob(db.Model):
    __tablename__ = "IngestionJob"
    
    id = db.Column(db.String, primary_key=True, server_default=text("gen_random_uuid()"))
    organizationId = db.Column(db.String, db.ForeignKey("Organization.id", ondelete="CASCADE"), nullable=False)
    vehicleId = db.Column(db.String, db.ForeignKey("Vehicle.id", ondelete="CASCADE"))
    
    filePath = db.Column(db.String, nullable=False)
    fileName = db.Column(db.String, nullable=False)
    fileType = db.Column(db.Enum(ProcessingFileType), nullable=False)
    fileHash = db.Column(db.String, nullable=False)
    status = db.Column(db.Enum(IngestionJobStatus), default=IngestionJobStatus.PENDING)
    priority = db.Column(db.Integer, default=0)
    sessionIds = db.Column(JSONB, default=[]) # ARRAY(db.String) in PG
    
    errorMessage = db.Column(db.String)
    errorDetails = db.Column(JSONB)
    
    detectedAt = db.Column(db.DateTime, default=datetime.utcnow)
    startedAt = db.Column(db.DateTime)
    completedAt = db.Column(db.DateTime)
    processedBy = db.Column(db.String)
    
    createdAt = db.Column(db.DateTime, default=datetime.utcnow)
    updatedAt = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    archivos = db.relationship("ArchivoSubido", back_populates="job")

class IngestionHistory(db.Model):
    __tablename__ = "IngestionHistory"
    
    id = db.Column(db.String, primary_key=True, server_default=text("gen_random_uuid()"))
    organizationId = db.Column(db.String, db.ForeignKey("Organization.id", ondelete="CASCADE"), nullable=False)
    vehicleId = db.Column(db.String, db.ForeignKey("Vehicle.id", ondelete="CASCADE"), nullable=False)
    
    date = db.Column(db.DateTime, nullable=False)
    operationType = db.Column(db.String, nullable=False) # SCAN | PROCESS | VALIDATE | CREATE_SESSION | ERROR
    status = db.Column(db.Enum(ProcessingStatus), nullable=False)
    filesProcessed = db.Column(JSONB)
    sessionsCreated = db.Column(JSONB, default=[])
    errors = db.Column(JSONB)
    meta_data = db.Column('metadata', JSONB)
    processingTime = db.Column(db.Integer)
    
    createdAt = db.Column(db.DateTime, default=datetime.utcnow)

class ArchivoSubido(db.Model):
    __tablename__ = "ArchivoSubido"
    
    id = db.Column(db.String, primary_key=True, server_default=text("gen_random_uuid()"))
    nombre = db.Column(db.String, nullable=False)
    tipo = db.Column(db.String, nullable=False)
    sessionId = db.Column(db.String, db.ForeignKey("Session.id", ondelete="CASCADE"))
    vehiculoId = db.Column(db.String, db.ForeignKey("Vehicle.id", ondelete="SET NULL"))
    ingestionJobId = db.Column(db.String, db.ForeignKey("IngestionJob.id", ondelete="SET NULL"))
    
    fechaSubida = db.Column(db.DateTime, default=datetime.utcnow)
    errores = db.Column(db.String)
    extraMetadata = db.Column(JSONB)
    
    lineasTotales = db.Column(db.Integer, default=0)
    lineasValidas = db.Column(db.Integer, default=0)
    lineasInvalidas = db.Column(db.Integer, default=0)
    porcentajeValido = db.Column(db.Float, default=0.0)
    problemasDetectados = db.Column(JSONB, default=[])
    
    createdAt = db.Column(db.DateTime, default=datetime.utcnow)
    updatedAt = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    job = db.relationship("IngestionJob", back_populates="archivos")

class FileState(db.Model):
    __tablename__ = "FileState"
    
    id = db.Column(db.String, primary_key=True, server_default=text("gen_random_uuid()"))
    fileName = db.Column(db.String, nullable=False)
    filePath = db.Column(db.String, nullable=False)
    fileHash = db.Column(db.String, nullable=False)
    fileSize = db.Column(db.Integer, nullable=False)
    vehicleId = db.Column(db.String, db.ForeignKey("Vehicle.id", ondelete="CASCADE"), nullable=False)
    organizationId = db.Column(db.String, db.ForeignKey("Organization.id", ondelete="CASCADE"), nullable=False)
    
    fileType = db.Column(db.String, nullable=False)
    processingStatus = db.Column(db.String, nullable=False)
    decodedStatus = db.Column(db.String)
    dataPointsCount = db.Column(db.Integer)
    lastProcessedAt = db.Column(db.DateTime)
    processingErrors = db.Column(JSONB, default=[])
    meta_data = db.Column('metadata', JSONB)
    
    createdAt = db.Column(db.DateTime, default=datetime.utcnow)
    updatedAt = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class DailyProcessingReport(db.Model):
    __tablename__ = "DailyProcessingReport"
    
    id = db.Column(db.String, primary_key=True, server_default=text("gen_random_uuid()"))
    organizationId = db.Column(db.String, db.ForeignKey("Organization.id", ondelete="CASCADE"), nullable=False)
    
    processingDate = db.Column(db.DateTime, nullable=False)
    totalVehicles = db.Column(db.Integer, nullable=False)
    successfulVehicles = db.Column(db.Integer, nullable=False)
    failedVehicles = db.Column(db.Integer, nullable=False)
    totalDataPoints = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String, nullable=False)
    details = db.Column(JSONB)
    
    createdAt = db.Column(db.DateTime, default=datetime.utcnow)
    updatedAt = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
