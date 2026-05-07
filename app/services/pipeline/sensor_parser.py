"""
Parser para archivos TXT del sensor Doback Elite.

Tres archivos físicos separados:

    GPS-DOBACK023-2025-09-30.txt
        GPS;DD/MM/YYYY-HH:MM:SS;DOBACK023;Sesión:N
        HoraRaspberry,Fecha,Hora(GPS),Latitud,Longitud,Altitud,HDOP,Fix,NumSats,Velocidad(km/h)
        <filas...>

    ESTABILIDAD-DOBACK023-2025-09-30.txt
        ESTABILIDAD;DD/MM/YYYY HH:MM:SS;DOBACK023;Sesión:N;
        ax; ay; az; gx; gy; gz; roll; pitch; yaw; timeantwifi; usciclo1..5; si; accmag; microsds; k3
        <filas...>

    ROTATIVO-DOBACK023-2025-09-30.txt
        ROTATIVO;DD/MM/YYYY-HH:MM:SS;DOBACK023;Sesión:N
        Fecha-Hora;Estado
        <filas...>

Cada archivo puede contener MÚLTIPLES sesiones (Sesión:1, Sesión:2, ...) — un día
entero de actividad del Doback acumulado. Cada sesión = ruta de un alumno
distinto. El manager debe elegir explícitamente qué sesión asociar al Attempt.

Conversiones al persistir:
    ax, ay, az : milli-g → m/s²  (× 0.00981)
    gx, gy, gz : grados/s (sin cambio)
    speed GPS  : km/h (sin cambio — el event_detector usa km/h directamente)
"""
import math
import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

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
_SESSION_RE = re.compile(r"Sesi[oó]n\s*:\s*(\d+)", re.IGNORECASE)

# ── GPS validation ──────────────────────────────────────────────────────────
# Bounding box que cubre España peninsular + Baleares + Canarias.
_GPS_LAT_MIN, _GPS_LAT_MAX = 27.5, 44.0
_GPS_LON_MIN, _GPS_LON_MAX = -18.5, 4.5
# HDOP mayor a esto = GPS muy contaminado, descartar.
_GPS_HDOP_MAX = 5.0
# Velocidad implícita máxima entre dos puntos consecutivos válidos. Si supera
# esto, asumimos que el segundo punto es un salto erróneo y lo descartamos.
_GPS_MAX_IMPLICIT_KMH = 180.0


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2
         + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2)
    return 2 * r * math.asin(math.sqrt(a))


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


@dataclass
class SessionMeta:
    """Metadata de una sesión presente en al menos uno de los 3 archivos."""
    number: int
    timestamp: Optional[datetime] = None     # primer timestamp del header
    gps_rows: int = 0
    stability_rows: int = 0
    rotativo_rows: int = 0

    def label(self) -> str:
        ts = self.timestamp.strftime("%d/%m/%Y %H:%M") if self.timestamp else "—"
        return f"Sesión {self.number} · {ts} · estab {self.stability_rows} / gps {self.gps_rows} / rot {self.rotativo_rows}"


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


def _section_session(header: str) -> Optional[int]:
    """Extrae el número de sesión de la línea de cabecera de sección."""
    m = _SESSION_RE.search(header)
    if m:
        try:
            return int(m.group(1))
        except ValueError:
            return None
    return None


def _is_intermediate_timestamp(line: str) -> bool:
    """True si la línea es un marcador de tiempo intercalado (HH:MM:SS sin fecha)."""
    s = line.strip()
    return s.count(":") == 2 and "/" not in s and ";" not in s and len(s) <= 12


def _split_sections(content: str, expected_type: Optional[str] = None) -> List[Tuple[str, str, List[str]]]:
    """
    Divide el contenido en bloques (uno por sesión).
    Retorna lista de (section_type, header_line, [data_lines]).
    Si expected_type está dado, ignora bloques de otros tipos (defensa contra
    archivos mezclados).
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

    if expected_type:
        sections = [s for s in sections if s[0] == expected_type]
    return sections


# ── Preview de sesiones ───────────────────────────────────────────────────────

def extract_sessions(
    gps_content: Optional[str] = None,
    stability_content: Optional[str] = None,
    rotativo_content: Optional[str] = None,
) -> List[SessionMeta]:
    """
    Recorre los 3 archivos sin persistir y devuelve la lista de sesiones
    presentes con conteo aproximado de filas de cada tipo. Útil para que el
    manager elija qué sesión asociar al Attempt.
    """
    sessions: Dict[int, SessionMeta] = {}

    def _ensure(num: int, ts: Optional[datetime]) -> SessionMeta:
        if num not in sessions:
            sessions[num] = SessionMeta(number=num, timestamp=ts)
        elif ts and (sessions[num].timestamp is None or ts < sessions[num].timestamp):
            sessions[num].timestamp = ts
        return sessions[num]

    if gps_content:
        for _, header, lines in _split_sections(gps_content, expected_type="GPS"):
            num = _section_session(header)
            if num is None:
                continue
            sm = _ensure(num, _section_dt(header))
            sm.gps_rows += sum(
                1 for ln in lines
                if not _is_intermediate_timestamp(ln)
                and not ln.strip().lower().startswith(("timestamp", "horaraspberry", "hora raspberry", "fecha"))
                and "sin datos gps" not in ln.lower()
            )

    if stability_content:
        for _, header, lines in _split_sections(stability_content, expected_type="ESTABILIDAD"):
            num = _section_session(header)
            if num is None:
                continue
            sm = _ensure(num, _section_dt(header))
            sm.stability_rows += sum(
                1 for ln in lines
                if not _is_intermediate_timestamp(ln) and not ln.strip().lower().startswith("ax")
            )

    if rotativo_content:
        for _, header, lines in _split_sections(rotativo_content, expected_type="ROTATIVO"):
            num = _section_session(header)
            if num is None:
                continue
            sm = _ensure(num, _section_dt(header))
            sm.rotativo_rows += sum(
                1 for ln in lines
                if not _is_intermediate_timestamp(ln) and not ln.strip().lower().startswith("fecha")
            )

    return sorted(sessions.values(), key=lambda s: s.number)


# ── Parsers por sección ───────────────────────────────────────────────────────

def _parse_gps(header: str, lines: List[str], attempt_id: str, org_id: str, r: ParseResult):
    """
    Columnas: Timestamp;FechaGPS;HoraGPS;Latitud;Longitud;Altitud;HDOP;Fix;NumSats;Velocidad(km/h)
    Variantes: separador puede ser ',' o ';'. Filas sin fix se descartan.

    Validaciones de outlier (en orden):
      1. Lat/lon dentro del bounding box de España.
      2. HDOP <= 5 (filtra puntos con GPS muy contaminado).
      3. Velocidad implícita respecto al último punto válido <= 180 km/h.
    Las filas descartadas se cuentan en `gps_skipped_no_fix` y la razón concreta
    se anota en `errors[]` (limitado a las 20 primeras para no inundar).
    """
    last_valid_ts: Optional[datetime] = None
    last_valid_lat: Optional[float] = None
    last_valid_lon: Optional[float] = None

    def _note(reason: str):
        if len(r.errors) < 20:
            r.errors.append(reason)

    for line in lines:
        if _is_intermediate_timestamp(line):
            continue
        # Detectar separador (CSV usa ',' moderno, viejo formato usa ';')
        sep = "," if line.count(",") >= 4 else ";"
        parts = [p.strip() for p in line.split(sep)]
        if len(parts) < 4:
            continue
        first_lower = parts[0].lower()
        if (first_lower.startswith(("timestamp", "horaraspberry", "hora raspberry", "fecha"))
                or "sin datos gps" in line.lower()):
            r.gps_skipped_no_fix += 1
            continue

        lat = _float(parts[3]) if len(parts) > 3 else None
        lon = _float(parts[4]) if len(parts) > 4 else None

        if lat is None or lon is None or lat == 0.0 or lon == 0.0:
            r.gps_skipped_no_fix += 1
            continue
        # Filtrar valores corruptos por rango global
        if not (-90.0 <= lat <= 90.0) or not (-180.0 <= lon <= 180.0):
            r.gps_skipped_no_fix += 1
            _note(f"GPS: lat/lon fuera de rango global ({lat}, {lon})")
            continue
        # Bounding box España
        if not (_GPS_LAT_MIN <= lat <= _GPS_LAT_MAX) or not (_GPS_LON_MIN <= lon <= _GPS_LON_MAX):
            r.gps_skipped_no_fix += 1
            _note(f"GPS: punto fuera de España ({lat:.4f}, {lon:.4f})")
            continue

        # Timestamp: en formato CSV nuevo viene como "HH:MM:SS" (col 0) + fecha "DD/MM/YYYY" (col 1)
        ts = None
        if "/" in parts[0]:
            ts = _parse_dt(parts[0])  # formato viejo "DD/MM/YYYY HH:MM:SS"
        else:
            # nuevo formato: col0=hora_raspberry, col1=fecha, col2=hora_gps
            if len(parts) > 2 and "/" in parts[1]:
                hora = parts[2] if ":" in parts[2] and parts[2].count(":") == 2 else parts[0]
                ts = _parse_dt(f"{parts[1]} {hora}")

        if ts is None:
            r.errors.append(f"GPS: timestamp inválido '{parts[0]}'")
            continue

        alt = _float(parts[5]) if len(parts) > 5 else 0.0
        hdop = _float(parts[6]) if len(parts) > 6 else None
        fix = parts[7].strip() if len(parts) > 7 else None
        sats = int(_float(parts[8]) or 0) if len(parts) > 8 else 0
        speed = _float(parts[9]) if len(parts) > 9 else 0.0  # ya en km/h

        # Filtro de calidad: HDOP alto = GPS contaminado
        if hdop is not None and hdop > _GPS_HDOP_MAX:
            r.gps_skipped_no_fix += 1
            _note(f"GPS: HDOP {hdop} > {_GPS_HDOP_MAX} a las {ts.strftime('%H:%M:%S')}")
            continue

        # Filtro de velocidad implícita respecto al último punto válido
        if last_valid_ts is not None:
            dt_s = (ts - last_valid_ts).total_seconds()
            if dt_s > 0:
                dist_km = _haversine_km(last_valid_lat, last_valid_lon, lat, lon)
                implicit_kmh = (dist_km / dt_s) * 3600.0
                if implicit_kmh > _GPS_MAX_IMPLICIT_KMH:
                    r.gps_skipped_no_fix += 1
                    _note(
                        f"GPS: salto imposible {implicit_kmh:.0f} km/h a las {ts.strftime('%H:%M:%S')}"
                    )
                    continue

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
        last_valid_ts = ts
        last_valid_lat = lat
        last_valid_lon = lon


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

def parse_sensor_files(
    attempt_id: str,
    org_id: str,
    session_number: int,
    gps_content: str,
    stability_content: str,
    rotativo_content: str,
) -> ParseResult:
    """
    Parsea los 3 archivos del sensor Doback Elite filtrando solo los bloques
    cuya cabecera contiene `Sesión:{session_number}`. Persiste las mediciones
    en el Attempt indicado. Los tres archivos son obligatorios.

    Idempotente: elimina mediciones previas del attempt antes de insertar.

    Args:
        attempt_id:        ID del Attempt destino.
        org_id:            ID de la organización.
        session_number:    número de sesión a importar.
        gps_content:       contenido del TXT de GPS.
        stability_content: contenido del TXT de ESTABILIDAD.
        rotativo_content:  contenido del TXT de ROTATIVO.

    Returns:
        ParseResult con estadísticas del parsing.

    Raises:
        ValueError: si el attempt no existe, ya está cerrado, o no se
                    encontró la sesión solicitada en ningún archivo.
    """
    attempt = Attempt.query.get(attempt_id)
    if not attempt:
        raise ValueError(f"Attempt {attempt_id} no encontrado")
    if attempt.closedAt:
        raise ValueError("Attempt ya cerrado — no se pueden ingresar datos")
    if not gps_content or not stability_content or not rotativo_content:
        raise ValueError("Se requieren los 3 archivos: GPS, ESTABILIDAD y ROTATIVO")

    result = ParseResult(attempt_id=attempt_id)

    # Idempotente: borrar mediciones previas
    GpsMeasurement.query.filter_by(attemptId=attempt_id).delete()
    StabilityMeasurement.query.filter_by(attemptId=attempt_id).delete()
    RotativoMeasurement.query.filter_by(attemptId=attempt_id).delete()
    CanMeasurement.query.filter_by(attemptId=attempt_id).delete()

    matched_any = False

    def _process(content: str, expected_type: str, parser_fn):
        nonlocal matched_any
        for sec_type, header, lines in _split_sections(content, expected_type=expected_type):
            if _section_session(header) != session_number:
                continue
            matched_any = True
            parser_fn(header, lines, attempt_id, org_id, result)

    if stability_content:
        _process(stability_content, "ESTABILIDAD", _parse_stability)
    if gps_content:
        _process(gps_content, "GPS", _parse_gps)
    if rotativo_content:
        _process(rotativo_content, "ROTATIVO", _parse_rotativo)

    if not matched_any:
        db.session.rollback()
        raise ValueError(
            f"No se encontró ninguna 'Sesión:{session_number}' en los archivos provistos."
        )

    db.session.commit()
    return result


# ── Compat: punto de entrada legacy (1 archivo concatenado, sin filtro) ──────

def parse_sensor_file(content: str, attempt_id: str, org_id: str) -> ParseResult:
    """Compat: parser viejo que recibe UN archivo con todas las secciones.
    Se mantiene para tests/scripts que lo usen. NO filtra por sesión."""
    attempt = Attempt.query.get(attempt_id)
    if not attempt:
        raise ValueError(f"Attempt {attempt_id} no encontrado")
    if attempt.closedAt:
        raise ValueError("Attempt ya cerrado — no se pueden ingresar datos")

    result = ParseResult(attempt_id=attempt_id)

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

    db.session.commit()
    return result
