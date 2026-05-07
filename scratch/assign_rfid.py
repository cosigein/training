
import os
import sys
sys.path.append(os.getcwd())

from app import create_app
from app.extensions import db
from app.models.auth import User
from app.models.training import RfidCard
from datetime import datetime

app = create_app()
with app.app_context():
    # 1. Carlos Rodríguez
    carlos = User.query.filter(User.name.like('%Carlos Rodríguez%')).first()
    if carlos:
        # Desactivar otras tarjetas con ese UID si existen
        RfidCard.query.filter_by(uid='RFID_DEBUG_001').update({'active': False, 'revokedAt': datetime.utcnow()})
        
        # Crear o actualizar
        card = RfidCard(
            uid='RFID_DEBUG_001',
            organizationId=carlos.organizationId,
            assignedTo=carlos.id,
            assignedAt=datetime.utcnow(),
            active=True
        )
        db.session.add(card)
        print(f"Asignada RFID_DEBUG_001 a {carlos.name}")

    # 2. Alumno Uno
    uno = User.query.filter(User.name.like('%Alumno Uno%')).first()
    if uno:
        RfidCard.query.filter_by(uid='RFID_DEMO_CARD').update({'active': False, 'revokedAt': datetime.utcnow()})
        card = RfidCard(
            uid='RFID_DEMO_CARD',
            organizationId=uno.organizationId,
            assignedTo=uno.id,
            assignedAt=datetime.utcnow(),
            active=True
        )
        db.session.add(card)
        print(f"Asignada RFID_DEMO_CARD a {uno.name}")

    db.session.commit()
    print("Base de datos actualizada con tarjetas de depuración.")
