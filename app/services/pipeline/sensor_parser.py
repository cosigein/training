"""
Parser para archivos TXT del sensor Doback Elite.

Formato: un único .txt con secciones consecutivas separadas por una línea
de cabecera de sección:

    GPS;DD/MM/YYYY HH:MM:SS;DOBACK023;Sesión:1;
    Timestamp;FechaGPS;HoraGPS;Latitud;Longitud;Altitud;HDOP;Fix;NumSats;Velocidad(km/h)
    <filas de datos...>

    ESTABILIDAD;DD/MM/YYYY HH:MM:SS;DOBACK023;Sesión:1;
    ax; ay; az; gx; gy; gz; roll; pitch; yaw; timeantwifi; usciclo1..5; si; accmag; microsds; k3
    <filas de datos...>

    ROTATIVO;DD/MM/YYYY-HH:MM:SS;DOBACK023;Sesión:1
    Fecha-Hora;Estado
    <filas de datos...>

Conversiones al persistir:
    ax, ay, az : milli-g → m/s²  (× 0.00981)
    gx, gy, gz : grados/s (sin cambio)
    speed GPS  : km/h (sin cambio — el event_detector usa km/h directamente)
"""
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Optional, Tuple

from app.extensions import db
from app.models.session import (
    Attempt,
    GpsMeasurement,
    StabilityMeasurement,
    RotativoMeasurement,
    CanMeasurement,
)

_MG_TO_MS2 = 0.00981
# Sensor de estabilidad: 5 ciclos × ~20 ms c/u → 100 ms por fila
_STAB_ROW_MS = 100
_KNOWN_SECTIONS = {"GPS", "ESTABILIDAD", "ROTATIVO", "CAN"}


# ── Resultado ─────────────────────────────────────────────────────────────────

@dataclass
class ParseResult:
    attempt_id: str
    gps_rows: int = 0
    stability_rows: int = 0
    rotativo_rows: int = 0
    can_rows: int = 0
    gps_skipped_no_fix: int = 0
    errors: List[str] = field(default_factory=list)

    @property
    def total_rows(self):
        return self.gps_rows + self.stability_rows + self.rotativo_rows + self.can_rows

    def summary(self):
        return (
            f"GPS {self.gps_rows} (sin fix: {self.gps_skipped_no_fix}) · "
            f"Estab {self.stability_rows} · "
            f"Rotativo {self.rotativo_rows} · "
            f"CAN {self.can_rows}"
        )


# ── Helpers ───────────────────────────────────────────────────────────────────

def _parse_dt(s: str, fmt: str = "%d/%m/%Y %H:%M:%S") -> Optional[datetime]:
    try:
        return datetime.strptime(s.strip(), fmt)
    except (ValueError, AttributeError):
        return None


def _float(s: str) -> Optional[float]:
    s = s.strip().replace(",", ".")
    if not s:
        return None
    try:
        return float(s)
    except ValueError:
        return None


def _section_dt(header: str) -> Optional[datetime]:
    """Extrae la fecha de la línea de cabecera de sección."""
    parts = header.split(";")
    if len(parts) < 2:
        return None
    raw = parts[1].strip()
    for fmt in ("%d/%m/%Y %H:%M:%S", "%d/%m/%Y-%H:%M:%S"):
        dt = _parse_dt(raw, fmt)
        if dt:
            return dt
    return None


def _is_intermediate_timestamp(line: str) -> bool:
    """True si la línea es un marcador de tiempo intercalado (HH:MM:SS sin fecha)."""
    s = line.strip()
    # Forma típica: "16:48:27" — solo tiene dos ':' y no tiene '/'
    return s.count(":") == 2 and "/" not in s and ";" not in s and len(s) <= 12


def _split_sections(content: str) -> List[Tuple[str, str, List[str]]]:
    """
    Divide el contenido en secciones.
    Retorna lista de (section_type, header_line, [data_lines]).
    """
    sections: List[Tuple[str, str, List[str]]] = []
    current_type: Optional[str] = None
    current_header: str = ""
    current_lines: List[str] = []

    for raw in content.splitlines():
        line = raw.strip()
        if not line:
            continue

        first_token = line.split(";")[0].strip().upper()
        if first_token in _KNOWN_SECTIONS:
            if current_type is not None:
                sections.append((current_type, current_header, current_lines))
            current_type = first_token
            current_header = line
            current_lines = []
        elif current_type is not None:
            current_lines.append(line)

    if current_type is not None:
        sections.append((current_type, current_header, current_lines))

    return sections


# ── Parsers por sección ───────────────────────────────────────────────────────

def _parse_gps(header: str, lines: List[str], attempt_id: str, org_id: str, r: ParseResult):
    """
    Columnas: Timestamp;FechaGPS;HoraGPS;Latitud;Longitud;Altitud;HDOP;Fix;NumSats;Velocidad(km/h)
    Filas sin fix GPS (Latitud/Longitud vacías o 0.0) se descartan.
    """
    for line in lines:
        if _is_intermediate_timestamp(line):
            continue
        parts = [p.strip() for p in line.split(";")]
        if len(parts) < 4:
            continue
        # Saltar cabecera de columnas
        if parts[0].lower() == "timestamp":
            continue

        lat = _float(parts[3]) if len(parts) > 3 else None
        lon = _float(parts[4]) if len(parts) > 4 else None

        if lat is None or lon is None or lat == 0.0 or lon == 0.0:
            r.gps_skipped_no_fix += 1
            continue

        ts = _parse_dt(parts[0])
        if ts is None:
            r.errors.append(f"GPS: timestamp inválido '{parts[0]}'")
            continue

        alt = _float(parts[5]) if len(parts) > 5 else 0.0
        hdop = _float(parts[6]) if len(parts) > 6 else None
        fix = parts[7].strip() if len(parts) > 7 else None
        sats = int(_float(parts[8]) or 0) if len(parts) > 8 else 0
        speed = _float(parts[9]) if len(parts) > 9 else 0.0  # ya en km/h

        db.session.add(GpsMeasurement(
            attemptId=attempt_id,
            organizationId=org_id,
            timestamp=ts,
            latitude=lat,
            longitude=lon,
            altitude=alt or 0.0,
            speed=speed or 0.0,
            satellites=sats,
            quality=fix or "UNKNOWN",
            hdop=hdop,
            fix=fix,
            heading=None,
            accuracy=None,
            confidence=None,
        ))
        r.gps_rows += 1


def _parse_stability(header: str, lines: List[str], attempt_id: str, org_id: str, r: ParseResult):
    """
    Columnas: ax; ay; az; gx; gy; gz; roll; pitch; yaw; timeantwifi; usciclo1..5; si; accmag; microsds; k3
    Las filas no tienen timestamp — se reconstruye como base + row_idx * 100 ms.
    ax/ay/az en milli-g → se convierten a m/s² (* 0.00981).
    """
    base_ts = _section_dt(header) or datetime.utcnow()
    row_idx = 0

    for line in lines:
        if _is_intermediate_timestamp(line):
            continue
        # Saltar cabecera de columnas
        if line.strip().lower().startswith("ax"):
            continue

        parts = [p.strip() for p in line.split(";")]
        if len(parts) < 9:
            continue

        try:
            ax_mg = float(parts[0])
            ay_mg = float(parts[1])
            az_mg = float(parts[2])
            gx = float(parts[3])
            gy = float(parts[4])
            gz = float(parts[5])
            roll = float(parts[6])
            pitch = float(parts[7])
            yaw = float(parts[8])
        except (ValueError, IndexError):
            continue

        si = _float(parts[15]) if len(parts) > 15 else None
        accmag_mg = _float(parts[16]) if len(parts) > 16 else None
        k3 = _float(parts[18]) if len(parts) > 18 else None

        ts = base_ts + timedelta(milliseconds=row_idx * _STAB_ROW_MS)

        db.session.add(StabilityMeasurement(
            attemptId=attempt_id,
            organizationId=org_id,
            timestamp=ts,
            ax=round(ax_mg * _MG_TO_MS2, 5),
            ay=round(ay_mg * _MG_TO_MS2, 5),
            az=round(az_mg * _MG_TO_MS2, 5),
            gx=gx,
            gy=gy,
            gz=gz,
            roll=roll,
            pitch=pitch,
            yaw=yaw,
            si=si,
            accmag=round(accmag_mg * _MG_TO_MS2, 5) if accmag_mg is not None else None,
            confidence=k3,
            isDRSHigh=False,
            isLTRCritical=False,
            isLateralGForceHigh=False,
        ))
        r.stability_rows += 1
        row_idx += 1


def _parse_rotativo(header: str, lines: List[str], attempt_id: str, org_id: str, r: ParseResult):
    """
    Columnas: Fecha-Hora;Estado
    Formato fecha: DD/MM/YYYY-HH:MM:SS
    """
    for line in lines:
        if _is_intermediate_timestamp(line):
            continue
        parts = [p.strip() for p in line.split(";")]
        if len(parts) < 2:
            continue
        if parts[0].lower().startswith("fecha"):
            continue

        ts = _parse_dt(parts[0], "%d/%m/%Y-%H:%M:%S")
        if ts is None:
            continue

        try:
            state = int(float(parts[1]))
        except ValueError:
            continue

        db.session.add(RotativoMeasurement(
            attemptId=attempt_id,
            organizationId=org_id,
            timestamp=ts,
            state=str(state),
            key=state,
        ))
        r.rotativo_rows += 1


# ── Punto de entrada ─────────────────────────────────────────────────────────

def parse_sensor_file(content: str, attempt_id: str, org_id: str) -> ParseResult:
    """
    Parsea el contenido completo de un TXT Doback Elite y persiste las mediciones.

    Idempotente: elimina mediciones previas del attempt antes de insertar.

    Args:
        content:    Contenido del archivo como string (UTF-8).
        attempt_id: ID del Attempt destino.
        org_id:     ID de la organización.

    Returns:
        ParseResult con estadísticas del parsing.

    Raises:
        ValueError: si el attempt no existe o ya está cerrado.
    """
    attempt = Attempt.query.get(attempt_id)
    if not attempt:
        raise ValueError(f"Attempt {attempt_id} no encontrado")
    if attempt.closedAt:
        raise ValueError("Attempt ya cerrado — no se pueden ingresar datos")

    result = ParseResult(attempt_id=attempt_id)

    # Idempotente: borrar mediciones previas
    GpsMeasurement.query.filter_by(attemptId=attempt_id).delete()
    StabilityMeasurement.query.filter_by(attemptId=attempt_id).delete()
    RotativoMeasurement.query.filter_by(attemptId=attempt_id).delete()
    CanMeasurement.query.filter_by(attemptId=attempt_id).delete()

    for section_type, header_line, lines in _split_sections(content):
        if section_type == "GPS":
            _parse_gps(header_line, lines, attempt_id, org_id, result)
        elif section_type == "ESTABILIDAD":
            _parse_stability(header_line, lines, attempt_id, org_id, result)
        elif section_type == "ROTATIVO":
            _parse_rotativo(header_line, lines, attempt_id, org_id, result)
        # CAN: se agrega cuando llegue el formato

    db.session.commit()
    return result
