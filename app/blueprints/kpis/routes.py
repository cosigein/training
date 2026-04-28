from flask import jsonify, request, render_template
from . import kpis_bp
from .services import kpi_service
from app.utils.decorators import jwt_required, get_jwt_identity, require_role
from app.models.auth import User

@kpis_bp.route("/dashboard", methods=["GET"])
@require_role(["ADMIN", "MANAGER"])
def dashboard_executive():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    stats = kpi_service.get_dashboard_stats(user.organizationId)
    chart_data = kpi_service.get_activity_chart(user.organizationId)
    fleet_data = kpi_service.get_fleet_distribution(user.organizationId)
    
    if request.accept_mimetypes.accept_json and not request.accept_mimetypes.accept_html:
        return jsonify({
            "stats": stats,
            "chart_data": chart_data,
            "fleet_data": fleet_data
        })
        
    return render_template("kpis/executive.html", stats=stats, chart_data=chart_data, fleet_data=fleet_data)

@kpis_bp.route("/summary", methods=["GET"])
@require_role(["ADMIN", "MANAGER"])
def get_kpi_summary():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    summary = kpi_service.get_org_summary(user.organizationId)
    if not summary:
        if request.accept_mimetypes.accept_json and not request.accept_mimetypes.accept_html:
            return jsonify({"message": "No hay datos de KPI todavía"}), 404
        return render_template("errors/404.html"), 404
        
    return jsonify({
        "id": summary.id,
        "velocidadPromedio": float(summary.velocidadPromedio) if summary.velocidadPromedio else 0,
        "distanciaRecorrida": float(summary.distanciaRecorrida) if summary.distanciaRecorrida else 0,
        "eventosCriticos": summary.eventosCriticos,
        "tiempoEnMovimiento": summary.tiempoEnMovimiento,
        "tiempoDetenido": summary.tiempoDetenido
    })

@kpis_bp.route("/rankings", methods=["GET"])
@require_role(["ADMIN", "MANAGER"])
def get_rankings():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    rankings = kpi_service.get_rankings(user.organizationId)
    return jsonify(rankings)
