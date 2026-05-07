from datetime import datetime
from flask_jwt_extended import create_access_token, create_refresh_token
from werkzeug.security import generate_password_hash, check_password_hash
from app.models.auth import User, Organization, OrganizationConfig
from app.utils.security import generate_api_key
from app.extensions import db

class AuthService:
    @staticmethod
    def authenticate_user(email, password):
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            # Update last login
            user.lastLoginAt = datetime.utcnow()
            db.session.commit()
            return user
        return None

    @staticmethod
    def get_user_tokens(user):
        access_token = create_access_token(identity=user.id)
        refresh_token = create_refresh_token(identity=user.id)
        return access_token, refresh_token

    @staticmethod
    def create_access_token(identity):
        return create_access_token(identity=identity)


    @staticmethod
    def register_user(email, password, name, role="VIEWER"):
        # Check if user exists
        if User.query.filter_by(email=email).first():
            return None, "El email ya está registrado"

        # Security: In this system, register always creates a new organization
        api_data = generate_api_key()
        org = Organization(
            name=f"Org-{name}",
            apiKey=api_data["raw"],
            apiKeyHash=api_data["hash"],
            apiKeyPrefix=api_data["prefix"]
        )
        db.session.add(org)
        db.session.flush() # Get org id

        # Create defaults
        org_config = OrganizationConfig(
            organizationId=org.id,
            notificationSettings={},
            stabilityThresholds={},
            telemetryThresholds={}
        )
        db.session.add(org_config)

        hashed_password = generate_password_hash(password)
        user = User(
            email=email,
            password=hashed_password,
            name=name,
            role=role,
            organizationId=org.id,
            status="ACTIVE"
        )
        db.session.add(user)
        db.session.commit()
        
        return user, None

auth_service = AuthService()
