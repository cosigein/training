"""generate_team_report.py — Informe diario CONSOLIDADO del equipo Training (CMadrid).

Cada día a las 14:00 Madrid (vía launchd), este script:
  1. Lee commits de GitHub del día corriente (vía git log local).
  2. Lee inputs externos del equipo en `~/Desktop/entregables/inputs/<YYYY-MM-DD>/`:
       - joel-slack.md    → mensaje que Antonio copió del Slack canal de Joel
       - jesus.pdf|.md    → entregable que Jesús subió al Drive (Antonio lo baja)
       - alejandro.pdf|.md → idem para Alejandro
  3. Consolida todo en un PDF con tono ejecutivo no técnico.
  4. Output → `~/Desktop/entregables/equipo/equipo-<YYYY-MM-DD>.pdf`

Si tenés Google Drive Desktop sincronizando la carpeta `equipo`, el PDF
se sube solo. Si no, lo arrastrás al Drive vía web una vez por día.

Uso manual:
    python scripts/generate_team_report.py             # día de hoy
    python scripts/generate_team_report.py 2026-04-29  # día concreto

Dependencias: markdown, weasyprint, pdfplumber.
"""
from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
from datetime import datetime, date
from pathlib import Path

import markdown
from weasyprint import HTML, CSS

try:
    import pdfplumber  # opcional pero recomendado
except ImportError:
    pdfplumber = None

# Imports condicionales para Slack/Drive auto-read (degradan a None si fallan)
try:
    from slack_reader import fetch_channel_messages
except ImportError:
    fetch_channel_messages = None

try:
    from drive_client import list_files_in_folder, download_file, upload_file
except ImportError:
    list_files_in_folder = None
    download_file = None
    upload_file = None


# ─── Configuración fija ──────────────────────────────────────────────────────

REPO_PATH = Path("/Users/antoniohermoso/repos/training")
DESKTOP = Path.home() / "Desktop"
INPUTS_ROOT = DESKTOP / "entregables" / "inputs"
OUTPUT_DIR = DESKTOP / "entregables" / "equipo"
LOG_FILE = DESKTOP / "entregables" / "team_report.log"

# Slack + Drive (auto-read si hay credenciales)
SLACK_CHANNEL_ID = "C0AV8A77E9M"  # canal donde Joel publica
DRIVE_TEAM_FOLDER = "1vjwi97QmwcUkzVj2LtPshZmGE5AEoZFD"  # carpeta general donde Jesús/Alejandro suben
DRIVE_EQUIPO_FOLDER = "1hOWpXO6OyKL9yGwRoxztqJW50MfTPA5p"  # carpeta donde se sube el PDF consolidado
ANTONIO_EMAIL = "antoniohermoso92@gmail.com"  # se excluye al listar la carpeta general

# Mapeo email del Drive → "key" usada en inputs_today (jesus / alejandro / joel)
# Verificado en Slack 29/04:
#   - Joel Heikkinen <joelh.heikkinen@gmail.com>
#   - Jesus Rodriguez Casado <burnt@burnt.ovh> (GitHub) / <burnt4023@gmail.com> (Drive)
#   - Alejandro Millán de Lara <i12milaa@uco.es>
#   - Jose Manuel Lopez <jlopez@cosigein.es> es el PM/coordinador, sube cosas POR
#     Jesús/Joel cuando ellos no tienen acceso al Drive. Sus uploads se asignan al
#     dueño según el nombre del archivo (entregable_jesus_*.pdf → Jesús, etc.).
DRIVE_EMAIL_TO_KEY = {
    "burnt@burnt.ovh": "jesus",
    "burnt4023@gmail.com": "jesus",
    "i12milaa@uco.es": "alejandro",
    "joelh.heikkinen@gmail.com": "joel",
}

# Mapeo PROXY: cuando jlopez@cosigein.es sube por otro, deduce el dueño del filename.
# Pattern: "entregable_<nombre>_<fecha>.pdf"
PROXY_UPLOADER_EMAIL = "jlopez@cosigein.es"
PROXY_FILENAME_PATTERN = re.compile(r"entregable[_-]([a-záéíóúñ]+)[_-]", re.I)
PROXY_NAME_TO_KEY = {
    "jesus": "jesus",
    "jesús": "jesus",
    "alejandro": "alejandro",
    "joel": "joel",
}

# Mapeo author email/name → rol humano. Cualquier otro → Joel.
TEAM_MAPPING = {
    "antoniohermoso92@gmail.com": "Antonio Hermoso (Director técnico)",
    "ia@cosigein.es": "Antonio Hermoso (Director técnico)",
    "hermoso92": "Antonio Hermoso (Director técnico)",
    "antonio hermoso gonzález": "Antonio Hermoso (Director técnico)",
    "burnt@burnt.ovh": "Jesús (Backend)",
    "eldur4023": "Jesús (Backend)",
    "i12milaa@uco.es": "Alejandro (Frontend)",
    "alejandro millán de lara": "Alejandro (Frontend)",
}

DIAS = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
MESES = [
    "enero", "febrero", "marzo", "abril", "mayo", "junio",
    "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre",
]


# ─── CSS institucional para el PDF ──────────────────────────────────────────

CSS_INSTITUCIONAL = """
@page {
    size: A4;
    margin: 2.5cm 2cm 2.5cm 2cm;
    @top-right { content: "Training · CMadrid · Informe del equipo"; font-family: sans-serif; font-size: 9pt; color: #64748b; }
    @bottom-center { content: "Página " counter(page) " de " counter(pages); font-family: sans-serif; font-size: 9pt; color: #94a3b8; }
    @bottom-right { content: "Confidencial — Bomberos Comunidad de Madrid"; font-family: sans-serif; font-size: 8pt; color: #94a3b8; }
}
body { font-family: serif; font-size: 11pt; line-height: 1.65; color: #0f172a; text-align: justify; }
h1 { font-family: sans-serif; font-size: 22pt; font-weight: 800; color: #1e3a8a; margin: 0 0 0.2cm 0; letter-spacing: -0.02em; }
h1 + h2 { font-size: 12pt; color: #475569; border: none; margin-top: 0; margin-bottom: 0.5cm; font-weight: 500; padding: 0; }
h2 { font-family: sans-serif; font-size: 14pt; font-weight: 700; color: #1e3a8a; margin-top: 0.8cm; margin-bottom: 0.3cm; border-bottom: 2px solid #1e3a8a; padding-bottom: 0.1cm; }
h3 { font-family: sans-serif; font-size: 12pt; font-weight: 700; color: #0f172a; margin-top: 0.5cm; margin-bottom: 0.15cm; }
p { margin: 0 0 0.4cm 0; }
ul, ol { margin: 0.2cm 0 0.4cm 0; padding-left: 0.6cm; }
li { margin-bottom: 0.15cm; }
strong { font-weight: 700; color: #0f172a; }
hr { border: none; border-top: 1px solid #cbd5e1; margin: 0.5cm 0; }
.fuente { font-style: italic; font-size: 9pt; color: #94a3b8; margin-top: -0.3cm; margin-bottom: 0.4cm; }
"""


# ─── Utilidades ─────────────────────────────────────────────────────────────

def log(msg: str) -> None:
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(line + "\n")


def fecha_humana(d: date) -> str:
    return f"{DIAS[d.weekday()]}, {d.day} de {MESES[d.month - 1]} de {d.year}"


def map_author(name: str, email: str) -> str:
    key_email = (email or "").lower().strip("<>")
    key_name = (name or "").lower().strip()
    for k, v in TEAM_MAPPING.items():
        if k == key_email or k == key_name:
            return v
    # Por defecto, cualquier autor desconocido → Joel
    return "Joel (QA / Simulator / CI)"


def get_commits_for_day(target_day: date) -> dict[str, list[str]]:
    """Devuelve {persona: [mensajes_commit_traducidos]}."""
    if not (REPO_PATH / ".git").is_dir():
        log(f"⚠️  Repo no encontrado en {REPO_PATH} — saltando commits")
        return {}

    # git pull silencioso para tener el último estado
    try:
        subprocess.run(
            ["git", "-C", str(REPO_PATH), "fetch", "--quiet"],
            check=False, timeout=30,
        )
    except Exception as e:
        log(f"⚠️  git fetch falló: {e}")

    since = f"{target_day.isoformat()} 00:00"
    until = f"{target_day.isoformat()} 23:59"
    cmd = [
        "git", "-C", str(REPO_PATH), "log",
        f"--since={since}", f"--until={until}",
        "--all",  # incluye remotos también
        "--pretty=format:%H|%an|%ae|%s",
    ]
    out = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if out.returncode != 0:
        log(f"⚠️  git log falló: {out.stderr}")
        return {}

    by_person: dict[str, list[str]] = {}
    seen_hashes: set[str] = set()
    for line in out.stdout.strip().split("\n"):
        if not line:
            continue
        parts = line.split("|", 3)
        if len(parts) < 4:
            continue
        h, name, email, subject = parts
        if h in seen_hashes:
            continue
        seen_hashes.add(h)
        person = map_author(name, email)
        by_person.setdefault(person, []).append(subject.strip())
    return by_person


def commits_to_executive_paragraph(commits: list[str]) -> str:
    """Toma una lista de mensajes técnicos de commits y devuelve un párrafo no técnico."""
    if not commits:
        return "Sin aportaciones de código registradas hoy."

    # Reglas de traducción simples: reemplazos de jerga técnica común.
    REPLACEMENTS = [
        (r"\bauth/routes\.py\b", "el módulo de autenticación"),
        (r"\bRBAC\b", "sistema de permisos"),
        (r"\bJWT\b", "tokens de sesión"),
        (r"\bCSRF\b", "protección frente a falsificación de solicitudes"),
        (r"\bWebSocket\b", "comunicación en tiempo real"),
        (r"\bbase de datos\b", "base de datos"),
        (r"\bSQLAlchemy\b", "base de datos"),
        (r"\bCelery\b", "tareas en segundo plano"),
        (r"\bRedis\b", "servicio de cache"),
        (r"\bnginx\b", "servidor web"),
        (r"\bsystemd\b", "servicio de arranque automático"),
        (r"\bVPS\b", "servidor de producción"),
        (r"\bPR #\d+\b", ""),
        (r"#\d+", ""),
        (r"\(#\d+\)", ""),
        (r"\brefactor\b", "reorganización"),
        (r"\bmerge conflicts?\b", "integración del trabajo"),
        (r"\bmanager\b", "el portal del manager"),
        (r"\benrollment\b", "inscripción"),
        (r"\bconvocatoria\b", "convocatoria"),
        (r"\bRfid[Cc]ard\b", "tarjeta RFID"),
        (r"\bkiosko\b", "kiosko"),
    ]
    bullets = []
    for c in commits:
        # Quitar prefijos conventional-commits como "feat(be):" o "fix(auth):"
        msg = re.sub(r"^(feat|fix|chore|docs|refactor|test|style|ci)(\(.*?\))?:\s*", "", c, flags=re.I)
        for pat, rep in REPLACEMENTS:
            msg = re.sub(pat, rep, msg, flags=re.I)
        msg = msg.strip()
        if not msg:
            continue
        # Capitalizar primera letra
        msg = msg[0].upper() + msg[1:] if msg else msg
        bullets.append(msg)

    if not bullets:
        return "Sin aportaciones de código registradas hoy."
    return "Trabajos del día:\n\n" + "\n".join(f"- {b}." for b in bullets if b)


def read_external_input(input_dir: Path, basename: str) -> tuple[str, str] | None:
    """Busca un archivo con stem `basename` y extensión .md / .txt / .pdf.
    Devuelve (texto_extraido, nombre_archivo) o None."""
    if not input_dir.is_dir():
        return None
    for ext in (".md", ".txt", ".pdf"):
        candidate = input_dir / f"{basename}{ext}"
        if not candidate.is_file():
            continue
        try:
            if ext in (".md", ".txt"):
                return candidate.read_text(encoding="utf-8"), candidate.name
            elif ext == ".pdf":
                if pdfplumber is None:
                    return f"_(adjunto: {candidate.name} — instalá pdfplumber para extraer texto)_", candidate.name
                texts: list[str] = []
                with pdfplumber.open(candidate) as pdf:
                    for page in pdf.pages:
                        t = page.extract_text() or ""
                        if t.strip():
                            texts.append(t)
                content = "\n\n".join(texts).strip() or f"_(no se pudo extraer texto del PDF {candidate.name})_"
                return content, candidate.name
        except Exception as e:
            log(f"⚠️  fallo leyendo {candidate}: {e}")
            return f"_(error leyendo {candidate.name}: {e})_", candidate.name
    return None


# ─── Generación del informe ─────────────────────────────────────────────────

def build_markdown(target_day: date, by_person: dict[str, list[str]], inputs_today: dict[str, tuple[str, str] | None]) -> str:
    """Combina commits + inputs externos en un Markdown consolidado."""
    md = []
    md.append("# Informe Diario del Equipo")
    md.append(f"## {fecha_humana(target_day)}")
    md.append("")
    md.append("Proyecto: **Training — Sistema de evaluación de conductores de camión bomberos (CMadrid)**")
    md.append("")
    md.append("---")
    md.append("")
    md.append("## Estado del día")
    md.append("")
    md.append(
        "Este informe consolida el avance reportado por cada miembro del equipo durante la jornada. "
        "Las aportaciones provienen del repositorio de código del proyecto y de los entregables individuales "
        "que cada miembro publicó en los canales del equipo."
    )
    md.append("")

    md.append("## Avance por miembro del equipo")
    md.append("")

    # Antonio
    md.append("### Antonio Hermoso (Director técnico)")
    md.append(commits_to_executive_paragraph(by_person.get("Antonio Hermoso (Director técnico)", [])))
    md.append("")

    # Jesús
    md.append("### Jesús (Backend)")
    md.append(commits_to_executive_paragraph(by_person.get("Jesús (Backend)", [])))
    jesus_input = inputs_today.get("jesus")
    if jesus_input:
        text, fname = jesus_input
        md.append("")
        md.append(f"**Aporte directo del responsable** _(fuente: `{fname}`)_:")
        md.append("")
        md.append(text.strip())
    md.append("")

    # Alejandro
    md.append("### Alejandro (Frontend)")
    md.append(commits_to_executive_paragraph(by_person.get("Alejandro (Frontend)", [])))
    alejandro_input = inputs_today.get("alejandro")
    if alejandro_input:
        text, fname = alejandro_input
        md.append("")
        md.append(f"**Aporte directo del responsable** _(fuente: `{fname}`)_:")
        md.append("")
        md.append(text.strip())
    md.append("")

    # Joel
    md.append("### Joel (QA y simulador)")
    md.append(commits_to_executive_paragraph(by_person.get("Joel (QA / Simulator / CI)", [])))
    joel_input = inputs_today.get("joel-slack")
    if joel_input:
        text, fname = joel_input
        md.append("")
        md.append(f"**Resumen reportado por Joel en Slack** _(fuente: `{fname}`)_:")
        md.append("")
        md.append(text.strip())
    md.append("")

    md.append("---")
    md.append("")
    md.append(
        "_Informe generado automáticamente a partir del histórico de cambios del proyecto y de los reportes "
        "individuales recogidos hasta las 14:00. Si algún miembro publicó material después de esa hora, no aparece "
        "reflejado en este informe y se incluirá en el del día siguiente._"
    )

    return "\n".join(md)


def md_to_pdf(md_text: str, output_pdf: Path) -> None:
    body = markdown.markdown(md_text, extensions=["extra", "smarty", "sane_lists"])
    html = f"""<!DOCTYPE html>
<html lang="es"><head><meta charset="UTF-8"><title>Informe Equipo</title></head>
<body>{body}</body></html>"""
    output_pdf.parent.mkdir(parents=True, exist_ok=True)
    HTML(string=html).write_pdf(
        target=str(output_pdf),
        stylesheets=[CSS(string=CSS_INSTITUCIONAL)],
    )


# ─── Main ───────────────────────────────────────────────────────────────────

def main(argv: list[str]) -> int:
    if len(argv) > 1:
        try:
            target = date.fromisoformat(argv[1])
        except ValueError:
            log(f"❌ Fecha inválida: {argv[1]} (formato esperado YYYY-MM-DD)")
            return 1
    else:
        target = date.today()

    log(f"▶️  Generando informe consolidado del equipo para {target.isoformat()}")

    # 1. Commits del repo
    by_person = get_commits_for_day(target)
    total_commits = sum(len(v) for v in by_person.values())
    log(f"   Commits encontrados: {total_commits} en {len(by_person)} personas")

    # 2. Inputs externos
    input_dir = INPUTS_ROOT / target.isoformat()
    inputs_today: dict[str, tuple[str, str] | None] = {
        "jesus": read_external_input(input_dir, "jesus"),
        "alejandro": read_external_input(input_dir, "alejandro"),
        "joel-slack": read_external_input(input_dir, "joel-slack"),
    }

    # 2.b Auto-read de Slack (si hay token configurado)
    if inputs_today["joel-slack"] is None and fetch_channel_messages is not None:
        slack_text = fetch_channel_messages(SLACK_CHANNEL_ID, target)
        if slack_text:
            inputs_today["joel-slack"] = (slack_text, f"slack:{SLACK_CHANNEL_ID}")
            log(f"   ✓ Slack: {len(slack_text.splitlines())} líneas leídas del canal {SLACK_CHANNEL_ID}")
        elif slack_text == "":
            log(f"   Slack: canal {SLACK_CHANNEL_ID} sin mensajes hoy")
        else:
            log(f"   Slack: lectura no disponible (sin token o error)")

    # 2.c Auto-read del Drive carpeta general (archivos del día subidos por otros)
    if list_files_in_folder is not None:
        drive_files = list_files_in_folder(DRIVE_TEAM_FOLDER, target, exclude_owner_email=ANTONIO_EMAIL)
        for f in drive_files:
            owner_email = f["owner_email"].lower()
            key = DRIVE_EMAIL_TO_KEY.get(owner_email)

            # Si quien subió es el coordinador (PM proxy), deducir dueño desde filename
            if not key and owner_email == PROXY_UPLOADER_EMAIL:
                m = PROXY_FILENAME_PATTERN.search(f["title"].lower())
                if m:
                    key = PROXY_NAME_TO_KEY.get(m.group(1).lower())

            if not key or inputs_today.get(key) is not None:
                continue  # no mapeado o ya tenemos input local para esa persona

            tmp_path = INPUTS_ROOT / target.isoformat() / f"{key}-from-drive.{('pdf' if f['mimeType'] == 'application/pdf' else 'md')}"
            tmp_path.parent.mkdir(parents=True, exist_ok=True)
            if download_file(f["id"], tmp_path, f["mimeType"]):
                payload = read_external_input(tmp_path.parent, tmp_path.stem)
                if payload:
                    inputs_today[key] = payload
                    log(f"   ✓ Drive: descargado {f['title']} de {f['owner_name']} → {key}")

    found = [k for k, v in inputs_today.items() if v is not None]
    log(f"   Inputs totales para hoy: {found if found else 'ninguno'}")

    # 3. Construir markdown
    md_text = build_markdown(target, by_person, inputs_today)
    md_path = OUTPUT_DIR / f"equipo-{target.isoformat()}.md"
    md_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.write_text(md_text, encoding="utf-8")
    log(f"   Markdown: {md_path}")

    # 4. Convertir a PDF
    pdf_path = OUTPUT_DIR / f"equipo-{target.isoformat()}.pdf"
    md_to_pdf(md_text, pdf_path)
    log(f"   PDF:      {pdf_path} ({pdf_path.stat().st_size // 1024} KB)")

    # 5. Auto-upload al Drive carpeta `equipo` (si hay credenciales)
    if upload_file is not None:
        uploaded_id = upload_file(pdf_path, DRIVE_EQUIPO_FOLDER, title=pdf_path.stem, mime_type="application/pdf")
        if uploaded_id:
            log(f"   ✓ Drive: PDF subido a carpeta `equipo` (id={uploaded_id})")
        else:
            log(f"   Drive: upload no disponible (sin credenciales). Sincronizá manualmente.")
    else:
        log(f"   (drive_client no disponible — sin auto-upload)")

    log(f"✅ Informe generado en {pdf_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
