"""slack_reader.py — Lee mensajes de un canal de Slack del día indicado.

Usado por `generate_team_report.py` para automatizar la sección de Joel.

Requiere un Bot Token de Slack en `~/.cmadrid-training/slack.token` con scopes:
- `channels:history`  → leer mensajes de canales públicos
- `channels:read`     → resolver nombre del canal
- `groups:history`    → para canales privados (opcional)
- `users:read`        → resolver `user_id` → nombre

Si el archivo de token no existe, las funciones devuelven None (graceful).
"""
from __future__ import annotations

import os
from datetime import date, datetime, time, timezone
from pathlib import Path
from typing import Optional


SLACK_TOKEN_PATH = Path.home() / ".cmadrid-training" / "slack.token"


def _load_token() -> Optional[str]:
    if not SLACK_TOKEN_PATH.is_file():
        return None
    try:
        token = SLACK_TOKEN_PATH.read_text(encoding="utf-8").strip()
        return token if token.startswith("xoxb-") or token.startswith("xoxp-") else None
    except Exception:
        return None


def _day_to_unix_range(target: date) -> tuple[float, float]:
    """Devuelve (start_ts, end_ts) en epoch UTC para el día completo en hora local Madrid."""
    # Aproximación: Madrid es UTC+2 en CEST (abril-octubre), UTC+1 en CET (resto)
    # Para simplificar usamos UTC+2 fijo durante el sprint (28/04 → 11/05).
    offset_hours = 2
    start_local = datetime.combine(target, time.min)
    end_local = datetime.combine(target, time.max)
    start_utc = (start_local - datetime.combine(target, time.min).utcoffset() if start_local.utcoffset() else start_local)
    # Sin tzinfo: convertir restando offset
    start_epoch = (datetime.combine(target, time.min).timestamp()) - offset_hours * 3600
    end_epoch = (datetime.combine(target, time.max).timestamp()) - offset_hours * 3600
    return start_epoch, end_epoch


def fetch_channel_messages(channel_id: str, target_day: date) -> Optional[str]:
    """Lee mensajes del canal del día indicado y los devuelve formateados como texto.

    Retorna None si:
    - No hay token configurado
    - slack_sdk no está instalado
    - La llamada a la API falla (problemas de red, permisos, etc.)

    Retorna string vacío "" si no hay mensajes ese día.
    """
    token = _load_token()
    if not token:
        return None

    try:
        from slack_sdk import WebClient
        from slack_sdk.errors import SlackApiError
    except ImportError:
        return None

    client = WebClient(token=token)
    start_ts, end_ts = _day_to_unix_range(target_day)

    try:
        resp = client.conversations_history(
            channel=channel_id,
            oldest=str(start_ts),
            latest=str(end_ts),
            inclusive=True,
            limit=200,
        )
    except SlackApiError as e:
        return f"_(no se pudo leer Slack: {e.response.get('error', 'unknown')})_"
    except Exception as e:
        return f"_(error consultando Slack: {e})_"

    messages = resp.data.get("messages", [])
    if not messages:
        return ""

    # Cache de nombres de usuario para evitar 1 llamada por mensaje
    user_cache: dict[str, str] = {}

    def resolve_user(uid: str) -> str:
        if uid in user_cache:
            return user_cache[uid]
        try:
            u = client.users_info(user=uid).data.get("user", {})
            name = u.get("real_name") or u.get("name") or uid
        except Exception:
            name = uid
        user_cache[uid] = name
        return name

    # Ordenar por timestamp ascendente (la API devuelve descendente por default)
    messages.sort(key=lambda m: float(m.get("ts", 0)))

    lines: list[str] = []
    for m in messages:
        if m.get("subtype") in ("channel_join", "channel_leave", "bot_message"):
            # ignorar joins/leaves, mensajes de bot
            if m.get("subtype") == "bot_message" and not m.get("text"):
                continue
        text = (m.get("text") or "").strip()
        if not text:
            continue
        user_id = m.get("user") or m.get("bot_id") or "?"
        author = resolve_user(user_id) if user_id.startswith("U") else f"bot:{user_id}"
        ts = float(m.get("ts", 0))
        hh_mm = datetime.fromtimestamp(ts).strftime("%H:%M")
        lines.append(f"**{author}** ({hh_mm}): {text}")

    return "\n\n".join(lines)


if __name__ == "__main__":
    import sys
    channel = sys.argv[1] if len(sys.argv) > 1 else "C0AV8A77E9M"
    day = date.fromisoformat(sys.argv[2]) if len(sys.argv) > 2 else date.today()
    out = fetch_channel_messages(channel, day)
    if out is None:
        print("(sin token configurado o slack_sdk faltante)")
    elif out == "":
        print(f"(sin mensajes en el canal {channel} el {day})")
    else:
        print(out)
