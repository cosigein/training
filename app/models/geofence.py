from datetime import datetime
from enum import Enum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy import text
from app.extensions import db

class GeofenceType(Enum):
    POLYGON = "POLYGON"
    CIRCLE = "CIRCLE"
    LINE = "LINE"

class GeofenceMode(Enum):
    CAR = "CAR"
    TRUCK = "TRUCK"
    PEDESTRIAN = "PEDESTRIAN"

class GeofenceEventType(Enum):
    ENTER = "ENTER"
    EXIT = "EXIT"
    DWELL = "DWELL"

class GeofenceEventStatus(Enum):
    ACTIVE = "ACTIVE"
    RESOLVED = "RESOLVED"
    IGNORED = "IGNORED"

class Park(db.Model):
    __tablename__ = "Park"
    
    id = db.Column(db.String, primary_key=True, server_default=text("gen_random_uuid()"))
    name = db.Column(db.String, nullable=False)
    identifier = db.Column(db.String, unique=True, nullable=False)
    geometry = db.Column(JSONB, nullable=False)
    geometry_postgis = db.Column(db.String) # Should use GeoAlchemy2 for real GIS
    organizationId = db.Column(db.String, db.ForeignKey("Organization.id", ondelete="CASCADE"), nullable=False)
    createdAt = db.Column(db.DateTime, default=datetime.utcnow)
    updatedAt = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    organization = db.relationship("Organization", back_populates="parks")
    zones = db.relationship("Zone", back_populates="park")
    vehicles = db.relationship("Vehicle", back_populates="park")

class Zone(db.Model):
    __tablename__ = "Zone"
    
    id = db.Column(db.String, primary_key=True, server_default=text("gen_random_uuid()"))
    name = db.Column(db.String, nullable=False)
    type = db.Column(db.String, nullable=False)
    geometry = db.Column(JSONB, nullable=False)
    geometry_postgis = db.Column(db.String)
    organizationId = db.Column(db.String, db.ForeignKey("Organization.id", ondelete="CASCADE"), nullable=False)
    parkId = db.Column(db.String, db.ForeignKey("Park.id", ondelete="SET NULL"))
    createdAt = db.Column(db.DateTime, default=datetime.utcnow)
    updatedAt = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    organization = db.relationship("Organization", back_populates="zones")
    park = db.relationship("Park", back_populates="zones")

class Geofence(db.Model):
    __tablename__ = "Geofence"
    
    id = db.Column(db.String, primary_key=True, server_default=text("gen_random_uuid()"))
    externalId = db.Column(db.String, unique=True)
    name = db.Column(db.String, nullable=False)
    description = db.Column(db.String)
    tag = db.Column(db.String)
    type = db.Column(db.Enum(GeofenceType), default=GeofenceType.POLYGON)
    mode = db.Column(db.Enum(GeofenceMode), default=GeofenceMode.CAR)
    enabled = db.Column(db.Boolean, default=True)
    live = db.Column(db.Boolean, default=True)
    geometry = db.Column(JSONB, nullable=False)
    geometryCenter = db.Column(JSONB)
    geometryRadius = db.Column(db.Float)
    disallowedPrecedingTagSubstrings = db.Column(JSONB)
    ip = db.Column(JSONB)
    organizationId = db.Column(db.String, db.ForeignKey("Organization.id", ondelete="CASCADE"), nullable=False)
    createdAt = db.Column(db.DateTime, default=datetime.utcnow)
    updatedAt = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    @property
    def is_enabled(self):
        return self.enabled

    @property
    def area(self):
        # Dummy area calculation for now, in a real scenario we would use PostGIS or a geom library
        return 0.0

    # PostGIS geometry would be 'geometry_postgis' field here
    
    organization = db.relationship("Organization", back_populates="geofences")

class GeofenceEvent(db.Model):
    __tablename__ = "GeofenceEvent"
    
    id = db.Column(db.String, primary_key=True, server_default=text("gen_random_uuid()"))
    geofenceId = db.Column(db.String, db.ForeignKey("Geofence.id", ondelete="CASCADE"), nullable=False)
    vehicleId = db.Column(db.String, db.ForeignKey("Vehicle.id", ondelete="CASCADE"), nullable=False)
    organizationId = db.Column(db.String, db.ForeignKey("Organization.id", ondelete="CASCADE"), nullable=False)
    sessionId = db.Column(db.String, db.ForeignKey("Session.id", ondelete="CASCADE"))
    
    type = db.Column(db.Enum(GeofenceEventType), nullable=False)
    status = db.Column(db.Enum(GeofenceEventStatus), default=GeofenceEventStatus.ACTIVE)
    timestamp = db.Column(db.DateTime, nullable=False)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    speed = db.Column(db.Float)
    heading = db.Column(db.Float)
    data = db.Column(JSONB)
    processed = db.Column(db.Boolean, default=False)
    
    createdAt = db.Column(db.DateTime, default=datetime.utcnow)
    updatedAt = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class GeofenceRule(db.Model):
    __tablename__ = "GeofenceRule"
    
    id = db.Column(db.String, primary_key=True) # Direct ID in Prisma?
    name = db.Column(db.String, nullable=False)
    description = db.Column(db.String)
    organizationId = db.Column(db.String, db.ForeignKey("Organization.id", ondelete="CASCADE"), nullable=False)
    zoneId = db.Column(db.String, db.ForeignKey("Zone.id", ondelete="CASCADE"))
    parkId = db.Column(db.String, db.ForeignKey("Park.id", ondelete="CASCADE"))
    
    conditions = db.Column(JSONB, default=[])
    actions = db.Column(JSONB, default=[])
    isActive = db.Column(db.Boolean, default=True)
    priority = db.Column(db.Integer, default=1)
    
    createdAt = db.Column(db.DateTime, default=datetime.utcnow)
    updatedAt = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class GeofenceVehicleState(db.Model):
    __tablename__ = "GeofenceVehicleState"
    
    id = db.Column(db.String, primary_key=True, server_default=text("gen_random_uuid()"))
    vehicleId = db.Column(db.String, nullable=False)
    organizationId = db.Column(db.String, db.ForeignKey("Organization.id", ondelete="CASCADE"), nullable=False)
    geofenceId = db.Column(db.String, db.ForeignKey("Geofence.id", ondelete="SET NULL"))
    
    currentZones = db.Column(JSONB, default=[])
    currentParks = db.Column(JSONB, default=[])
    lastUpdate = db.Column(db.DateTime, default=datetime.utcnow)
    ruleStates = db.Column(JSONB, default={})
    
    createdAt = db.Column(db.DateTime, default=datetime.utcnow)
    updatedAt = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
