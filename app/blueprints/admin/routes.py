from flask import jsonify, request, render_template, redirect, url_for, flash, current_app
from . import admin_bp
from .services import admin_service
from .convocatoria_service import convocatoria_service, ConvocatoriaError
from app.utils.decorators import jwt_required, get_jwt_identity, require_role
from app.models.auth import User


# ─────────────────────────────────────────────────────────────────────────────
# Users / Organizations (legacy, usados por el sidebar)
# ─────────────────────────────────────────────────────────────────────────────

@admin_bp.route("/users", methods=["GET"])
@require_role(["ADMIN", "SUPER_ADMIN"])
def list_users():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    users = admin_service.get_all_users(user.organizationId)

    if request.accept_mimetypes.accept_json and not request.accept_mimetypes.accept_html:
        return jsonify([{
            "id": u.id, "email": u.email, "name": u.name,
            "role": u.role.value if hasattr(u.role, 'value') else u.role,
            "status": u.status,
        } for u in users])
    return render_template("admin/organizations.html", users=users)


@admin_bp.route("/organizations", methods=["GET"])
@require_role(["ADMIN", "SUPER_ADMIN"])
def list_organizations():
    orgs = admin_service.get_all_organizations()
    if request.accept_mimetypes.accept_json and not request.accept_mimetypes.accept_html:
        return jsonify([{
            "id": o.id, "name": o.name,
            "createdAt": o.createdAt.isoformat() if o.createdAt else None,
        } for o in orgs])
    return render_template("admin/organizations.html", organizations=orgs)


# ─────────────────────────────────────────────────────────────────────────────
# Convocatorias
# ─────────────────────────────────────────────────────────────────────────────

@admin_bp.route("/convocatorias", methods=["GET"])
@require_role(["ADMIN", "MANAGER", "SUPER_ADMIN"])
def list_convocatorias():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    convocatorias = convocatoria_service.list_convocatorias(user.organizationId)

    if request.accept_mimetypes.accept_json and not request.accept_mimetypes.accept_html:
        return jsonify([_convocatoria_to_dict(c) for c in convocatorias])
    return render_template("admin/convocatorias_list.html", convocatorias=convocatorias)


@admin_bp.route("/convocatorias/new", methods=["GET"])
@require_role(["ADMIN", "SUPER_ADMIN"])
def new_convocatoria_form():
    return render_template("admin/convocatoria_new.html")


@admin_bp.route("/convocatorias", methods=["POST"])
@require_role(["ADMIN", "SUPER_ADMIN"])
def create_convocatoria():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    data = request.get_json() if request.is_json else request.form.to_dict()

    try:
        conv = convocatoria_service.create_convocatoria(user.organizationId, user_id, data)
    except ConvocatoriaError as exc:
        if request.is_json:
            return jsonify({"message": str(exc)}), 400
        flash(str(exc), "danger")
        return render_template("admin/convocatoria_new.html", form=data), 400

    if request.is_json:
        return jsonify(_convocatoria_to_dict(conv)), 201
    flash(f"Convocatoria '{conv.name}' creada.", "success")
    return redirect(url_for("admin.get_convocatoria_detail", conv_id=conv.id))


@admin_bp.route("/convocatorias/<string:conv_id>", methods=["GET"])
@require_role(["ADMIN", "MANAGER", "SUPER_ADMIN"])
def get_convocatoria_detail(conv_id):
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    conv = convocatoria_service.get_convocatoria(conv_id, user.organizationId)
    if not conv:
        if request.is_json:
            return jsonify({"message": "Convocatoria no encontrada"}), 404
        return render_template("errors/404.html"), 404

    enrollments = convocatoria_service.list_enrollments(conv.id, user.organizationId)
    eligible = convocatoria_service.list_eligible_students(user.organizationId)

    if request.accept_mimetypes.accept_json and not request.accept_mimetypes.accept_html:
        return jsonify({
            **_convocatoria_to_dict(conv),
            "enrollments": [_enrollment_to_dict(e) for e in enrollments],
        })

    return render_template(
        "admin/convocatoria_detail.html",
        convocatoria=conv,
        enrollments=enrollments,
        eligible_students=eligible,
    )


@admin_bp.route("/convocatorias/<string:conv_id>/edit", methods=["GET"])
@require_role(["ADMIN", "SUPER_ADMIN"])
def edit_convocatoria_form(conv_id):
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    conv = convocatoria_service.get_convocatoria(conv_id, user.organizationId)
    if not conv:
        return render_template("errors/404.html"), 404
    return render_template("admin/convocatoria_edit.html", convocatoria=conv)


@admin_bp.route("/convocatorias/<string:conv_id>", methods=["POST"])
@require_role(["ADMIN", "SUPER_ADMIN"])
def update_convocatoria(conv_id):
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    data = request.get_json() if request.is_json else request.form.to_dict()

    try:
        conv = convocatoria_service.update_convocatoria(
            conv_id, user.organizationId, user_id, data
        )
    except ConvocatoriaError as exc:
        if request.is_json:
            return jsonify({"message": str(exc)}), 422
        flash(str(exc), "danger")
        return redirect(url_for("admin.edit_convocatoria_form", conv_id=conv_id))

    if not conv:
        if request.is_json:
            return jsonify({"message": "Convocatoria no encontrada"}), 404
        return render_template("errors/404.html"), 404

    if request.is_json:
        return jsonify(_convocatoria_to_dict(conv))
    flash("Convocatoria actualizada.", "success")
    return redirect(url_for("admin.get_convocatoria_detail", conv_id=conv.id))


@admin_bp.route("/convocatorias/<string:conv_id>/delete", methods=["POST"])
@require_role(["ADMIN", "SUPER_ADMIN"])
def delete_convocatoria(conv_id):
    user_id = get_jwt_identity()
    user = User.query.get(user_id)

    try:
        ok = convocatoria_service.delete_convocatoria(conv_id, user.organizationId, user_id)
    except ConvocatoriaError as exc:
        if request.is_json:
            return jsonify({"message": str(exc)}), 422
        flash(str(exc), "danger")
        return redirect(url_for("admin.get_convocatoria_detail", conv_id=conv_id))

    if not ok:
        if request.is_json:
            return jsonify({"message": "Convocatoria no encontrada"}), 404
        flash("Convocatoria no encontrada.", "warning")
        return redirect(url_for("admin.list_convocatorias"))

    if request.is_json:
        return "", 204
    flash("Convocatoria eliminada.", "success")
    return redirect(url_for("admin.list_convocatorias"))


# ─── Enrollments ──────────────────────────────────────────────────────────────

@admin_bp.route("/convocatorias/<string:conv_id>/enrollments", methods=["POST"])
@require_role(["ADMIN", "SUPER_ADMIN"])
def add_enrollment(conv_id):
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    data = request.get_json() if request.is_json else request.form.to_dict()
    student_id = data.get("studentId") or data.get("student_id")
    route_id = data.get("routeId") or data.get("route_id")

    try:
        enr = convocatoria_service.add_enrollment(
            conv_id, user.organizationId, user_id, student_id, route_id
        )
    except ConvocatoriaError as exc:
        if request.is_json:
            return jsonify({"message": str(exc)}), 400
        flash(str(exc), "danger")
        return redirect(url_for("admin.get_convocatoria_detail", conv_id=conv_id))

    if request.is_json:
        return jsonify(_enrollment_to_dict(enr)), 201
    flash(f"Alumno inscrito.", "success")
    return redirect(url_for("admin.get_convocatoria_detail", conv_id=conv_id))


@admin_bp.route("/convocatorias/<string:conv_id>/enrollments/<string:enrollment_id>/delete", methods=["POST"])
@require_role(["ADMIN", "SUPER_ADMIN"])
def remove_enrollment(conv_id, enrollment_id):
    user_id = get_jwt_identity()
    user = User.query.get(user_id)

    try:
        ok = convocatoria_service.remove_enrollment(
            conv_id, user.organizationId, user_id, enrollment_id
        )
    except ConvocatoriaError as exc:
        if request.is_json:
            return jsonify({"message": str(exc)}), 422
        flash(str(exc), "danger")
        return redirect(url_for("admin.get_convocatoria_detail", conv_id=conv_id))

    if not ok:
        if request.is_json:
            return jsonify({"message": "Enrollment no encontrado"}), 404
        flash("Enrollment no encontrado.", "warning")
        return redirect(url_for("admin.get_convocatoria_detail", conv_id=conv_id))

    if request.is_json:
        return "", 204
    flash("Alumno dado de baja de la convocatoria.", "success")
    return redirect(url_for("admin.get_convocatoria_detail", conv_id=conv_id))


# ─── Cierre 3 pasos (T10) ─────────────────────────────────────────────────────

@admin_bp.route("/convocatorias/<string:conv_id>/close/preview", methods=["POST"])
@require_role(["ADMIN", "SUPER_ADMIN"])
def close_preview(conv_id):
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    try:
        result = convocatoria_service.close_preview(conv_id, user.organizationId)
    except ConvocatoriaError as exc:
        return jsonify({"message": str(exc)}), 422
    return jsonify(result), 200


@admin_bp.route("/convocatorias/<string:conv_id>/close/initiate", methods=["POST"])
@require_role(["ADMIN", "SUPER_ADMIN"])
def close_initiate(conv_id):
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    data = request.get_json() or {}
    confirmation_text = data.get("confirmation_text", "")
    try:
        conv = convocatoria_service.close_initiate(conv_id, user.organizationId, user_id, confirmation_text)
    except ConvocatoriaError as exc:
        return jsonify({"message": str(exc)}), 422
    return jsonify({"id": conv.id, "status": conv.status.value, "closureInitiatedAt": conv.closureInitiatedAt.isoformat()}), 200


@admin_bp.route("/convocatorias/<string:conv_id>/close/confirm", methods=["POST"])
@require_role(["ADMIN", "SUPER_ADMIN"])
def close_confirm(conv_id):
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    data = request.get_json() or {}
    confirmation_text = data.get("confirmation_text", "")
    password = data.get("password", "")
    try:
        conv, sha256 = convocatoria_service.close_confirm(
            conv_id, user.organizationId, user_id, confirmation_text, password
        )
    except ConvocatoriaError as exc:
        return jsonify({"message": str(exc)}), 422
    return jsonify({
        "id": conv.id,
        "status": conv.status.value,
        "closedAt": conv.closedAt.isoformat(),
        "reverseWindowUntil": conv.reverseWindowUntil.isoformat(),
        "actaSignatureHash": sha256,
        "actaUrl": f"/admin/convocatorias/{conv.id}/acta",
    }), 200


@admin_bp.route("/convocatorias/<string:conv_id>/close/abort", methods=["POST"])
@require_role(["ADMIN", "SUPER_ADMIN"])
def close_abort(conv_id):
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    try:
        conv = convocatoria_service.close_abort(conv_id, user.organizationId, user_id)
    except ConvocatoriaError as exc:
        return jsonify({"message": str(exc)}), 422
    return jsonify({"id": conv.id, "status": conv.status.value}), 200


@admin_bp.route("/convocatorias/<string:conv_id>/close/reverse", methods=["POST"])
@require_role(["SUPER_ADMIN"])
def close_reverse(conv_id):
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    data = request.get_json() or {}
    reason = data.get("reason", "")
    try:
        conv = convocatoria_service.close_reverse(conv_id, user.organizationId, user_id, reason)
    except ConvocatoriaError as exc:
        return jsonify({"message": str(exc)}), 422
    return jsonify({"id": conv.id, "status": conv.status.value, "reversedAt": conv.reversedAt.isoformat()}), 200


@admin_bp.route("/convocatorias/<string:conv_id>/acta", methods=["GET"])
@require_role(["ADMIN", "SUPER_ADMIN"])
def download_acta(conv_id):
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    from app.models.training import Convocatoria, ConvocatoriaStatus
    conv = Convocatoria.query.filter_by(id=conv_id, organizationId=user.organizationId).first()
    if not conv:
        return jsonify({"message": "Convocatoria no encontrada"}), 404
    if conv.status not in (ConvocatoriaStatus.CLOSED, ConvocatoriaStatus.LOCKED):
        return jsonify({"message": "El acta solo está disponible para convocatorias cerradas"}), 409
    if not conv.acta:
        return jsonify({"message": "Acta no disponible"}), 404
    from flask import Response
    filename = f"acta_{conv.name.replace(' ', '_')}_{conv.closedAt.strftime('%Y%m%d')}.pdf"
    return Response(
        conv.acta,
        mimetype="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _convocatoria_to_dict(c):
    return {
        "id": c.id,
        "name": c.name,
        "description": c.description,
        "routePrincipal": c.routePrincipal,
        "plazas": c.plazas,
        "umbralMin": c.umbralMin,
        "status": c.status.value if c.status else None,
        "criteriaVersion": c.criteriaVersion,
        "normalizerVersion": c.normalizerVersion,
        "detectorVersion": c.detectorVersion,
        "openedAt": c.openedAt.isoformat() if c.openedAt else None,
        "closedAt": c.closedAt.isoformat() if c.closedAt else None,
        "enrollments_count": len(c.enrollments) if c.enrollments is not None else 0,
    }


def _enrollment_to_dict(e):
    return {
        "id": e.id,
        "studentId": e.studentId,
        "studentName": e.student.name if e.student else None,
        "studentEmail": e.student.email if e.student else None,
        "routeId": e.routeId,
        "status": e.status.value if e.status else None,
        "attemptsCount": e.attemptsCount,
        "enrolledAt": e.enrolledAt.isoformat() if e.enrolledAt else None,
    }
