"""drive_client.py — Cliente Google Drive para el cron de informes.

Hace 3 cosas:
  1. Lista archivos modificados HOY en una carpeta (filtra por owner si se quiere).
  2. Descarga un archivo dado su id a una ruta local.
  3. Sube un archivo (PDF, MD) a una carpeta destino.

Setup OAuth (una sola vez):
  - El usuario crea OAuth Desktop credentials en Google Cloud Console y guarda
    `~/.cmadrid-training/credentials.json`.
  - Primera ejecución abre browser para autorizar; el token se guarda en
    `~/.cmadrid-training/token.json` y se refresca solo.

Si las credenciales no están, todas las funciones devuelven None / [] (graceful).
"""
from __future__ import annotations

import io
import os
from datetime import date, datetime, time, timezone, timedelta
from pathlib import Path
from typing import Optional

CONFIG_DIR = Path.home() / ".cmadrid-training"
CREDS_PATH = CONFIG_DIR / "credentials.json"
TOKEN_PATH = CONFIG_DIR / "token.json"

SCOPES = ["https://www.googleapis.com/auth/drive.file", "https://www.googleapis.com/auth/drive.readonly"]


def _get_service():
    try:
        from google.oauth2.credentials import Credentials
        from google.auth.transport.requests import Request
        from google_auth_oauthlib.flow import InstalledAppFlow
        from googleapiclient.discovery import build
    except ImportError:
        return None

    creds = None
    if TOKEN_PATH.is_file():
        try:
            creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), SCOPES)
        except Exception:
            creds = None

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception:
                creds = None
        if not creds:
            if not CREDS_PATH.is_file():
                return None
            flow = InstalledAppFlow.from_client_secrets_file(str(CREDS_PATH), SCOPES)
            # local server flow abre el browser solo en la primera vez
            creds = flow.run_local_server(port=0, open_browser=True)
        # Persistir
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        TOKEN_PATH.write_text(creds.to_json(), encoding="utf-8")

    return build("drive", "v3", credentials=creds, cache_discovery=False)


def list_files_in_folder(folder_id: str, target_day: date, exclude_owner_email: str | None = None) -> list[dict]:
    """Lista archivos creados/modificados durante el día indicado dentro de la carpeta.

    Retorna lista de dicts con keys: id, title, mimeType, owner_email, modifiedTime.
    Si no hay credenciales, retorna [].
    """
    svc = _get_service()
    if svc is None:
        return []

    # Rango UTC para el día completo Europe/Madrid (UTC+2 en sprint)
    offset = timedelta(hours=2)
    start = datetime.combine(target_day, time.min) - offset
    end = datetime.combine(target_day, time.max) - offset
    start_iso = start.strftime("%Y-%m-%dT%H:%M:%S") + "Z"
    end_iso = end.strftime("%Y-%m-%dT%H:%M:%S") + "Z"

    q = (
        f"'{folder_id}' in parents and trashed = false "
        f"and modifiedTime >= '{start_iso}' "
        f"and modifiedTime <= '{end_iso}'"
    )
    try:
        resp = svc.files().list(
            q=q,
            fields="files(id,name,mimeType,owners(emailAddress,displayName),modifiedTime)",
            pageSize=50,
        ).execute()
    except Exception:
        return []

    files = []
    for f in resp.get("files", []):
        owners = f.get("owners") or [{}]
        owner_email = owners[0].get("emailAddress", "")
        if exclude_owner_email and owner_email.lower() == exclude_owner_email.lower():
            continue
        files.append({
            "id": f["id"],
            "title": f["name"],
            "mimeType": f["mimeType"],
            "owner_email": owner_email,
            "owner_name": owners[0].get("displayName", ""),
            "modifiedTime": f["modifiedTime"],
        })
    return files


def download_file(file_id: str, dest_path: Path, mime_type: str | None = None) -> bool:
    """Descarga un archivo a dest_path. Si es Google Doc, lo exporta a PDF.

    Retorna True si fue OK, False si falló o no hay credenciales.
    """
    svc = _get_service()
    if svc is None:
        return False

    try:
        from googleapiclient.http import MediaIoBaseDownload
        if mime_type and mime_type.startswith("application/vnd.google-apps."):
            # Google Doc/Sheet/Slide → exportar a PDF
            request = svc.files().export_media(fileId=file_id, mimeType="application/pdf")
        else:
            request = svc.files().get_media(fileId=file_id)
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        with dest_path.open("wb") as fh:
            downloader = MediaIoBaseDownload(fh, request)
            done = False
            while not done:
                _, done = downloader.next_chunk()
        return True
    except Exception:
        return False


def upload_file(local_path: Path, parent_folder_id: str, title: str | None = None, mime_type: str = "application/pdf") -> Optional[str]:
    """Sube un archivo al folder. Devuelve el id del archivo subido o None si falla."""
    svc = _get_service()
    if svc is None:
        return None
    if not local_path.is_file():
        return None
    try:
        from googleapiclient.http import MediaFileUpload
        body = {
            "name": title or local_path.name,
            "parents": [parent_folder_id],
        }
        media = MediaFileUpload(str(local_path), mimetype=mime_type, resumable=False)
        f = svc.files().create(body=body, media_body=media, fields="id,name,webViewLink").execute()
        return f.get("id")
    except Exception:
        return None


if __name__ == "__main__":
    import sys
    folder = sys.argv[1] if len(sys.argv) > 1 else "1vjwi97QmwcUkzVj2LtPshZmGE5AEoZFD"
    day = date.fromisoformat(sys.argv[2]) if len(sys.argv) > 2 else date.today()
    files = list_files_in_folder(folder, day, exclude_owner_email="antoniohermoso92@gmail.com")
    if not files:
        print("(sin archivos del equipo hoy o sin credenciales)")
    else:
        print(f"Archivos del equipo en {folder} el {day}:")
        for f in files:
            print(f"  - {f['title']} ({f['mimeType']}) by {f['owner_name']} <{f['owner_email']}>")
