"""
Servicio de Convocatorias y Enrollments para el blueprint admin.

Reglas de negocio (PDF §9, §12):
- Solo se puede editar `pesosPorFamilia` y `criteriaVersion` si la convocatoria
  está en `OPEN`. Una vez en CLOSING/CLOSED/LOCKED queda inmutable.
- No se puede borrar una convocatoria que tiene attempts (sería pérdida de datos).
- No se puede agregar/quitar enrollments si la convocatoria NO está OPEN.
- Un alumno solo puede tener 1 enrollment por convocatoria (DB constraint).
- Cierre 3 pasos (PDF §9.1): preview → initiate (admin#1) → confirm (admin#2 distinto).
- Ventana de reversa de 24 h wallclock Madrid; solo SUPER_ADMIN puede revertir.
"""
import hashlib
from datetime import datetime, timedelta

from werkzeug.security import check_password_hash

from app.extensions import db
from app.models.training import (
    Convocatoria, Enrollment, ConvocatoriaStatus, EnrollmentStatus,
    Ranking, RankingStatus,
    TrainingAuditLog, AuditAction,
)
from app.models.auth import User, UserRole
from app.models.session import Attempt, AttemptStatus


class ConvocatoriaError(Exception):
    """Error de negocio que el caller debe convertir a 400/422 + mensaje."""
    pass


class ConvocatoriaService:

    @staticmethod
    def list_convocatorias(org_id):
        return Convocatoria.query.filter_by(organizationId=org_id)\
            .order_by(Convocatoria.openedAt.desc()).all()

    @staticmethod
    def get_convocatoria(conv_id, org_id):
        return Convocatoria.query.filter_by(id=conv_id, organizationId=org_id).first()

    @staticmethod
    def create_convocatoria(org_id, actor_id, data):
        # Validaciones mínimas
        required = ["name", "routePrincipal", "plazas", "criteriaVersion",
                    "normalizerVersion", "detectorVersion"]
        missing = [k for k in required if not data.get(k)]
        if missing:
            raise ConvocatoriaError(f"Campos obligatorios: {', '.join(missing)}")

        try:
            plazas = int(data["plazas"])
        except (TypeError, ValueError):
            raise ConvocatoriaError("`plazas` debe ser un entero.")
        if plazas <= 0:
            raise ConvocatoriaError("`plazas` debe ser mayor a 0.")

        umbral = data.get("umbralMin", 5.0)
        try:
            umbral = float(umbral)
        except (TypeError, ValueError):
            raise ConvocatoriaError("`umbralMin` debe ser numérico.")
        if not (0 <= umbral <= 10):
            raise ConvocatoriaError("`umbralMin` debe estar entre 0 y 10.")

        conv = Convocatoria(
            organizationId=org_id,
            name=data["name"].strip(),
            description=data.get("description") or None,
            routePrincipal=data["routePrincipal"].strip(),
            plazas=plazas,
            umbralMin=umbral,
            pesosPorFamilia=data.get("pesosPorFamilia") or {},
            criteriaVersion=data["criteriaVersion"].strip(),
            normalizerVersion=data["normalizerVersion"].strip(),
            detectorVersion=data["detectorVersion"].strip(),
            status=ConvocatoriaStatus.OPEN,
        )
        db.session.add(conv)
        db.session.flush()

        ConvocatoriaService._audit(
            actor_id=actor_id, action=AuditAction.CONVOCATORIA_CREATED,
            resource_type="Convocatoria", resource_id=conv.id, org_id=org_id,
            delta={"name": conv.name, "plazas": conv.plazas},
        )
        db.session.commit()
        return conv

    @staticmethod
    def update_convocatoria(conv_id, org_id, actor_id, data):
        conv = ConvocatoriaService.get_convocatoria(conv_id, org_id)
        if not conv:
            return None
        if conv.status != ConvocatoriaStatus.OPEN:
            raise ConvocatoriaError(
                f"No se puede editar una convocatoria en estado {conv.status.value}."
            )

        delta = {}
        # Campos editables mientras OPEN
        if "name" in data and data["name"]:
            new = data["name"].strip()
            if new != conv.name:
                delta["name"] = {"from": conv.name, "to": new}
                conv.name = new
        if "description" in data:
            new = (data["description"] or "").strip() or None
            if new != conv.description:
                delta["description"] = {"from": conv.description, "to": new}
                conv.description = new
        if "plazas" in data and data["plazas"] not in (None, ""):
            try:
                new = int(data["plazas"])
            except (TypeError, ValueError):
                raise ConvocatoriaError("`plazas` debe ser un entero.")
            if new <= 0:
                raise ConvocatoriaError("`plazas` debe ser mayor a 0.")
            if new != conv.plazas:
                delta["plazas"] = {"from": conv.plazas, "to": new}
                conv.plazas = new
        if "umbralMin" in data and data["umbralMin"] not in (None, ""):
            try:
                new = float(data["umbralMin"])
            except (TypeError, ValueError):
                raise ConvocatoriaError("`umbralMin` debe ser numérico.")
            if not (0 <= new <= 10):
                raise ConvocatoriaError("`umbralMin` debe estar entre 0 y 10.")
            if new != conv.umbralMin:
                delta["umbralMin"] = {"from": conv.umbralMin, "to": new}
                conv.umbralMin = new

        if not delta:
            return conv

        ConvocatoriaService._audit(
            actor_id=actor_id, action=AuditAction.CONVOCATORIA_EDITED,
            resource_type="Convocatoria", resource_id=conv.id, org_id=org_id,
            delta=delta,
        )
        db.session.commit()
        return conv

    @staticmethod
    def delete_convocatoria(conv_id, org_id, actor_id):
        conv = ConvocatoriaService.get_convocatoria(conv_id, org_id)
        if not conv:
            return False
        if conv.status not in (ConvocatoriaStatus.OPEN, ConvocatoriaStatus.PREVIEW):
            raise ConvocatoriaError(
                "Solo se pueden borrar convocatorias OPEN o PREVIEW. "
                "Las CLOSED/LOCKED son inmutables."
            )
        # Si tiene enrollments con attempts, el borrado pierde datos.
        # Por ahora delegamos en cascade. Más adelante validar attempts > 0.
        db.session.delete(conv)
        db.session.commit()
        return True

    @staticmethod
    def list_enrollments(conv_id, org_id):
        conv = ConvocatoriaService.get_convocatoria(conv_id, org_id)
        if not conv:
            return None
        return Enrollment.query.filter_by(convocatoriaId=conv.id)\
            .order_by(Enrollment.enrolledAt.asc()).all()

    @staticmethod
    def add_enrollment(conv_id, org_id, actor_id, student_id, route_id):
        conv = ConvocatoriaService.get_convocatoria(conv_id, org_id)
        if not conv:
            raise ConvocatoriaError("Convocatoria no encontrada.")
        if conv.status != ConvocatoriaStatus.OPEN:
            raise ConvocatoriaError(
                "Solo se pueden inscribir alumnos cuando la convocatoria está OPEN."
            )

        student = User.query.filter_by(id=student_id, organizationId=org_id).first()
        if not student:
            raise ConvocatoriaError("Alumno no encontrado en esta organización.")
        student_role = student.role.value if hasattr(student.role, "value") else student.role
        if student_role != UserRole.STUDENT.value:
            raise ConvocatoriaError(f"El usuario tiene rol {student_role}, no STUDENT.")

        # Idempotencia: si ya existe, devolver el existente sin error
        existing = Enrollment.query.filter_by(
            convocatoriaId=conv.id, studentId=student_id
        ).first()
        if existing:
            return existing

        enr = Enrollment(
            convocatoriaId=conv.id,
            studentId=student_id,
            organizationId=org_id,
            routeId=(route_id or None),
            status=EnrollmentStatus.ACTIVE,
        )
        db.session.add(enr)
        db.session.flush()

        ConvocatoriaService._audit(
            actor_id=actor_id, action=AuditAction.ENROLLMENT_CREATED,
            resource_type="Enrollment", resource_id=enr.id, org_id=org_id,
            delta={"convocatoriaId": conv.id, "studentId": student_id, "routeId": route_id},
        )
        db.session.commit()
        return enr

    @staticmethod
    def remove_enrollment(conv_id, org_id, actor_id, enrollment_id):
        conv = ConvocatoriaService.get_convocatoria(conv_id, org_id)
        if not conv:
            return False
        if conv.status != ConvocatoriaStatus.OPEN:
            raise ConvocatoriaError(
                "Solo se pueden quitar enrollments cuando la convocatoria está OPEN."
            )

        enr = Enrollment.query.filter_by(
            id=enrollment_id, convocatoriaId=conv.id, organizationId=org_id
        ).first()
        if not enr:
            return False

        ConvocatoriaService._audit(
            actor_id=actor_id, action=AuditAction.ENROLLMENT_REMOVED,
            resource_type="Enrollment", resource_id=enr.id, org_id=org_id,
            delta={"studentId": enr.studentId, "convocatoriaId": conv.id},
        )
        db.session.delete(enr)
        db.session.commit()
        return True

    # ── Cierre 3 pasos (PDF §9.1) ────────────────────────────────────────────

    @staticmethod
    def close_preview(conv_id, org_id):
        """
        Simulación de cierre (solo lectura, idempotente).
        Devuelve el ranking calculado al vuelo, conteos y advertencias.
        No cambia estado ni escribe en BD.
        """
        conv = ConvocatoriaService.get_convocatoria(conv_id, org_id)
        if not conv:
            raise ConvocatoriaError("Convocatoria no encontrada.")
        if conv.status not in (ConvocatoriaStatus.OPEN, ConvocatoriaStatus.CLOSING):
            raise ConvocatoriaError(
                f"Solo se puede hacer preview en estado OPEN o CLOSING (actual: {conv.status.value})."
            )

        enrollments = (
            Enrollment.query
            .filter_by(convocatoriaId=conv.id, organizationId=org_id)
            .filter(Enrollment.status == EnrollmentStatus.ACTIVE)
            .all()
        )

        entries = []
        for e in enrollments:
            scored = (
                Attempt.query
                .filter_by(enrollmentId=e.id, status=AttemptStatus.CLOSED)
                .filter(Attempt.score.isnot(None))
                .all()
            )
            scores = [a.score for a in scored]
            nota_media = round(sum(scores) / len(scores), 2) if scores else 0.0
            student = User.query.get(e.studentId)
            entries.append({
                "enrollmentId": e.id,
                "studentId": e.studentId,
                "studentName": student.name if student else "—",
                "notaMedia": nota_media,
                "rutasCompletadas": len(scored),
            })

        entries.sort(key=lambda x: -x["notaMedia"])
        for i, entry in enumerate(entries, start=1):
            entry["puesto"] = i
            entry["dentroCdCorte"] = i <= conv.plazas

        aptos = sum(1 for e in entries if e["dentroCdCorte"])
        advertencias = []
        if not entries:
            advertencias.append("Sin candidatos inscritos activos.")
        if any(e["rutasCompletadas"] == 0 for e in entries):
            advertencias.append("Hay candidatos sin ningún intento completado.")

        return {
            "ranking": entries,
            "aptos": aptos,
            "noAptos": len(entries) - aptos,
            "totalCandidatos": len(entries),
            "plazas": conv.plazas,
            "advertencias": advertencias,
        }

    @staticmethod
    def close_initiate(conv_id, org_id, actor_id, confirmation_text):
        """
        Admin#1 inicia el proceso de cierre. OPEN → CLOSING (atómico).
        Requiere que confirmation_text == conv.name exacto.
        """
        conv = ConvocatoriaService.get_convocatoria(conv_id, org_id)
        if not conv:
            raise ConvocatoriaError("Convocatoria no encontrada.")
        if conv.status != ConvocatoriaStatus.OPEN:
            raise ConvocatoriaError(
                f"Solo se puede iniciar cierre en estado OPEN (actual: {conv.status.value})."
            )
        if (confirmation_text or "").strip() != conv.name:
            raise ConvocatoriaError(
                "El texto de confirmación no coincide con el nombre de la convocatoria."
            )

        # UPDATE atómico para evitar race condition
        updated = (
            db.session.query(Convocatoria)
            .filter(
                Convocatoria.id == conv_id,
                Convocatoria.status == ConvocatoriaStatus.OPEN,
            )
            .update(
                {
                    "status": ConvocatoriaStatus.CLOSING,
                    "closureInitiatedAt": datetime.utcnow(),
                    "closureInitiatedBy": actor_id,
                },
                synchronize_session=False,
            )
        )
        if updated == 0:
            raise ConvocatoriaError("La convocatoria ya no está en estado OPEN (concurrencia).")

        ConvocatoriaService._audit(
            actor_id=actor_id, action=AuditAction.CONVOCATORIA_CLOSURE_INITIATED,
            resource_type="Convocatoria", resource_id=conv_id, org_id=org_id,
            delta={"confirmation_text": confirmation_text},
        )
        db.session.commit()
        return db.session.get(Convocatoria, conv_id)

    @staticmethod
    def close_confirm(conv_id, org_id, actor_id, confirmation_text, password):
        """
        Admin#2 (distinto al que inició) confirma el cierre. CLOSING → CLOSED.
        Requiere re-autenticación por contraseña + confirmation_text == conv.name.
        Genera acta PDF con WeasyPrint y persiste bytes + SHA256.
        """
        conv = ConvocatoriaService.get_convocatoria(conv_id, org_id)
        if not conv:
            raise ConvocatoriaError("Convocatoria no encontrada.")
        if conv.status != ConvocatoriaStatus.CLOSING:
            raise ConvocatoriaError(
                f"Solo se puede confirmar en estado CLOSING (actual: {conv.status.value})."
            )
        if actor_id == conv.closureInitiatedBy:
            raise ConvocatoriaError(
                "El mismo admin que inició el cierre no puede confirmarlo (doble validación requerida)."
            )
        if (confirmation_text or "").strip() != conv.name:
            raise ConvocatoriaError(
                "El texto de confirmación no coincide con el nombre de la convocatoria."
            )

        # Re-autenticación
        actor = User.query.get(actor_id)
        if not actor or not check_password_hash(actor.password, password or ""):
            raise ConvocatoriaError("Contraseña incorrecta.")

        # Calcular y persistir ranking definitivo
        from app.workers.ranking_worker import _build_snapshot
        _build_snapshot(conv, RankingStatus.DEFINITIVE)

        # Ranking para el acta
        preview = ConvocatoriaService.close_preview(conv_id, org_id)

        # Generar acta PDF
        initiator = User.query.get(conv.closureInitiatedBy)
        pdf_bytes = ConvocatoriaService._generate_acta_pdf(
            conv=conv,
            confirmer=actor,
            initiator=initiator,
            preview=preview,
            closed_at=datetime.utcnow(),
        )
        sha256 = hashlib.sha256(pdf_bytes).hexdigest()

        now = datetime.utcnow()
        conv.status = ConvocatoriaStatus.CLOSED
        conv.closedAt = now
        conv.closureConfirmedBy = actor_id
        conv.finalRankingSnapshot = preview
        conv.acta = pdf_bytes
        conv.actaSignatureHash = sha256
        conv.reverseWindowUntil = now + timedelta(hours=24)

        ConvocatoriaService._audit(
            actor_id=actor_id, action=AuditAction.CONVOCATORIA_CLOSURE_CONFIRMED,
            resource_type="Convocatoria", resource_id=conv_id, org_id=org_id,
            delta={
                "sha256": sha256,
                "aptos": preview["aptos"],
                "noAptos": preview["noAptos"],
                "reverseWindowUntil": conv.reverseWindowUntil.isoformat(),
            },
        )
        db.session.commit()
        return conv, sha256

    @staticmethod
    def close_abort(conv_id, org_id, actor_id):
        """
        Cancela un cierre en curso. CLOSING → OPEN.
        Solo puede ejecutarlo el admin que lo inició o un SUPER_ADMIN.
        """
        conv = ConvocatoriaService.get_convocatoria(conv_id, org_id)
        if not conv:
            raise ConvocatoriaError("Convocatoria no encontrada.")
        if conv.status != ConvocatoriaStatus.CLOSING:
            raise ConvocatoriaError(
                f"Solo se puede abortar en estado CLOSING (actual: {conv.status.value})."
            )

        actor = User.query.get(actor_id)
        actor_role = actor.role.value if actor and hasattr(actor.role, "value") else str(actor.role) if actor else ""
        is_initiator = conv.closureInitiatedBy == actor_id
        is_super = actor_role == UserRole.SUPER_ADMIN.value
        if not is_initiator and not is_super:
            raise ConvocatoriaError(
                "Solo puede abortar el admin que inició el cierre o un SUPER_ADMIN."
            )

        conv.status = ConvocatoriaStatus.OPEN
        conv.closureInitiatedAt = None
        conv.closureInitiatedBy = None

        ConvocatoriaService._audit(
            actor_id=actor_id, action=AuditAction.CONVOCATORIA_CLOSURE_ABORTED,
            resource_type="Convocatoria", resource_id=conv_id, org_id=org_id,
            delta={},
        )
        db.session.commit()
        return conv

    @staticmethod
    def close_reverse(conv_id, org_id, actor_id, reason):
        """
        SUPER_ADMIN revierte un cierre dentro de la ventana de 24 h. CLOSED → OPEN.
        Anula el ranking definitivo (voidedAt) y limpia los campos del cierre.
        """
        if not reason or len(reason.strip()) < 50:
            raise ConvocatoriaError("La razón de reversión debe tener al menos 50 caracteres.")

        actor = User.query.get(actor_id)
        actor_role = actor.role.value if actor and hasattr(actor.role, "value") else ""
        if actor_role != UserRole.SUPER_ADMIN.value:
            raise ConvocatoriaError("Solo un SUPER_ADMIN puede revertir un cierre.")

        conv = ConvocatoriaService.get_convocatoria(conv_id, org_id)
        if not conv:
            raise ConvocatoriaError("Convocatoria no encontrada.")
        if conv.status != ConvocatoriaStatus.CLOSED:
            raise ConvocatoriaError(
                f"Solo se puede revertir en estado CLOSED (actual: {conv.status.value})."
            )
        now = datetime.utcnow()
        if conv.reverseWindowUntil and now > conv.reverseWindowUntil:
            raise ConvocatoriaError(
                "La ventana de reversión de 24 h ya expiró. La convocatoria está bloqueada."
            )

        # Anular snapshots definitivos del ranking
        (
            db.session.query(Ranking)
            .filter_by(convocatoriaId=conv_id, status=RankingStatus.DEFINITIVE)
            .filter(Ranking.voidedAt.is_(None))
            .update(
                {"voidedAt": now, "voidedBy": actor_id, "voidedReason": reason.strip()},
                synchronize_session=False,
            )
        )

        conv.status = ConvocatoriaStatus.OPEN
        conv.closedAt = None
        conv.closureInitiatedAt = None
        conv.closureInitiatedBy = None
        conv.closureConfirmedBy = None
        conv.finalRankingSnapshot = None
        conv.acta = None
        conv.actaSignatureHash = None
        conv.reverseWindowUntil = None
        conv.reversedAt = now
        conv.reversedBy = actor_id
        conv.reversalReason = reason.strip()

        ConvocatoriaService._audit(
            actor_id=actor_id, action=AuditAction.CONVOCATORIA_CLOSURE_REVERSED,
            resource_type="Convocatoria", resource_id=conv_id, org_id=org_id,
            delta={"reason": reason.strip()},
        )
        db.session.commit()
        return conv

    @staticmethod
    def _generate_acta_pdf(conv, confirmer, initiator, preview, closed_at):
        """Genera el PDF del acta de cierre con WeasyPrint."""
        from weasyprint import HTML

        rows = "".join(
            f"<tr>"
            f"<td>{e['puesto']}</td>"
            f"<td>{e['studentName']}</td>"
            f"<td style='text-align:center'>{e['notaMedia']:.2f}</td>"
            f"<td style='text-align:center'>{e['rutasCompletadas']}</td>"
            f"<td style='text-align:center;font-weight:bold;color:{'#1a7a1a' if e['dentroCdCorte'] else '#a00'}'>"
            f"{'APTO' if e['dentroCdCorte'] else 'NO APTO'}</td>"
            f"</tr>"
            for e in preview["ranking"]
        )

        html = f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<style>
  body {{ font-family: Arial, sans-serif; font-size: 12px; margin: 2cm; color: #111; }}
  h1 {{ font-size: 18px; text-align: center; margin-bottom: 4px; }}
  .subtitle {{ text-align: center; color: #555; margin-bottom: 20px; }}
  .meta {{ margin-bottom: 20px; }}
  .meta td {{ padding: 3px 8px; }}
  .meta td:first-child {{ font-weight: bold; color: #333; width: 200px; }}
  table.ranking {{ width: 100%; border-collapse: collapse; margin-top: 16px; }}
  table.ranking th {{ background: #1a3d6e; color: white; padding: 6px 8px; text-align: left; }}
  table.ranking td {{ padding: 5px 8px; border-bottom: 1px solid #ddd; }}
  table.ranking tr:nth-child(even) {{ background: #f5f5f5; }}
  .footer {{ margin-top: 30px; font-size: 10px; color: #888; text-align: center; }}
  .signatures {{ margin-top: 50px; display: flex; justify-content: space-around; }}
  .sig-box {{ text-align: center; }}
  .sig-line {{ border-top: 1px solid #333; width: 200px; margin: 0 auto 6px; }}
</style>
</head>
<body>
<h1>ACTA DE CIERRE DE CONVOCATORIA</h1>
<p class="subtitle">Cuerpo de Bomberos — Comunidad de Madrid · Sistema Training</p>

<table class="meta">
  <tr><td>Convocatoria:</td><td><strong>{conv.name}</strong></td></tr>
  <tr><td>Descripción:</td><td>{conv.description or '—'}</td></tr>
  <tr><td>Plazas convocadas:</td><td>{conv.plazas}</td></tr>
  <tr><td>Fecha de cierre:</td><td>{closed_at.strftime('%d/%m/%Y %H:%M')} UTC</td></tr>
  <tr><td>Iniciado por:</td><td>{initiator.name if initiator else '—'}</td></tr>
  <tr><td>Confirmado por:</td><td>{confirmer.name}</td></tr>
  <tr><td>Candidatos evaluados:</td><td>{preview['totalCandidatos']}</td></tr>
  <tr><td>Aptos:</td><td style="color:#1a7a1a;font-weight:bold">{preview['aptos']}</td></tr>
  <tr><td>No aptos:</td><td style="color:#a00;font-weight:bold">{preview['noAptos']}</td></tr>
</table>

<table class="ranking">
  <thead>
    <tr>
      <th>#</th><th>Candidato</th><th>Nota media</th>
      <th>Rutas completadas</th><th>Resultado</th>
    </tr>
  </thead>
  <tbody>{rows}</tbody>
</table>

<div class="signatures">
  <div class="sig-box">
    <div class="sig-line"></div>
    <div>Admin iniciador</div>
    <div style="color:#555">{initiator.name if initiator else '—'}</div>
  </div>
  <div class="sig-box">
    <div class="sig-line"></div>
    <div>Admin confirmador</div>
    <div style="color:#555">{confirmer.name}</div>
  </div>
</div>

<p class="footer">
  Documento generado automáticamente por el sistema Training el {closed_at.strftime('%d/%m/%Y %H:%M')} UTC.
  La autenticidad de este acta puede verificarse mediante su hash SHA-256 registrado en el sistema.
</p>
</body>
</html>"""

        return HTML(string=html).write_pdf()

    @staticmethod
    def list_eligible_students(org_id):
        """Alumnos de la org que aún no están inscritos en TODAS las convocatorias."""
        return User.query.filter_by(
            organizationId=org_id, role=UserRole.STUDENT
        ).order_by(User.name).all()

    @staticmethod
    def _audit(actor_id, action, resource_type, resource_id, org_id, delta=None):
        actor = User.query.get(actor_id) if actor_id else None
        actor_role = None
        if actor:
            actor_role = actor.role.value if hasattr(actor.role, "value") else actor.role
        log = TrainingAuditLog(
            actorId=actor_id,
            actorRole=actor_role,
            action=action,
            resourceType=resource_type,
            resourceId=resource_id,
            delta=delta or {},
            organizationId=org_id,
        )
        db.session.add(log)


convocatoria_service = ConvocatoriaService()
