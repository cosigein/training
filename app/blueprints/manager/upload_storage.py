"""Almacenamiento temporal de archivos del Doback Elite entre los pasos del wizard.

Los 3 archivos (gps, estabilidad, rotativo) se guardan en
`/tmp/training-uploads/<upload_id>/` cuando el manager los sube en el paso 1.
En el paso 2, los recuperamos por `upload_id`, filtramos por sesión elegida y
disparamos el pipeline. Después se borra el directorio.

Si el manager abandona el wizard, los archivos quedan en /tmp y un cron diario
los limpia (no implementado aquí — TTL implícito por el sistema).
"""
import os
import shutil
import uuid
from pathlib import Path
from typing import Optional

_BASE_DIR = Path("/tmp/training-uploads")
_FILES = ("gps", "stability", "rotativo")


class UploadStorageError(Exception):
    pass


def _ensure_base():
    _BASE_DIR.mkdir(parents=True, exist_ok=True)


def create_upload(
    org_id: str,
    attempt_id: str,
    gps_bytes: bytes,
    stability_bytes: bytes,
    rotativo_bytes: bytes,
) -> str:
    """Guarda los 3 archivos en disco bajo un upload_id nuevo y devuelve el id.
    Los tres son obligatorios."""
    if not gps_bytes:
        raise UploadStorageError("El archivo de GPS es obligatorio.")
    if not stability_bytes:
        raise UploadStorageError("El archivo de ESTABILIDAD es obligatorio.")
    if not rotativo_bytes:
        raise UploadStorageError("El archivo de ROTATIVO es obligatorio.")

    _ensure_base()
    upload_id = uuid.uuid4().hex
    folder = _BASE_DIR / upload_id
    folder.mkdir(parents=True, exist_ok=False)

    # Marker con metadata para validación posterior (org + attempt)
    (folder / "meta.txt").write_text(f"{org_id}\n{attempt_id}\n", encoding="utf-8")
    (folder / "gps.txt").write_bytes(gps_bytes)
    (folder / "stability.txt").write_bytes(stability_bytes)
    (folder / "rotativo.txt").write_bytes(rotativo_bytes)

    return upload_id


def read_upload(org_id: str, attempt_id: str, upload_id: str) -> dict:
    """Devuelve un dict con los contenidos `gps`, `stability`, `rotativo` (o None
    si el archivo no se subió). Valida que el upload pertenece al attempt+org
    para evitar acceso cruzado por id adivinado."""
    folder = _BASE_DIR / upload_id
    meta_path = folder / "meta.txt"
    if not meta_path.exists():
        raise UploadStorageError("Upload no encontrado o expirado.")

    parts = meta_path.read_text(encoding="utf-8").splitlines()
    if len(parts) < 2 or parts[0] != org_id or parts[1] != attempt_id:
        raise UploadStorageError("Upload no pertenece a este intento.")

    def _read(name: str) -> Optional[str]:
        p = folder / f"{name}.txt"
        if not p.exists():
            return None
        return p.read_text(encoding="utf-8", errors="replace")

    return {
        "gps": _read("gps"),
        "stability": _read("stability"),
        "rotativo": _read("rotativo"),
    }


def delete_upload(upload_id: str) -> None:
    """Borra el directorio del upload. Idempotente."""
    folder = _BASE_DIR / upload_id
    if folder.exists():
        shutil.rmtree(folder, ignore_errors=True)
