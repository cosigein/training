
import os
import sys
# Add parent dir to path to import app
sys.path.append(os.getcwd())

from app import create_app
from app.extensions import db
from app.models.auth import User, UserRole
from app.models.training import Convocatoria, Enrollment, RfidCard, ConvocatoriaStatus

app = create_app()
with app.app_context():
    print("--- CONVOCATORIAS ---")
    convs = Convocatoria.query.all()
    for c in convs:
        status = c.status.value if hasattr(c.status, 'value') else c.status
        print(f"ID: {c.id}, Name: {c.name}, Status: {status}")

    print("\n--- STUDENTS ---")
    students = User.query.filter_by(role=UserRole.STUDENT).all()
    for s in students:
        print(f"ID: {s.id}, Name: {s.name}")
        # Check enrollments
        ens = Enrollment.query.filter_by(studentId=s.id).all()
        for e in ens:
            e_status = e.status.value if hasattr(e.status, 'value') else e.status
            print(f"  -> Enrolled in: {e.convocatoriaId}, Status: {e_status}")
        # Check RFID
        cards = RfidCard.query.filter_by(assignedTo=s.id).all()
        for card in cards:
            print(f"  -> RFID: {card.uid}, Active: {card.active}")

    print("\n--- RFID CARDS (UNASSIGNED) ---")
    cards = RfidCard.query.filter(RfidCard.assignedTo.is_(None)).all()
    for card in cards:
        print(f"ID: {card.id}, UID: {card.uid}, Active: {card.active}")
