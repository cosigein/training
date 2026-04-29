"""
Endpoints del kiosko.

Por ahora son endpoints públicos (sin JWT) — el dispositivo no se loguea.
En V2: agregar device token via header `X-Kiosk-Token`.
"""
from flask import jsonify, request, current_app
from . import kiosko_bp
from .services import kiosko_service, KioskoError
from app.extensions import csrf


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
