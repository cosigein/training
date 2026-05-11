from datetime import datetime
from flask import jsonify, request, render_template, redirect, url_for, flash, current_app
from . import admin_bp
from .services import admin_service
from .convocatoria_service import convocatoria_service, ConvocatoriaError
from app.utils.decorators import jwt_required, get_jwt_identity, require_role
from app.models.auth import User, UserRole
from app.models.training import RfidCard, Enrollment, EnrollmentStatus
from app.extensions import db

# ─────────────────────────────────────────────────────────────────────────────
# MOCK PARA PRUEBAS UI (Eliminar en producción)
# ─────────────────────────────────────────────────────────────────────────────
class MockUser:
    id = "mock-123"
    name = "Admin Prueba"
    is_authenticated = True
    organizationId = "org-1"
    class role:
        value = "SUPER_ADMIN"

MOCK_CONVOCATORIAS = [
    {
        "id": "conv-a-2026", "name": "CM-2026-A", "status": "OPEN",
        "plazas": 50, "candidatos": 198,
        "cierre": "15/06/2026", "completados": 156, "pendientes": 42,
    },
    {
        "id": "conv-b-2026", "name": "CM-2026-B", "status": "CLOSING",
        "plazas": 30, "candidatos": 147,
        "cierre": "20/05/2026", "completados": 147, "pendientes": 0,
        "iniciado_por": "María García", "iniciado_hace": "12 minutos",
    },
    {
        "id": "conv-z-2025", "name": "CM-2025-Z", "status": "LOCKED",
        "plazas": 25, "candidatos": 112,
        "cierre": "30/11/2025", "completados": 112, "pendientes": 0,
    },
]

MOCK_SYSTEM_STATUS = {
    "api_ok": True, "db_ok": True,
    "webfleet_cuota": 22,
    "kioskos_online": 4, "kioskos_total": 6,
    "candidatos_total": 457,
    "intentos_hoy": 12,
}

MOCK_GDPR_REQUESTS = [
    {"id": "gr-001", "alumno": "Juan Carlos Pérez López", "tipo": "Olvido", "fecha": "01/05/2026", "estado": "PENDING"},
    {"id": "gr-002", "alumno": "María del Carmen García Ruiz", "tipo": "Acceso", "fecha": "28/04/2026", "estado": "APPROVED"},
    {"id": "gr-003", "alumno": "Pedro Antonio Fernández Díaz", "tipo": "Olvido", "fecha": "25/04/2026", "estado": "REJECTED"},
]

MOCK_USUARIOS = [
    {"id": "u-001", "nombre": "Antonio Hermoso", "email": "ahermoso@cmadrid.es", "rol": "SUPER_ADMIN", "acceso": "05/05/2026 09:12"},
    {"id": "u-002", "nombre": "María García Soto", "email": "mgarcia@cmadrid.es", "rol": "ADMIN", "acceso": "05/05/2026 08:45"},
    {"id": "u-003", "nombre": "Carlos Ruiz Martínez", "email": "cruiz@cmadrid.es", "rol": "ADMIN", "acceso": "04/05/2026 16:30"},
    {"id": "u-004", "nombre": "Ana Romero Vidal", "email": "aromero@cmadrid.es", "rol": "MANAGER", "acceso": "05/05/2026 09:00"},
    {"id": "u-005", "nombre": "Luis Castro Pinto", "email": "lcastro@cmadrid.es", "rol": "MANAGER", "acceso": "04/05/2026 14:22"},
    # Alumnos de las convocatorias
    {"id": "u-006", "nombre": "María García López", "email": "mgarcia.l@alumno.es", "rol": "ALUMNO", "acceso": "06/05/2026 10:15"},
    {"id": "u-007", "nombre": "Elena Jiménez Torres", "email": "ejimenez@alumno.es", "rol": "ALUMNO", "acceso": "06/05/2026 09:30"},
    {"id": "u-008", "nombre": "Roberto Gómez Paz", "email": "rgomez@alumno.es", "rol": "ALUMNO", "acceso": "05/05/2026 18:20"},
    {"id": "u-009", "nombre": "Pedro Sánchez Villa", "email": "psanchez@alumno.es", "rol": "ALUMNO", "acceso": "06/05/2026 11:00"},
    {"id": "u-010", "nombre": "Ana Romero Díaz", "email": "aromero.d@alumno.es", "rol": "ALUMNO", "acceso": "05/05/2026 09:45"},
    {"id": "u-011", "nombre": "Lucía Fernández", "email": "lfernandez@alumno.es", "rol": "ALUMNO", "acceso": "04/05/2026 12:10"},
    {"id": "u-012", "nombre": "Francisco Morales Vega", "email": "fmorales@alumno.es", "rol": "ALUMNO", "acceso": "06/05/2026 08:50"},
    {"id": "u-013", "nombre": "Carmen López Blanco", "email": "clopez@alumno.es", "rol": "ALUMNO", "acceso": "05/05/2026 20:15"},
    {"id": "u-014", "nombre": "Javier Herrero Ortega", "email": "jherrero@alumno.es", "rol": "ALUMNO", "acceso": "05/05/2026 15:40"},
    {"id": "u-015", "nombre": "Miguel Ángel Ruiz", "email": "mruiz@alumno.es", "rol": "ALUMNO", "acceso": "04/05/2026 17:22"},
    {"id": "u-016", "nombre": "Isabel Navarro Cid", "email": "inavarro@alumno.es", "rol": "ALUMNO", "acceso": "Hoy 09:00"},
]

# ─────────────────────────────────────────────────────────────────────────────
# UI Views (Admin Portal)
# ─────────────────────────────────────────────────────────────────────────────

@admin_bp.route("/dashboard", endpoint="dashboard", methods=["GET"])
@require_role(["ADMIN", "SUPER_ADMIN"])
def admin_dashboard():
    return render_template("admin/dashboard.html",
        current_user=MockUser(),
        active_page="dashboard",
        convocatorias=MOCK_CONVOCATORIAS,
        stats=MOCK_SYSTEM_STATUS,
    )

@admin_bp.route("/matriz", endpoint="matriz", methods=["GET"])
@require_role(["ADMIN", "SUPER_ADMIN"])
def admin_matriz():
    return render_template("admin/matriz.html",
        current_user=MockUser(),
        active_page="matriz",
        convocatorias=MOCK_CONVOCATORIAS,
    )

@admin_bp.route("/simulador", endpoint="simulador", methods=["GET"])
@require_role(["ADMIN", "SUPER_ADMIN"])
def admin_simulador():
    return render_template("admin/simulador.html",
        current_user=MockUser(),
        active_page="simulador",
        convocatorias=MOCK_CONVOCATORIAS,
    )

@admin_bp.route("/cierre", endpoint="cierre", methods=["GET"])
@admin_bp.route("/cierre/<string:conv_id>", endpoint="cierre_detail", methods=["GET"])
@require_role(["ADMIN", "SUPER_ADMIN"])
def admin_cierre(conv_id=None):
    return render_template("admin/cierre.html",
        current_user=MockUser(),
        active_page="cierre",
        convocatorias=[c for c in MOCK_CONVOCATORIAS if c["status"] in ("OPEN", "CLOSING", "CLOSED")],
        target_conv_id=conv_id
    )

@admin_bp.route("/gdpr-panel", endpoint="gdpr", methods=["GET"])
@require_role(["ADMIN", "SUPER_ADMIN"])
def admin_gdpr():
    return render_template("admin/gdpr.html",
        current_user=MockUser(),
        active_page="gdpr",
        solicitudes=MOCK_GDPR_REQUESTS,
    )

@admin_bp.route("/convocatorias-panel", endpoint="convocatorias", methods=["GET"])
@require_role(["ADMIN", "SUPER_ADMIN"])
def admin_convocatorias_ui():
    return render_template("admin/convocatorias.html",
        current_user=MockUser(),
        active_page="convocatorias",
        convocatorias=MOCK_CONVOCATORIAS,
    )

@admin_bp.route("/usuarios-panel", endpoint="usuarios", methods=["GET"])
@require_role(["ADMIN", "SUPER_ADMIN"])
def admin_usuarios_ui():
    return render_template("admin/usuarios.html",
        current_user=MockUser(),
        active_page="usuarios",
        usuarios=MOCK_USUARIOS,
    )

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
    # D-FE-001 opción C: la vista lista vive en /manager/convocatorias
    return redirect(url_for("manager.convocatorias"))


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
    # Demo/Mock check
    mock_conv = next((c for c in MOCK_CONVOCATORIAS if c["id"] == conv_id), None)
    
    from app.models.training import Convocatoria, ConvocatoriaStatus
    conv = Convocatoria.query.filter_by(id=conv_id, organizationId=user.organizationId).first()
    
    if not conv and not mock_conv:
        return jsonify({"message": "Convocatoria no encontrada"}), 404
    
    # If it's a mock or real but locked/closed
    status = conv.status if conv else mock_conv["status"]
    if status not in (ConvocatoriaStatus.CLOSED, ConvocatoriaStatus.LOCKED, "CLOSED", "LOCKED"):
        return jsonify({"message": "El acta solo está disponible para convocatorias cerradas"}), 409
    
    from flask import Response
    if mock_conv and not conv:
        # Return a valid minimal PDF for demo
        dummy_pdf = (
            b"%PDF-1.1\n"
            b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
            b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n"
            b"3 0 obj\n<< /Type /Page /Parent 2 0 R /Resources << /Font << /F1 4 0 R >> >> /MediaBox [0 0 612 792] /Contents 5 0 R >>\nendobj\n"
            b"4 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n"
            b"5 0 obj\n<< /Length 50 >>\nstream\nBT /F1 24 Tf 100 700 Td (Acta de Convocatoria - DEMO) Tj ET\nendstream\n"
            b"endobj\n"
            b"xref\n0 6\n0000000000 65535 f \n0000000010 00000 n \n0000000059 00000 n \n0000000116 00000 n \n0000000223 00000 n \n0000000295 00000 n \ntrailer\n<< /Size 6 /Root 1 0 R >>\nstartxref\n395\n%%EOF"
        )
        filename = f"acta_{mock_conv['name'].replace(' ', '_')}_20260101.pdf"
        return Response(
            dummy_pdf,
            mimetype="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
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


# ─── GDPR (T12) ───────────────────────────────────────────────────────────────

@admin_bp.route("/gdpr/forget-requests", methods=["GET"])
@require_role(["ADMIN", "SUPER_ADMIN"])
def gdpr_list_forget_requests():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    from app.models.training import GdprForgetRequest, GdprForgetStatus
    status_filter = request.args.get("status")
    q = GdprForgetRequest.query.filter_by(organizationId=user.organizationId)
    if status_filter:
        try:
            q = q.filter_by(status=GdprForgetStatus(status_filter))
        except ValueError:
            pass
    requests_list = q.order_by(GdprForgetRequest.requestedAt.desc()).all()
    return jsonify([{
        "id": r.id,
        "studentId": r.studentId,
        "studentName": r.student.name if r.student else "—",
        "reason": r.reason,
        "status": r.status.value,
        "requestedAt": r.requestedAt.isoformat(),
        "approvedAt": r.approvedAt.isoformat() if r.approvedAt else None,
    } for r in requests_list]), 200


@admin_bp.route("/gdpr/forget-requests/<string:req_id>/approve", methods=["POST"])
@require_role(["SUPER_ADMIN"])
def gdpr_approve_forget_request(req_id):
    from datetime import datetime
    from app.models.training import GdprForgetRequest, GdprForgetStatus, TrainingAuditLog, AuditAction
    user_id = get_jwt_identity()
    user = User.query.get(user_id)

    fr = GdprForgetRequest.query.filter_by(id=req_id, organizationId=user.organizationId).first()
    if not fr:
        return jsonify({"message": "Solicitud no encontrada"}), 404
    if fr.status != GdprForgetStatus.PENDING:
        return jsonify({"message": f"La solicitud ya está en estado {fr.status.value}"}), 409

    fr.status = GdprForgetStatus.APPROVED
    fr.approvedBy = user_id
    fr.approvedAt = datetime.utcnow()

    from app.extensions import db as _db
    _db.session.add(TrainingAuditLog(
        actorId=user_id, actorRole="SUPER_ADMIN",
        action=AuditAction.GDPR_FORGET_APPROVED,
        resourceType="GdprForgetRequest", resourceId=req_id,
        delta={"studentId": fr.studentId},
        organizationId=user.organizationId,
    ))
    _db.session.commit()
    return jsonify({"id": fr.id, "status": fr.status.value, "approvedAt": fr.approvedAt.isoformat()}), 200


@admin_bp.route("/gdpr/forget-requests", methods=["POST"])
@require_role(["ADMIN", "SUPER_ADMIN"])
def gdpr_create_forget_request():
    """Permite al admin registrar manualmente una solicitud GDPR de un alumno."""
    from app.models.training import GdprForgetRequest
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    data = request.get_json() or {}
    student_id = data.get("studentId", "")
    reason = data.get("reason", "")
    if not student_id:
        return jsonify({"message": "Se requiere studentId"}), 400

    from app.extensions import db as _db
    fr = GdprForgetRequest(
        studentId=student_id,
        organizationId=user.organizationId,
        reason=reason,
    )
    _db.session.add(fr)
    _db.session.commit()
    return jsonify({"id": fr.id, "status": fr.status.value}), 201


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


# ── Gestión de tarjetas RFID ───────────────────────────────────────────────────

@admin_bp.route("/rfid")
@require_role(["ADMIN"])
def rfid_cards():
    org_id = get_jwt_identity()
    user = User.query.get(org_id)
    org_id = user.organizationId if user else None

    cards = (
        RfidCard.query
        .filter_by(organizationId=org_id)
        .order_by(RfidCard.createdAt.desc())
        .all()
    )
    students = (
        User.query
        .filter_by(organizationId=org_id, role=UserRole.STUDENT)
        .order_by(User.name)
        .all()
    )
    cards_data = []
    for c in cards:
        student = User.query.get(c.assignedTo) if c.assignedTo else None
        cards_data.append({
            "id": c.id,
            "uid": c.uid,
            "active": c.active,
            "assignedTo": c.assignedTo,
            "studentName": student.name if student else None,
            "studentEmail": student.email if student else None,
            "assignedAt": c.assignedAt.strftime("%d/%m/%Y") if c.assignedAt else None,
            "revokedAt": c.revokedAt.strftime("%d/%m/%Y") if c.revokedAt else None,
        })

    return render_template(
        "admin/rfid.html",
        cards=cards_data,
        students=students,
        active_page="rfid",
    )


@admin_bp.route("/rfid", methods=["POST"])
@require_role(["ADMIN"])
def rfid_create():
    org_id = get_jwt_identity()
    user = User.query.get(org_id)
    org_id = user.organizationId if user else None

    uid = (request.form.get("uid") or "").strip()
    student_id = (request.form.get("student_id") or "").strip()

    if not uid:
        flash("El código de tarjeta no puede estar vacío.", "danger")
        return redirect(url_for("admin.rfid_cards"))

    existing = RfidCard.query.filter_by(uid=uid, organizationId=org_id, active=True).first()
    if existing:
        flash(f"Ya existe una tarjeta activa con el código «{uid}».", "danger")
        return redirect(url_for("admin.rfid_cards"))

    card = RfidCard(
        uid=uid,
        organizationId=org_id,
        assignedTo=student_id or None,
        assignedAt=datetime.utcnow() if student_id else None,
        active=True,
    )
    db.session.add(card)
    db.session.commit()
    flash(f"Tarjeta «{uid}» registrada correctamente.", "success")
    return redirect(url_for("admin.rfid_cards"))


@admin_bp.route("/rfid/<string:card_id>/assign", methods=["POST"])
@require_role(["ADMIN"])
def rfid_assign(card_id):
    org_id = get_jwt_identity()
    user = User.query.get(org_id)
    org_id = user.organizationId if user else None

    card = RfidCard.query.filter_by(id=card_id, organizationId=org_id).first_or_404()
    student_id = (request.form.get("student_id") or "").strip()
    card.assignedTo = student_id or None
    card.assignedAt = datetime.utcnow() if student_id else None
    db.session.commit()
    flash("Asignación actualizada.", "success")
    return redirect(url_for("admin.rfid_cards"))


@admin_bp.route("/rfid/<string:card_id>/revoke", methods=["POST"])
@require_role(["ADMIN"])
def rfid_revoke(card_id):
    org_id = get_jwt_identity()
    user = User.query.get(org_id)
    org_id = user.organizationId if user else None

    card = RfidCard.query.filter_by(id=card_id, organizationId=org_id).first_or_404()
    card.active = False
    card.revokedAt = datetime.utcnow()
    db.session.commit()
    flash(f"Tarjeta «{card.uid}» revocada.", "warning")
    return redirect(url_for("admin.rfid_cards"))