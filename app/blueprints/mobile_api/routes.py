from datetime import datetime, timezone

from flask import jsonify

from app.blueprints.mobile_api import mobile_api_bp


@mobile_api_bp.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "ok",
        "version": "v1",
        "time": datetime.now(timezone.utc).isoformat(),
    })
