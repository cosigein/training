"""Schemas Marshmallow del blueprint mobile_api.

Política: solo escalares + listas planas; nunca `fields.Nested` con relaciones
SQLAlchemy lazy (riesgo DetachedInstanceError). Cuando se necesita estructura
anidada, el handler construye el dict antes de `schema.dump(...)`.

Implementación por PR:
- UserSchema, AuthLoginResponseSchema → PR-2 ✅
- ConvocatoriaSummarySchema → PR-3 ✅
- StandingSchema → PR-4
- RankingEntrySchema → PR-6
- AttemptDetailSchema → PR-7
"""

from marshmallow import Schema, fields


class UserSchema(Schema):
    id = fields.String(dump_only=True)
    email = fields.String(dump_only=True)
    name = fields.String(dump_only=True)
    role = fields.Method("get_role", dump_only=True)
    organizationId = fields.String(dump_only=True)
    studentProfileId = fields.String(dump_only=True, allow_none=True)

    def get_role(self, obj):
        role = getattr(obj, "role", None)
        return role.value if hasattr(role, "value") else role


class AuthLoginResponseSchema(Schema):
    """Documental — handler construye el dict manual."""
    access_token = fields.String(required=True)
    refresh_token = fields.String(required=True)
    token_type = fields.String(dump_default="Bearer")
    expires_in = fields.Integer(required=True)


class ConvocatoriaSummarySchema(Schema):
    id = fields.String(dump_only=True)
    name = fields.String(dump_only=True)
    description = fields.String(dump_only=True)
    status = fields.String(dump_only=True, allow_none=True)
    plazas = fields.Integer(dump_only=True)
    totalCandidates = fields.Integer(dump_only=True)
    closedAt = fields.String(dump_only=True, allow_none=True)
    updatedAt = fields.String(dump_only=True, allow_none=True)


class StandingSchema(Schema):
    pass


class RankingEntrySchema(Schema):
    pass


class AttemptDetailSchema(Schema):
    pass
