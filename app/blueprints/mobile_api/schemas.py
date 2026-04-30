"""Schemas Marshmallow del blueprint mobile_api.

Stubs creados en PR-1. Solo escalares + listas planas; nunca `fields.Nested`
con relaciones lazy de SQLAlchemy (riesgo de DetachedInstanceError).
Cuando se necesita estructura anidada (RankingEntry.candidate, AttemptDetail.events)
el handler construye el dict antes de `schema.dump(...)`.

Implementación por PR:
- UserSchema, AuthLoginResponseSchema → PR-2
- ConvocatoriaSummarySchema → PR-3
- StandingSchema → PR-4
- RankingEntrySchema → PR-6
- AttemptDetailSchema → PR-7
"""

from marshmallow import Schema


class UserSchema(Schema):
    pass


class AuthLoginResponseSchema(Schema):
    pass


class ConvocatoriaSummarySchema(Schema):
    pass


class StandingSchema(Schema):
    pass


class RankingEntrySchema(Schema):
    pass


class AttemptDetailSchema(Schema):
    pass
