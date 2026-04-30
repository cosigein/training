"""Helpers del blueprint mobile_api.

Stubs creados en PR-1; cuerpo se implementa en los PRs siguientes:
- convocatorias_for_user → PR-3
- get_convocatoria_detail → PR-5
- can_user_view_attempt → PR-7
- _remap_conv → PR-3
- _remap_ranking_entry → PR-6
- _remap_attempt → PR-7

Nota: el modelo `User.managedConvocatorias` es `db.Column(JSONB, default=[])`
con la lista de IDs de convocatorias supervisadas, NO un relationship.
Patrón de query: `Convocatoria.query.filter(Convocatoria.id.in_(user.managedConvocatorias or []))`.
"""


def convocatorias_for_user(user):
    raise NotImplementedError("Implementado en PR-3 (feat/be-mobile-api-me)")


def get_convocatoria_detail(conv_id, user):
    raise NotImplementedError("Implementado en PR-5 (feat/be-mobile-api-convocatorias-list)")


def can_user_view_attempt(user, attempt):
    raise NotImplementedError("Implementado en PR-7 (feat/be-mobile-api-attempt-detail)")


def _remap_conv(conv_dict):
    raise NotImplementedError("Implementado en PR-3 (feat/be-mobile-api-me)")


def _remap_ranking_entry(entry_dict):
    raise NotImplementedError("Implementado en PR-6 (feat/be-mobile-api-ranking-matrix)")


def _remap_attempt(attempt_dict):
    raise NotImplementedError("Implementado en PR-7 (feat/be-mobile-api-attempt-detail)")
