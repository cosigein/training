from flask import jsonify, request, render_template
from . import uploads_bp
from .services import ingestion_service
from app.utils.decorators import jwt_required, get_jwt_identity, require_org, require_role
from app.models.auth import User

@uploads_bp.route("/", methods=["GET"])
@require_org
def unified_upload():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    jobs = ingestion_service.get_org_jobs(user.organizationId)
    
    if request.accept_mimetypes.accept_json and not request.accept_mimetypes.accept_html:
        return jsonify([{
            "id": j.id,
            "fileName": j.fileName,
            "status": j.status.value if hasattr(j.status, 'value') else j.status,
            "createdAt": j.createdAt.isoformat()
        } for j in jobs])
        
    return render_template("uploads/unified.html", jobs=jobs)

@uploads_bp.route("/jobs", methods=["GET"])
@require_org
def list_jobs():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    jobs = ingestion_service.get_org_jobs(user.organizationId)
    return jsonify([{
        "id": j.id,
        "fileName": j.fileName,
        "status": j.status.value if hasattr(j.status, 'value') else j.status,
        "createdAt": j.createdAt.isoformat()
    } for j in jobs])

@uploads_bp.route("/upload", methods=["POST"])
@require_org
def upload_file():
    # En una implementación real aquí se manejaría S3 o el filesystem local
    # Por ahora registramos el job de ingesta
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    data = request.get_json()
    
    if not data or not data.get("fileName") or not data.get("filePath"):
        return jsonify({"message": "Faltan datos del archivo"}), 400
        
    job = ingestion_service.create_job(data, user.organizationId)
    
    # Aquí se dispararía la tarea de Celery
    # from app.workers.ingestion import ingest_task
    # ingest_task.delay(job.id)
    
    return jsonify({"message": "Archivo recibido e ingesta programada", "jobId": job.id}), 202
