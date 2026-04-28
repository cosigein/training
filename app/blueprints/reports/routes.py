from flask import jsonify, request, render_template
from . import reports_bp
from app.utils.decorators import jwt_required, get_jwt_identity, require_org
from app.models.auth import User

@reports_bp.route("/", methods=["GET"])
@require_org
def list_reports():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    # Placeholder for actual data retrieval
    reports = [] 
    automations = []
    
    if request.accept_mimetypes.accept_json and not request.accept_mimetypes.accept_html:
        return jsonify({
            "reports": reports,
            "automations": automations
        })
        
    return render_template("reports/list.html", reports=reports, automations=automations)

@reports_bp.route("/generate", methods=["POST"])
@require_org
def trigger_report():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    data = request.get_json()
    
    # Trigger Celery task
    # generate_report.delay(data, user.organizationId)
    
    return jsonify({"message": "Generación de reporte iniciada", "status": "PENDING"}), 202
