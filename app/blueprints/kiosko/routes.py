"""
Endpoints del kiosko.

Contiene tanto las vistas para el portal del kiosko (UI) como el endpoint de
telemetría (TAP). El UI es público (sin auth) y consulta BD real para mostrar
plazas, rutas y notas. La identificación es por nº de plaza (V1, single-tenant);
en V2 pasa a kioskCode + RFID.
"""
from flask import render_template, request, redirect, url_for, jsonify, current_app
from . import kiosko_bp
from app.extensions import csrf
from .services import (
    kiosko_service,
    KioskoError,
    resolve_enrollment_by_plaza,
    resolve_enrollment_by_rfid,
    resolve_attempt_view,
)
from app.blueprints.student.student_service import (
    get_student_dashboard,
    get_student_intento,
)
from app.models.session import GpsMeasurement


# ── VISTAS (UI pública del kiosko) ──────────────────────────────────────────

@kiosko_bp.route("/")
def index():
    return redirect(url_for("kiosko.login"))


@kiosko_bp.route("/login")
def login():
    return render_template("kiosko/login.html")


@kiosko_bp.route("/entrar", methods=["POST"])
def entrar():
    plaza = (request.form.get("plaza") or "").strip()
    return redirect(url_for("kiosko.rutas", plaza=plaza))


@kiosko_bp.route("/rfid")
def rfid_login():
    """Entrada por tarjeta RFID (HID Bluetooth). El ESP32 tipea el uid de la
    tarjeta + Enter; el JS del login redirige aquí con ?code=<uid>."""
    code = (request.args.get("code") or "").strip()
    resolved = resolve_enrollment_by_rfid(code)
    if not resolved:
        return redirect(url_for("kiosko.login", error="rfid"))

    enrollment, conv, org = resolved
    ctx = get_student_dashboard(enrollment.studentId, org.id, conv.id)
    if not ctx:
        return redirect(url_for("kiosko.login", error="rfid"))

    return render_template(
        "kiosko/rutas.html",
        candidato=ctx["candidato"],
        convocatoria=ctx["convocatoria"],
        rutas=ctx["rutas"],
        nota_media=ctx["nota_media"],
    )


@kiosko_bp.route("/rutas")
def rutas():
    plaza = (request.args.get("plaza") or "").strip()
    conv_id = request.args.get("convocatoria")
    resolved = resolve_enrollment_by_plaza(plaza, conv_id=conv_id)
    if not resolved:
        return redirect(url_for("auth.login"))

    enrollment, conv, org = resolved
    ctx = get_student_dashboard(enrollment.studentId, org.id, conv.id)
    if not ctx:
        return redirect(url_for("auth.login"))

    return render_template(
        "kiosko/rutas.html",
        candidato=ctx["candidato"],
        convocatoria=ctx["convocatoria"],
        rutas=ctx["rutas"],
        nota_media=ctx["nota_media"],
    )


@kiosko_bp.route("/intento/<attempt_id>")
def intento(attempt_id):
    resolved = resolve_attempt_view(attempt_id)
    if not resolved:
        return redirect(url_for("auth.login"))

    attempt, org = resolved
    if not attempt.studentId:
        return redirect(url_for("auth.login"))

    ctx = get_student_intento(attempt_id, attempt.studentId, org.id)
    if not ctx:
        return redirect(url_for("kiosko.login"))

    return render_template(
        "kiosko/intento.html",
        candidato=ctx["candidato"],
        ruta=ctx["ruta"],
        nota_info=ctx["nota_info"],
        attempt_id=attempt_id,
        score_breakdown=ctx["score_breakdown"],
        pedagogico=ctx["pedagogico"],
        convocatoria=ctx["convocatoria"],
    )


@kiosko_bp.route("/ruta/<ruta_id>")
def ruta_detalle(ruta_id):
    """Vista de una ruta sin intento asociado (o info general)."""
    plaza = (request.args.get("plaza") or "").strip()
    conv_id = request.args.get("convocatoria")
    resolved = resolve_enrollment_by_plaza(plaza, conv_id=conv_id)
    if not resolved:
        return redirect(url_for("auth.login"))

    enrollment, conv, org = resolved
    # Aquí podríamos buscar una ruta 'ideal' o simplemente mostrar que está pendiente
    # Por ahora, simulamos un contexto mínimo para no romper el layout
    ctx = {
        "candidato": {"nombre": enrollment.student.name, "plaza": plaza},
        "convocatoria": {"id": conv.id, "nombre": conv.name},
        "ruta": {"id": ruta_id, "label": ruta_id},
        "nota_info": {"nota": 0.0, "data_quality": "N/A", "fecha": "Pendiente", "hora": ""},
        "score_breakdown": [],
        "pedagogico": None,
    }
    return render_template("kiosko/intento.html", **ctx, attempt_id=None)


# ── API (TELEMETRÍA HARDWARE) ───────────────────────────────────────────────

@kiosko_bp.route("/tap", methods=["POST"])
@csrf.exempt   # los kioskos no son navegadores; auth real va en V2 vía device token
def kiosk_tap():
    data = request.get_json(silent=True) or request.form.to_dict() or {}
    kiosk_code = data.get("kioskCode") or data.get("kiosk_code")
    rfid_uid = data.get("rfidUid") or data.get("rfid_uid")

    try:
        attempt, previous = kiosko_service.process_tap(kiosk_code, rfid_uid)
    except KioskoError as exc:
        return jsonify({"error": exc.code, "message": str(exc)}), exc.http
    except Exception as exc:
        current_app.logger.exception("kiosk_tap failed for kioskCode=%s", kiosk_code)
        return jsonify({
            "error": "internal",
            "message": f"{type(exc).__name__}: {str(exc)[:300]}",
        }), 500

    return jsonify({
        "attempt": {
            "id": attempt.id,
            "studentId": attempt.studentId,
            "convocatoriaId": attempt.convocatoriaId,
            "enrollmentId": attempt.enrollmentId,
            "vehicleId": attempt.vehicleId,
            "attemptNumber": attempt.attemptNumber,
            "startTime": attempt.startTime.isoformat(),
            "status": attempt.status.value,
            "criteriaVersionPinned": attempt.criteriaVersionPinned,
        },
        "closedPrevious": (
            {
                "id": previous.id,
                "closedAt": previous.closedAt.isoformat() if previous.closedAt else None,
                "reason": "NEXT_TAP",
            } if previous else None
        ),
    }), 201


@kiosko_bp.route("/intento/<attempt_id>/gps")
def intento_gps(attempt_id):
    """Devuelve la traza GPS del intento como JSON para Leaflet."""
    resolved = resolve_attempt_view(attempt_id)
    if not resolved:
        return jsonify({"points": []}), 200

    attempt, org = resolved
    points = (
        GpsMeasurement.query
        .filter_by(attemptId=attempt_id, organizationId=org.id)
        .order_by(GpsMeasurement.timestamp.asc())
        .with_entities(
            GpsMeasurement.latitude,
            GpsMeasurement.longitude,
            GpsMeasurement.speed,
            GpsMeasurement.confidence,
        )
        .all()
    )

    # Submuestrear si hay muchos puntos (máx 500 para el mapa)
    step = max(1, len(points) // 500)
    sampled = points[::step]

    return jsonify({
        "points": [
            {"lat": p.latitude, "lng": p.longitude,
             "speed": p.speed, "confidence": p.confidence}
            for p in sampled
        ]
    })
