"""Generador de PDF de entregables diarios para CMadrid.

Convierte un archivo Markdown a un PDF con estilo institucional usando WeasyPrint
(el mismo engine que se usará para el acta de cierre de convocatoria, así que
ganamos consistencia visual entre informes diarios y documentos legales).

Uso:
    python scripts/generate_entregable_pdf.py <input.md> <output.pdf>

Ejemplo:
    python scripts/generate_entregable_pdf.py \
        ~/Desktop/entregables/entregable-2026-04-29.md \
        ~/Desktop/entregables/entregable-2026-04-29.pdf
"""
import sys
from pathlib import Path

import markdown
from weasyprint import HTML, CSS


CSS_INSTITUCIONAL = """
@page {
    size: A4;
    margin: 2.5cm 2cm 2.5cm 2cm;

    @top-right {
        content: "Training · CMadrid";
        font-family: sans-serif;
        font-size: 9pt;
        color: #64748b;
    }

    @bottom-center {
        content: "Página " counter(page) " de " counter(pages);
        font-family: sans-serif;
        font-size: 9pt;
        color: #94a3b8;
    }

    @bottom-right {
        content: "Confidencial — Bomberos Comunidad de Madrid";
        font-family: sans-serif;
        font-size: 8pt;
        color: #94a3b8;
    }
}

body {
    font-family: serif;
    font-size: 11pt;
    line-height: 1.65;
    color: #0f172a;
    text-align: justify;
}

h1 {
    font-family: sans-serif;
    font-size: 22pt;
    font-weight: 800;
    color: #1e3a8a;
    margin: 0 0 0.2cm 0;
    letter-spacing: -0.02em;
}

h2 {
    font-family: sans-serif;
    font-size: 14pt;
    font-weight: 700;
    color: #1e3a8a;
    margin-top: 0.8cm;
    margin-bottom: 0.3cm;
    border-bottom: 2px solid #1e3a8a;
    padding-bottom: 0.1cm;
}

/* Subtítulo bajo h1 (la línea con la fecha) */
h1 + h2 {
    font-size: 12pt;
    color: #475569;
    border: none;
    margin-top: 0;
    margin-bottom: 0.5cm;
    font-weight: 500;
    padding: 0;
}

h3 {
    font-family: sans-serif;
    font-size: 12pt;
    font-weight: 700;
    color: #0f172a;
    margin-top: 0.5cm;
    margin-bottom: 0.15cm;
}

p {
    margin: 0 0 0.4cm 0;
}

ul, ol {
    margin: 0.2cm 0 0.4cm 0;
    padding-left: 0.6cm;
}

li {
    margin-bottom: 0.15cm;
}

strong {
    font-weight: 700;
    color: #0f172a;
}

hr {
    border: none;
    border-top: 1px solid #cbd5e1;
    margin: 0.5cm 0;
}

/* Cabecera del documento */
.doc-header {
    border-bottom: 3px solid #1e3a8a;
    padding-bottom: 0.4cm;
    margin-bottom: 0.6cm;
}

.doc-meta {
    font-family: sans-serif;
    font-size: 10pt;
    color: #64748b;
    margin-top: 0.2cm;
}

/* Apartado "Para mañana" más visible */
h2:last-of-type {
    page-break-before: avoid;
}
"""


def md_to_pdf(md_path: Path, pdf_path: Path) -> None:
    md_text = md_path.read_text(encoding="utf-8")

    # Convertir Markdown a HTML
    html_body = markdown.markdown(
        md_text,
        extensions=["extra", "smarty", "sane_lists"],
    )

    html_doc = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>Informe Diario — Training (CMadrid)</title>
</head>
<body>
{html_body}
</body>
</html>"""

    HTML(string=html_doc).write_pdf(
        target=str(pdf_path),
        stylesheets=[CSS(string=CSS_INSTITUCIONAL)],
    )
    print(f"✅ PDF generado: {pdf_path} ({pdf_path.stat().st_size // 1024} KB)")


def main() -> int:
    if len(sys.argv) != 3:
        print(__doc__, file=sys.stderr)
        return 1

    md_path = Path(sys.argv[1]).expanduser().resolve()
    pdf_path = Path(sys.argv[2]).expanduser().resolve()

    if not md_path.is_file():
        print(f"❌ Markdown no encontrado: {md_path}", file=sys.stderr)
        return 2

    pdf_path.parent.mkdir(parents=True, exist_ok=True)
    md_to_pdf(md_path, pdf_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
