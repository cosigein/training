"""Almacenamiento temporal del archivo del Doback Elite entre pasos del wizard.

V1: solo se introduce manualmente el archivo de ESTABILIDAD por la UI del
manager. Los datos de GPS y ROTATIVO vendrán de la integración con Webfleet
(no implementada aún) y se inyectarán por otro camino.

El archivo se guarda en `/tmp/training-uploads/<upload_id>/` cuando el
manager lo sube en el paso 1. En el paso 2, lo recuperamos por `upload_id`,
filtramos por sesión elegida y disparamos el pipeline. Después se borra el
directorio.

Si el manager abandona el wizard, los archivos quedan en /tmp y un cron
diario los limpia (TTL implícito del sistema).
"""
import shutil
import uuid
from pathlib import Path
from typing import Optional

_BASE_DIR = Path("/tmp/training-uploads")


class UploadStorageError(Exception):
    pass


def _ensure_base():
    _BASE_DIR.mkdir(parents=True, exist_ok=True)


def create_upload(
    org_id: str,
    attempt_id: str,
    stability_bytes: bytes,
) -> str:
    """Guarda el TXT de estabilidad bajo un upload_id nuevo y devuelve el id."""
    if not stability_bytes:
        raise UploadStorageError("El archivo de ESTABILIDAD es obligatorio.")

    _ensure_base()
    upload_id = uuid.uuid4().hex
    folder = _BASE_DIR / upload_id
    folder.mkdir(parents=True, exist_ok=False)

    # Marker con metadata para validación posterior (org + attempt)
    (folder / "meta.txt").write_text(f"{org_id}\n{attempt_id}\n", encoding="utf-8")
    (folder / "stability.txt").write_bytes(stability_bytes)

    return upload_id


def read_upload(org_id: str, attempt_id: str, upload_id: str) -> dict:
    """Devuelve un dict con el contenido de `stability` (y `gps`/`rotativo` en
    None — reservados para cuando Webfleet inyecte esos datos). Valida que el
    upload pertenece al attempt+org para evitar acceso cruzado."""
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
