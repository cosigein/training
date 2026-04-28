from app.models.auth import User, Organization
from app.extensions import db

class AdminService:
    @staticmethod
    def get_all_users(org_id=None):
        if org_id:
            return User.query.filter_by(organizationId=org_id).all()
        return User.query.all()

    @staticmethod
    def get_all_organizations():
        return Organization.query.all()

    @staticmethod
    def update_user_status(user_id, status):
        user = User.query.get(user_id)
        if user:
            user.status = status
            db.session.commit()
            return user
        return None

admin_service = AdminService()
