import os
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from werkzeug.security import generate_password_hash
from dotenv import load_dotenv

# Cargar variables desde .env
load_dotenv()

from app import create_app
from app.extensions import db
from app.models.auth import User, Organization, UserRole
from app.models.vehicle import Vehicle
# Import all models to ensure they are registered
from app.models import session, vehicle, auth, event, training, audit, ingestion, notifications

def create_database_if_not_exists():
    print("🔍 Verificando existencia de la base de datos...")
    # Obtenemos la URL de la DB de la env o usamos el default
    db_url = os.environ.get("DATABASE_URL", "postgresql://postgres:postgres@localhost/doback_dev")
    
    # Parseamos la URL para conectar a 'postgres' y crear la db objetivo
    # Formato esperado: postgresql://user:pass@host:port/dbname
    try:
        base_url, db_name = db_url.rsplit('/', 1)
        root_url = f"{base_url}/postgres"
        
        conn = psycopg2.connect(root_url)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cur = conn.cursor()
        
        # Verificar si la base existe
        cur.execute(f"SELECT 1 FROM pg_catalog.pg_database WHERE datname = '{db_name}'")
        exists = cur.fetchone()
        
        if not exists:
            print(f"🏗️  La base de datos '{db_name}' no existe. Creándola...")
            cur.execute(f"CREATE DATABASE {db_name}")
            print(f"✅ Base de datos '{db_name}' creada.")
        else:
            print(f"ℹ️  La base de datos '{db_name}' ya existe.")
            
        cur.close()
        conn.close()
    except Exception as e:
        print(f"⚠️  Nota: No se pudo verificar/crear la DB automáticamente: {e}")
        print("Asegúrate de que los credenciales en DATABASE_URL sean correctos y el usuario tenga permisos de CREATEDB.")

def setup_database():
    create_database_if_not_exists()
    
    app = create_app()
    with app.app_context():
        print("🛠️  Creando todas las tablas...")
        db.create_all()
        print("✅ Tablas creadas con éxito.")

        # Seed inicial
        if not Organization.query.filter_by(name="CMadrid").first():
            print("🌱 Sembrando datos iniciales...")
            
            # 1. Crear Organización
            org = Organization(
                name="CMadrid",
                apiKey="demo-key",
                formacionHabilitada=False
            )
            db.session.add(org)
            db.session.flush()

            # 2. Crear Admin User (admin123)
            admin = User(
                name="Admin CMadrid",
                email="admin@cmadrid.com",
                password=generate_password_hash("admin123", method="pbkdf2:sha256"),
                role=UserRole.ADMIN,
                organizationId=org.id,
                status="ACTIVE"
            )
            db.session.add(admin)
            db.session.commit()
            print("🚀 Seed completado. Usuario: admin@cmadrid.com / Clave: admin123")
        else:
            print("ℹ️  Los datos ya existen, saltando seed.")

if __name__ == "__main__":
    setup_database()
