from flask import jsonify, request, render_template, current_app, redirect, url_for, flash
from . import sessions_bp
from .services import attempt_service, AttemptError
from app.utils.decorators import jwt_required, get_jwt_identity, require_role
from app.models.auth import User
from app.extensions import db


@sessions_bp.route("/", methods=["GET"])
@require_role(["ADMIN", "MANAGER", "SUPER_ADMIN"])
def list_attempts():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)

    limit = request.args.get("limit", 50, type=int)
    attempts = attempt_service.get_org_attempts(user.organizationId, limit)

    if request.accept_mimetypes.accept_json and not request.accept_mimetypes.accept_html:
        return jsonify([{
            "id": a.id,
            "startTime": a.startTime.isoformat() if a.startTime else None,
            "endTime": a.endTime.isoformat() if a.endTime else None,
            "vehicleId": a.vehicleId,
            "studentId": a.studentId,
            "convocatoriaId": a.convocatoriaId,
            "score": a.score,
            "status": a.status.value if a.status else None,
        } for a in attempts])

    return render_template("sessions/list.html", attempts=attempts)


@sessions_bp.route("/<string:id>", methods=["GET"])
@require_role(["ADMIN", "MANAGER", "SUPER_ADMIN"])
def get_attempt_detail(id):
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    attempt = attempt_service.get_attempt_details(id, user.organizationId)

    if not attempt:
        if request.accept_mimetypes.accept_json and not request.accept_mimetypes.accept_html:
            return jsonify({"message": "Intento no encontrado"}), 404
        return render_template("errors/404.html"), 404

    if request.accept_mimetypes.accept_json and not request.accept_mimetypes.accept_html:
        return jsonify({
            "id": attempt.id,
            "startTime": attempt.startTime.isoformat() if attempt.startTime else None,
            "endTime": attempt.endTime.isoformat() if attempt.endTime else None,
            "vehicleId": attempt.vehicleId,
            "studentId": attempt.studentId,
            "convocatoriaId": attempt.convocatoriaId,
            "score": attempt.score,
            "scoreBreakdown": attempt.scoreBreakdown,
            "status": attempt.status.value if attempt.status else None,
        })

    events = attempt_service.get_attempt_events(id)
    gps_data = attempt_service.get_attempt_gps(id)

    route_geojson = {
        "type": "Feature",
        "geometry": {
            "type": "LineString",
            "coordinates": [[g.longitude, g.latitude] for g in gps_data]
        }
    }

    chart_data = {
        "labels": [g.timestamp.strftime("%H:%M:%S") for g in gps_data],
        "speed": [g.speed for g in gps_data],
    }

    return render_template(
        "sessions/detail.html",
        attempt=attempt,
        events=events,
        route_geojson=route_geojson,
        chart_data=chart_data,
    )


@sessions_bp.route("/<string:id>", methods=["DELETE"])
@require_role(["ADMIN", "SUPER_ADMIN"])
def delete_attempt(id):
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    try:
        deleted = attempt_service.delete_attempt(id, user.organizationId)
    except Exception as exc:
        db.session.rollback()
        current_app.logger.exception(
            "delete_attempt failed for id=%s org=%s",
            id, user.organizationId if user else None,
        )
        return jsonify({
            "message": f"{type(exc).__name__}: {str(exc)[:300]}",
            "type": type(exc).__name__,
        }), 500

    if not deleted:
        return jsonify({"message": "Intento no encontrado o sin permisos"}), 404
    return "", 204


@sessions_bp.route("/<string:id>/close", methods=["POST"])
@require_role(["ADMIN", "SUPER_ADMIN"])
def close_attempt(id):
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    try:
        att = attempt_service.close_attempt(id, user.organizationId, user_id)
    except AttemptError as exc:
        if request.is_json:
            return jsonify({"message": str(exc)}), 422
        flash(str(exc), "danger")
        return redirect(url_for("sessions.get_attempt_detail", id=id))

    if not att:
        if request.is_json:
            return jsonify({"message": "Intento no encontrado"}), 404
        return render_template("errors/404.html"), 404

    if request.is_json:
        return jsonify({"id": att.id, "status": att.status.value, "closedAt": att.closedAt.isoformat()})
    flash("Intento cerrado.", "success")
    return redirect(url_for("sessions.get_attempt_detail", id=att.id))


@sessions_bp.route("/<string:id>/invalidate", methods=["POST"])
@require_role(["ADMIN", "SUPER_ADMIN"])
def invalidate_attempt(id):
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    data = request.get_json() if request.is_json else request.form.to_dict()
    reason = (data.get("reason") or "").strip()

    try:
        att = attempt_service.invalidate_attempt(id, user.organizationId, user_id, reason)
    except AttemptError as exc:
        if request.is_json:
            return jsonify({"message": str(exc)}), 422
        flash(str(exc), "danger")
        return redirect(url_for("sessions.get_attempt_detail", id=id))

    if not att:
        if request.is_json:
            return jsonify({"message": "Intento no encontrado"}), 404
        return render_template("errors/404.html"), 404

    if request.is_json:
        return jsonify({
            "id": att.id, "status": att.status.value,
            "invalidatedAt": att.invalidatedAt.isoformat(),
            "invalidatedReason": att.invalidatedReason,
        })
    flash("Intento invalidado.", "success")
    return redirect(url_for("sessions.get_attempt_detail", id=att.id))


@sessions_bp.route("/<string:id>/gps", methods=["GET"])
@require_role(["ADMIN", "MANAGER", "SUPER_ADMIN"])
def get_attempt_gps(id):
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    attempt = attempt_service.get_attempt_details(id, user.organizationId)

    if not attempt:
        return jsonify({"message": "Intento no encontrado"}), 404

    gps_data = attempt_service.get_attempt_gps(id)
    return jsonify([{
        "lat": g.latitude,
        "lon": g.longitude,
        "speed": g.speed,
        "timestamp": g.timestamp.isoformat(),
    } for g in gps_data])
