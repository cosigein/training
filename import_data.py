import os
import sys
from datetime import datetime
import csv
import math
from app import create_app
from app.extensions import db
from app.models.vehicle import Vehicle, VehicleType, VehicleStatus, RealtimePosition
from app.models.auth import Organization
from app.models.session import Session, GpsMeasurement, StabilityMeasurement, RotativoMeasurement, SessionStatus, SessionType

def haversine(lat1, lon1, lat2, lon2):
    R = 6371  # Earth radius in km
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
    c = 2 * math.asin(math.sqrt(a))
    return R * c

app = create_app()

def parse_gps_file(filepath):
    """
    Supports two formats:
    1. Raspberry: HoraRaspberry,Fecha,Hora(GPS),Latitud,Longitud,Altitud,HDOP,Fix,NumSats,Velocidad(km/h)
    2. CSV: Fecha,Hora,Latitud,Longitud,Altitud,Velocidad,HDOP,NumSats
    """
    with open(filepath, 'r') as f:
        lines = f.readlines()
    
    if not lines:
        return None
    
    header_line = lines[0].strip()
    header = header_line.split(';')
    if header[0] != 'GPS':
        return None
    
    # Detect vehicle and session
    # Format 1: GPS;30/09/2025-19:28:15;DOBACK028;Sesión:1
    # Format 2: GPS;05/03/2025 09:28:46AM;DOBACK003;5;1
    
    vehicle_identifier = header[2]
    try:
        session_number = int(header[3].split(':')[1]) if ':' in header[3] else int(header[3])
    except:
        session_number = 1
        
    start_time_str = header[1]
    try:
        start_time = datetime.strptime(start_time_str, '%d/%m/%Y-%H:%M:%S')
    except ValueError:
        try:
            start_time = datetime.strptime(start_time_str, '%d/%m/%Y %I:%M:%S%p')
        except ValueError:
            start_time = datetime.now()

    measurements = []
    # Skip header and columns line
    for line in lines[2:]:
        parts = line.strip().split(',')
        if len(parts) < 6:
            continue
        
        if 'sin datos GPS' in line:
            continue
            
        try:
            if len(parts) >= 10: # Format 1
                # 19:28:16,30/09/2025,...
                time_part = parts[0].split('-')[1] if '-' in parts[0] else parts[0]
                ts = datetime.strptime(f"{parts[1]} {time_part}", '%d/%m/%Y %H:%M:%S')
                measurements.append({
                    'timestamp': ts,
                    'latitude': float(parts[3]),
                    'longitude': float(parts[4]),
                    'altitude': float(parts[5]),
                    'hdop': float(parts[6]),
                    'fix': parts[7],
                    'satellites': int(parts[8]),
                    'speed': float(parts[9])
                })
            else: # Format 2
                # 05/03/2025,09:28:53AM,37.9078748,-4.7296792,175.87,0.0,3,9
                ts = datetime.strptime(f"{parts[0]} {parts[1]}", '%d/%m/%Y %I:%M:%S%p')
                measurements.append({
                    'timestamp': ts,
                    'latitude': float(parts[2]),
                    'longitude': float(parts[3]),
                    'altitude': float(parts[4]),
                    'speed': float(parts[5]),
                    'hdop': float(parts[6]),
                    'satellites': int(parts[7]),
                    'fix': '3D' # Assume 3D fix if data is present
                })
        except (ValueError, IndexError):
            continue
            
    return {
        'vehicle_identifier': vehicle_identifier,
        'session_number': session_number,
        'start_time': start_time,
        'measurements': measurements
    }

def parse_stability_file(filepath):
    """
    Header: ESTABILIDAD;30/09/2025 14:00:33;DOBACK028;Sesión:2;
    Columns: ax; ay; az; gx; gy; gz; roll; pitch; yaw; ...
    """
    with open(filepath, 'r') as f:
        content = f.read()
    
    sections = content.split('ESTABILIDAD;')
    all_sessions = []
    
    for section in sections:
        if not section.strip():
            continue
            
        lines = section.strip().split('\n')
        if not lines:
            continue
            
        # Header parts (rest of the first line)
        header_parts = lines[0].strip().split(';')
        # header_parts[0]: 30/09/2025 14:00:33
        # header_parts[1]: DOBACK028
        # header_parts[2]: Sesión:2
        
        try:
            start_time = datetime.strptime(header_parts[0], '%d/%m/%Y %H:%M:%S')
            vehicle_identifier = header_parts[1]
            session_number = int(header_parts[2].split(':')[1])
        except (ValueError, IndexError):
            continue
            
        measurements = []
        current_time_str = start_time.strftime('%H:%M:%S')
        
        # Skip columns line
        for line in lines[2:]:
            line = line.strip()
            if not line: continue
            
            # Check if this line is a new timestamp update e.g. "14:00:34"
            if len(line.split(';')) == 1 and ':' in line:
                current_time_str = line
                continue
                
            parts = line.split(';')
            if len(parts) < 9:
                continue
                
            try:
                ts = datetime.strptime(f"{start_time.strftime('%d/%m/%Y')} {current_time_str}", '%d/%m/%Y %H:%M:%S')
                measurements.append({
                    'timestamp': ts,
                    'ax': float(parts[0]),
                    'ay': float(parts[1]),
                    'az': float(parts[2]),
                    'gx': float(parts[3]),
                    'gy': float(parts[4]),
                    'gz': float(parts[5]),
                    'roll': float(parts[6]),
                    'pitch': float(parts[7]),
                    'yaw': float(parts[8]),
                    'si': float(parts[15]) if len(parts) > 15 else 0,
                    'accmag': float(parts[16]) if len(parts) > 16 else 0
                })
            except (ValueError, IndexError):
                continue
                
        all_sessions.append({
            'vehicle_identifier': vehicle_identifier,
            'session_number': session_number,
            'start_time': start_time,
            'measurements': measurements
        })
        
    return all_sessions

def parse_rotary_file(filepath):
    """
    Header: ROTATIVO;30/09/2025-09:32:50;DOBACK028;Sesión:1
    Columns: Fecha-Hora;Estado
    """
    with open(filepath, 'r') as f:
        content = f.read()
        
    sections = content.split('ROTATIVO;')
    all_sessions = []
    
    for section in sections:
        if not section.strip():
            continue
            
        lines = section.strip().split('\n')
        if not lines:
            continue
            
        header_parts = lines[0].strip().split(';')
        try:
            start_time = datetime.strptime(header_parts[0], '%d/%m/%Y-%H:%M:%S')
            vehicle_identifier = header_parts[1]
            session_number = int(header_parts[2].split(':')[1])
        except (ValueError, IndexError):
            continue
            
        measurements = []
        for line in lines[2:]:
            parts = line.strip().split(';')
            if len(parts) < 2:
                continue
                
            try:
                ts = datetime.strptime(parts[0], '%d/%m/%Y-%H:%M:%S')
                measurements.append({
                    'timestamp': ts,
                    'state': parts[1]
                })
            except (ValueError, IndexError):
                continue
                
        all_sessions.append({
            'vehicle_identifier': vehicle_identifier,
            'session_number': session_number,
            'start_time': start_time,
            'measurements': measurements
        })
        
    return all_sessions

def main():
    data_dir = '../doback028'
    
    with app.app_context():
        # Get or create organization
        org = Organization.query.first()
        if not org:
            org = Organization(name='DobackSoft Default')
            db.session.add(org)
            db.session.commit()
            
        # Get or create vehicle
        vehicle = Vehicle.query.filter_by(identifier='DOBACK028').first()
        if not vehicle:
            vehicle = Vehicle(
                name='Doback 028',
                identifier='DOBACK028',
                model='Experimental',
                licensePlate='DB-028',
                type=VehicleType.TRUCK,
                organizationId=org.id
            )
            db.session.add(vehicle)
            db.session.commit()
            
        print(f"Importing data for vehicle {vehicle.identifier}...")

        # Process GPS
        gps_dir = os.path.join(data_dir, 'GPS')
        print(f"Scanning GPS dir: {gps_dir}")
        for filename in os.listdir(gps_dir):
            print(f" Checking file: {filename}")
            if filename.endswith('.txt') or filename.endswith('.csv'):
                data = parse_gps_file(os.path.join(gps_dir, filename))
                if not data: 
                    print(f"  Skipping {filename}: no data returned")
                    continue
                
                v_id = data['vehicle_identifier']
                # Get or create vehicle
                v = Vehicle.query.filter_by(identifier=v_id).first()
                if not v:
                    v = Vehicle(
                        name=f'Vehicle {v_id}',
                        identifier=v_id,
                        model='Experimental',
                        licensePlate=f'LP-{v_id}',
                        type=VehicleType.TRUCK,
                        organizationId=org.id
                    )
                    db.session.add(v)
                    db.session.flush()

                # Check if session exists
                session = Session.query.filter_by(
                    vehicleId=v.id, 
                    sessionNumber=data['session_number'],
                    startTime=data['start_time']
                ).first()
                
                if not session:
                    session = Session(
                        vehicleId=v.id,
                        organizationId=org.id,
                        startTime=data['start_time'],
                        sessionNumber=data['session_number'],
                        sequence=data['session_number'],
                        status=SessionStatus.COMPLETED,
                        type=SessionType.ROUTINE,
                        source='file_import'
                    )
                    db.session.add(session)
                    db.session.flush()
                else:
                    # Clean up existing data for this session to avoid duplicates
                    GpsMeasurement.query.filter_by(sessionId=session.id).delete()
                    StabilityMeasurement.query.filter_by(sessionId=session.id).delete()
                    RotativoMeasurement.query.filter_by(sessionId=session.id).delete()
                
                # Add measurements
                total_distance = 0
                last_point = None
                
                for m in data['measurements']:
                    meas = GpsMeasurement(
                        sessionId=session.id,
                        organizationId=org.id,
                        timestamp=m['timestamp'],
                        latitude=m['latitude'],
                        longitude=m['longitude'],
                        altitude=m['altitude'],
                        speed=m['speed'],
                        satellites=m['satellites'],
                        hdop=m['hdop'],
                        fix=m['fix']
                    )
                    db.session.add(meas)
                    
                    if last_point:
                        total_distance += haversine(
                            last_point['latitude'], last_point['longitude'],
                            m['latitude'], m['longitude']
                        )
                    last_point = m
                
                session.matcheddistance = total_distance
                session.endTime = data['measurements'][-1]['timestamp'] if data['measurements'] else data['start_time']
                
                # Update Realtime Position
                if data['measurements']:
                    last_m = data['measurements'][-1]
                    rt = RealtimePosition.query.filter_by(vehicleId=v.id).first()
                    if not rt:
                        rt = RealtimePosition(vehicleId=v.id)
                        db.session.add(rt)
                    
                    rt.timestamp = last_m['timestamp']
                    rt.lat = last_m['latitude']
                    rt.lon = last_m['longitude']
                    rt.alt = last_m['altitude']
                    rt.speed = last_m['speed']
                    rt.source = 'file_import'

                print(f"  Processed GPS: {filename} (Vehicle: {v_id}, Session: {data['session_number']}, Dist: {total_distance:.2f} km)")
                db.session.commit()

        # Process Stability
        stab_dir = os.path.join(data_dir, 'ESTABILIDAD')
        for filename in os.listdir(stab_dir):
            if filename.endswith('.txt'):
                sessions_data = parse_stability_file(os.path.join(stab_dir, filename))
                for data in sessions_data:
                    # Find session (by number and date match)
                    # We match sessions by sessionNumber and the same DAY
                    session = Session.query.filter(
                        Session.vehicleId == vehicle.id,
                        Session.sessionNumber == data['session_number'],
                        db.func.date(Session.startTime) == data['start_time'].date()
                    ).first()
                    
                    if not session:
                        session = Session(
                            vehicleId=vehicle.id,
                            organizationId=org.id,
                            startTime=data['start_time'],
                            sessionNumber=data['session_number'],
                            sequence=data['session_number'],
                            status=SessionStatus.COMPLETED,
                            type=SessionType.ROUTINE,
                            source='file_import'
                        )
                        db.session.add(session)
                        db.session.flush()
                    
                    for m in data['measurements']:
                        meas = StabilityMeasurement(
                            sessionId=session.id,
                            organizationId=org.id,
                            timestamp=m['timestamp'],
                            ax=m['ax'], ay=m['ay'], az=m['az'],
                            gx=m['gx'], gy=m['gy'], gz=m['gz'],
                            roll=m['roll'], pitch=m['pitch'], yaw=m['yaw'],
                            si=m['si'], accmag=m['accmag']
                        )
                        db.session.add(meas)
                    
                    print(f"  Processed Stability: {filename} (Session {data['session_number']})")
                    db.session.commit()

        # Process Rotary
        rot_dir = os.path.join(data_dir, 'ROTATIVO')
        for filename in os.listdir(rot_dir):
            if filename.endswith('.txt'):
                sessions_data = parse_rotary_file(os.path.join(rot_dir, filename))
                for data in sessions_data:
                    session = Session.query.filter(
                        Session.vehicleId == vehicle.id,
                        Session.sessionNumber == data['session_number'],
                        db.func.date(Session.startTime) == data['start_time'].date()
                    ).first()
                    
                    if not session:
                        session = Session(
                            vehicleId=vehicle.id,
                            organizationId=org.id,
                            startTime=data['start_time'],
                            sessionNumber=data['session_number'],
                            sequence=data['session_number'],
                            status=SessionStatus.COMPLETED,
                            type=SessionType.ROUTINE,
                            source='file_import'
                        )
                        db.session.add(session)
                        db.session.flush()
                        
                    for m in data['measurements']:
                        meas = RotativoMeasurement(
                            sessionId=session.id,
                            organizationId=org.id,
                            timestamp=m['timestamp'],
                            state=m['state']
                        )
                        db.session.add(meas)
                    
                    print(f"  Processed Rotary: {filename} (Session {data['session_number']})")
                    db.session.commit()

if __name__ == '__main__':
    main()
