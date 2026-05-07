from app import create_app
from app.models.auth import User, UserRole
from app.models.training import RfidCard, Enrollment

app = create_app()
with app.app_context():
    students = User.query.filter(User.role == UserRole.STUDENT).all()
    print(f"{'NAME':<25} | {'UID':<20} | {'PLAZA':<5}")
    print("-" * 60)
    for s in students:
        card = RfidCard.query.filter_by(assignedTo=s.id).first()
        uid = card.uid if card else "NONE"
        
        # Calculate plaza
        from app.blueprints.kiosko.services import get_plaza_for_student
        plaza = get_plaza_for_student(s.id)
        
        print(f"{s.name:<25} | {uid:<20} | {plaza:<5}")
