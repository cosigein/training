"""Integration tests del blueprint /api/v1/* (mobile_api).

Cubren los escenarios SC-1, SC-6, SC-10, SC-11, SC-13, SC-14, SC-16, SC-18, SC-20 del spec
mobile-api-v1-foundation. Asumen seed_demo.py corrido en la BD de test.
"""

import pytest

from app.models.auth import User, UserRole
from app.models.session import Attempt
from app.models.training import Convocatoria, Enrollment, EnrollmentStatus


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _first_by_role(role):
    if isinstance(role, list):
        return User.query.filter(User.role.in_(role)).first()
    return User.query.filter(User.role == role).first()


# ─────────────────────────────────────────────────────────────────────────────
# Tests
# ─────────────────────────────────────────────────────────────────────────────

def test_health_returns_ok(client):
    """SC-20: GET /api/v1/health (sin auth) → 200 con shape esperada."""
    r = client.get("/api/v1/health")
    assert r.status_code == 200
    body = r.get_json()
    assert body["status"] == "ok"
    assert body["version"] == "v1"
    assert "time" in body


def test_login_invalid_credentials_returns_401_json(client):
    """SC-2 (negativo): login con creds inválidas → 401 JSON `{error:"unauthenticated"}`."""
    r = client.post(
        "/api/v1/auth/login",
        json={"email": "no-existe@cmadrid.com", "password": "wrong"},
    )
    assert r.status_code == 401
    body = r.get_json()
    assert body["error"] == "unauthenticated"
    # Las cookies NO deben venir seteadas en este endpoint
    assert "Set-Cookie" not in r.headers


def test_me_with_valid_header_returns_user(client, db, auth_headers_for):
    """SC-6: GET /api/v1/me con Bearer válido → 200 + UserSchema."""
    user = User.query.first()
    assert user is not None, "seed_demo.py debe haber creado al menos un user"
    r = client.get("/api/v1/me", headers=auth_headers_for(user.id))
    assert r.status_code == 200
    body = r.get_json()
    assert body["id"] == user.id
    assert body["email"] == user.email
    assert "role" in body
    assert "organizationId" in body


def test_me_without_token_returns_401(client):
    """SC-7: GET /api/v1/me sin token → 401 JSON (no redirect)."""
    r = client.get("/api/v1/me")
    assert r.status_code == 401
    body = r.get_json()
    assert body is not None
    assert "message" in body or "error" in body


def test_standing_for_non_enrolled_student_returns_404(client, db, auth_headers_for):
    """SC-11: STUDENT pidiendo conv en la que no está enrolled → 404."""
    student = _first_by_role(UserRole.STUDENT)
    if student is None:
        pytest.skip("seed_demo.py no creó STUDENT")
    r = client.get(
        "/api/v1/me/convocatorias/inexistente-xyz/standing",
        headers=auth_headers_for(student.id),
    )
    assert r.status_code == 404


def test_standing_as_manager_returns_403(client, db, auth_headers_for):
    """SC-12: MANAGER pidiendo standing (STUDENT-only) → 403 JSON."""
    manager = _first_by_role(UserRole.MANAGER)
    if manager is None:
        pytest.skip("seed_demo.py no creó MANAGER")
    r = client.get(
        "/api/v1/me/convocatorias/cualquier/standing",
        headers=auth_headers_for(manager.id),
    )
    assert r.status_code == 403


def test_ranking_as_admin_returns_list_without_within_cutoff(client, db, auth_headers_for):
    """SC-13 + R-S-6: ADMIN pidiendo ranking → 200, sin `withinCutoff` en el body."""
    admin = _first_by_role([UserRole.ADMIN, UserRole.SUPER_ADMIN])
    if admin is None:
        pytest.skip("seed_demo.py no creó ADMIN/SUPER_ADMIN")
    conv = Convocatoria.query.filter_by(organizationId=admin.organizationId).first()
    if conv is None:
        pytest.skip("seed_demo.py no creó Convocatoria")
    r = client.get(
        f"/api/v1/convocatorias/{conv.id}/ranking",
        headers=auth_headers_for(admin.id),
    )
    assert r.status_code == 200
    body = r.get_json()
    assert "convocatoria" in body
    assert "entries" in body
    body_text = str(body)
    assert "withinCutoff" not in body_text, "withinCutoff NO debe aparecer (D-API-001 GDPR)"
    assert "dentro_del_corte" not in body_text


def test_ranking_as_student_returns_403(client, db, auth_headers_for):
    """SC-14: STUDENT pidiendo ranking admin-only → 403."""
    student = _first_by_role(UserRole.STUDENT)
    if student is None:
        pytest.skip("seed_demo.py no creó STUDENT")
    r = client.get(
        "/api/v1/convocatorias/cualquier/ranking",
        headers=auth_headers_for(student.id),
    )
    assert r.status_code == 403


def test_attempt_as_admin_returns_detail(client, db, auth_headers_for):
    """SC-16: ADMIN pidiendo attempt detail → 200 con shape AttemptDetailSchema."""
    admin = _first_by_role([UserRole.ADMIN, UserRole.SUPER_ADMIN])
    if admin is None:
        pytest.skip("seed_demo.py no creó ADMIN/SUPER_ADMIN")
    attempt = Attempt.query.filter_by(organizationId=admin.organizationId).first()
    if attempt is None:
        pytest.skip("seed_demo.py no creó Attempt")
    r = client.get(
        f"/api/v1/attempts/{attempt.id}",
        headers=auth_headers_for(admin.id),
    )
    assert r.status_code == 200
    body = r.get_json()
    assert body["id"] == attempt.id
    assert "candidate" in body and "id" in body["candidate"]
    assert "route" in body
    assert "scoreBreakdown" in body and isinstance(body["scoreBreakdown"], list)
    assert "events" in body and isinstance(body["events"], list)


def test_attempt_for_non_owner_student_returns_404(client, db, auth_headers_for):
    """SC-18 + R-S-1: STUDENT que no es dueño del attempt → 404 (no 403, no leakea existencia)."""
    student_attempt = Attempt.query.join(User, Attempt.studentId == User.id).filter(User.role == UserRole.STUDENT).first()
    if student_attempt is None:
        pytest.skip("seed_demo.py no creó Attempt de STUDENT")
    other = User.query.filter(User.role == UserRole.STUDENT, User.id != student_attempt.studentId).first()
    if other is None:
        pytest.skip("seed_demo.py no creó otro STUDENT")
    r = client.get(
        f"/api/v1/attempts/{student_attempt.id}",
        headers=auth_headers_for(other.id),
    )
    assert r.status_code == 404, f"Esperado 404 para STUDENT ajeno, got {r.status_code}"
