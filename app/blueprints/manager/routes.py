from flask import render_template
from . import manager_bp

# ── DATOS MOCK (modelo Paper Maestro v6) ────────────────────────────────────
# Representan el estado de la Convocatoria 2026-A al día de hoy.
# Nota: las notas son 0-10 por intento; el modelo NO emite apto/no_apto
# por intento — solo al cierre de la convocatoria.

CONVOCATORIAS = [
    {
        "id": "conv-26a",
        "nombre": "Convocatoria 2026-A",
        "descripcion": "Conductor de camión · Proceso de oposición pública",
        "status": "OPEN",
        "plazas": 5,
        "total_candidatos": 8,
        "fecha_cierre": "15/06/2026",
        "ultima_actualizacion": "28/04/2026 06:00",
        "auditorias_pendientes": 2,
        "rutas": [
            {"id": "R01", "label": "Salida Cochera"},
            {"id": "R02", "label": "Maniobra T"},
            {"id": "R03", "label": "Paso Angosto"},
            {"id": "R04", "label": "Marcha Atrás"},
            {"id": "R05", "label": "Curva Pronunciada"},
            {"id": "R06", "label": "Emergencia Urbana"},
            {"id": "R07", "label": "Conducción Nocturna"},
            {"id": "R08", "label": "Terreno Irregular"},
        ],
    },
    {
        "id": "conv-26b",
        "nombre": "Convocatoria 2026-B",
        "descripcion": "Conductor de camión · Turno de tarde",
        "status": "OPEN",
        "plazas": 3,
        "total_candidatos": 12,
        "fecha_cierre": "30/06/2026",
        "ultima_actualizacion": "28/04/2026 06:00",
        "auditorias_pendientes": 0,
        "rutas": [
            {"id": "R01", "label": "Salida Cochera"},
            {"id": "R02", "label": "Maniobra T"},
            {"id": "R03", "label": "Paso Angosto"},
            {"id": "R04", "label": "Marcha Atrás"},
        ],
    },
]

# Candidatos con intentos numéricos (nota 0-10 por ruta).
# None = pendiente (no ha completado esa ruta todavía)
# Cada candidato tiene además flags de auditoría por intento.
CANDIDATOS = [
    {
        "id": 1,
        "convocatoria_id": "conv-26a",
        "nombre": "Carlos Rodríguez",
        "plaza": "001",
        "categoria": "C+E",
        "notas": {
            "R01": {"nota": 8.8, "data_quality": "HIGH", "audit": False, "attempt_id": "att-001", "fecha": "25/04/2026", "hora": "09:32"},
            "R02": {"nota": 7.5, "data_quality": "HIGH", "audit": False, "attempt_id": "att-002", "fecha": "26/04/2026", "hora": "10:15"},
            "R03": {"nota": 5.2, "data_quality": "LOW",  "audit": True,  "attempt_id": "att-003", "fecha": "27/04/2026", "hora": "14:22"},
            "R04": {"nota": 8.1, "data_quality": "HIGH", "audit": False, "attempt_id": "att-004", "fecha": "28/04/2026", "hora": "08:45"},
            "R05": {"nota": 7.8, "data_quality": "HIGH", "audit": False, "attempt_id": "att-005", "fecha": "29/04/2026", "hora": "11:05"},
            "R06": None, "R07": None, "R08": None,
        },
        "rutas_completadas": 5,
        "rutas_total": 8,
        "sesiones": 5,
        "ultima": "25/04/2026",
    },
    {
        "id": 2,
        "convocatoria_id": "conv-26a",
        "nombre": "María González",
        "plaza": "002",
        "categoria": "C",
        "notas": {
            "R01": {"nota": 9.2, "data_quality": "HIGH", "audit": False, "attempt_id": "att-010", "fecha": "18/04/2026", "hora": "09:00"},
            "R02": {"nota": 8.7, "data_quality": "HIGH", "audit": False, "attempt_id": "att-011", "fecha": "19/04/2026", "hora": "10:30"},
            "R03": {"nota": 8.9, "data_quality": "HIGH", "audit": False, "attempt_id": "att-012", "fecha": "21/04/2026", "hora": "09:15"},
            "R04": {"nota": 9.0, "data_quality": "HIGH", "audit": False, "attempt_id": "att-013", "fecha": "22/04/2026", "hora": "14:00"},
            "R05": {"nota": 8.5, "data_quality": "HIGH", "audit": False, "attempt_id": "att-014", "fecha": "24/04/2026", "hora": "11:30"},
            "R06": {"nota": 9.1, "data_quality": "HIGH", "audit": False, "attempt_id": "att-015", "fecha": "26/04/2026", "hora": "09:45"},
            "R07": None, "R08": None,
        },
        "rutas_completadas": 6,
        "rutas_total": 8,
        "sesiones": 6,
        "ultima": "26/04/2026",
    },
    {
        "id": 3,
        "convocatoria_id": "conv-26a",
        "nombre": "Javier Martínez",
        "plaza": "003",
        "categoria": "C+E",
        "notas": {
            "R01": {"nota": 7.3, "data_quality": "HIGH",   "audit": False, "attempt_id": "att-020", "fecha": "17/04/2026", "hora": "09:00"},
            "R02": {"nota": 4.8, "data_quality": "MEDIUM", "audit": True,  "attempt_id": "att-021", "fecha": "18/04/2026", "hora": "10:30"},
            "R03": {"nota": 3.9, "data_quality": "LOW",    "audit": False, "attempt_id": "att-022", "fecha": "20/04/2026", "hora": "14:00"},
            "R04": {"nota": 7.1, "data_quality": "HIGH",   "audit": False, "attempt_id": "att-023", "fecha": "22/04/2026", "hora": "09:30"},
            "R05": None, "R06": None, "R07": None, "R08": None,
        },
        "rutas_completadas": 4,
        "rutas_total": 8,
        "sesiones": 4,
        "ultima": "22/04/2026",
    },
    {
        "id": 4,
        "convocatoria_id": "conv-26a",
        "nombre": "Ana López",
        "plaza": "004",
        "categoria": "C",
        "notas": {
            "R01": None, "R02": None, "R03": None, "R04": None,
            "R05": None, "R06": None, "R07": None, "R08": None,
        },
        "rutas_completadas": 0,
        "rutas_total": 8,
        "sesiones": 0,
        "ultima": "—",
    },
    {
        "id": 5,
        "convocatoria_id": "conv-26a",
        "nombre": "Pedro Sánchez",
        "plaza": "005",
        "categoria": "C+E",
        "notas": {
            "R01": {"nota": 9.4, "data_quality": "HIGH", "audit": False, "attempt_id": "att-030", "fecha": "15/04/2026", "hora": "08:30"},
            "R02": {"nota": 9.0, "data_quality": "HIGH", "audit": False, "attempt_id": "att-031", "fecha": "17/04/2026", "hora": "10:00"},
            "R03": {"nota": 8.7, "data_quality": "HIGH", "audit": False, "attempt_id": "att-032", "fecha": "19/04/2026", "hora": "14:15"},
            "R04": {"nota": 9.2, "data_quality": "HIGH", "audit": False, "attempt_id": "att-033", "fecha": "21/04/2026", "hora": "09:30"},
            "R05": {"nota": 8.9, "data_quality": "HIGH", "audit": False, "attempt_id": "att-034", "fecha": "23/04/2026", "hora": "11:00"},
            "R06": {"nota": 9.1, "data_quality": "HIGH", "audit": False, "attempt_id": "att-035", "fecha": "25/04/2026", "hora": "08:45"},
            "R07": {"nota": 8.8, "data_quality": "HIGH", "audit": False, "attempt_id": "att-036", "fecha": "27/04/2026", "hora": "10:30"},
            "R08": None,
        },
        "rutas_completadas": 7,
        "rutas_total": 8,
        "sesiones": 7,
        "ultima": "27/04/2026",
    },
    {
        "id": 6,
        "convocatoria_id": "conv-26a",
        "nombre": "Laura Fernández",
        "plaza": "006",
        "categoria": "C",
        "notas": {
            "R01": {"nota": 7.8, "data_quality": "HIGH", "audit": False, "attempt_id": "att-040", "fecha": "16/04/2026", "hora": "09:15"},
            "R02": {"nota": 8.2, "data_quality": "HIGH", "audit": False, "attempt_id": "att-041", "fecha": "17/04/2026", "hora": "11:00"},
            "R03": {"nota": 7.5, "data_quality": "HIGH", "audit": False, "attempt_id": "att-042", "fecha": "19/04/2026", "hora": "14:30"},
            "R04": {"nota": 4.1, "data_quality": "LOW",  "audit": False, "attempt_id": "att-043", "fecha": "21/04/2026", "hora": "09:45"},
            "R05": {"nota": 7.9, "data_quality": "HIGH", "audit": False, "attempt_id": "att-044", "fecha": "24/04/2026", "hora": "10:30"},
            "R06": None, "R07": None, "R08": None,
        },
        "rutas_completadas": 5,
        "rutas_total": 8,
        "sesiones": 5,
        "ultima": "24/04/2026",
    },
    {
        "id": 7,
        "convocatoria_id": "conv-26a",
        "nombre": "Miguel Torres",
        "plaza": "007",
        "categoria": "C+E",
        "notas": {
            "R01": {"nota": 7.1, "data_quality": "HIGH",   "audit": False, "attempt_id": "att-050", "fecha": "17/04/2026", "hora": "08:30"},
            "R02": {"nota": 6.8, "data_quality": "HIGH",   "audit": False, "attempt_id": "att-051", "fecha": "18/04/2026", "hora": "10:00"},
            "R03": {"nota": 3.5, "data_quality": "LOW",    "audit": False, "attempt_id": "att-052", "fecha": "20/04/2026", "hora": "14:15"},
            "R04": {"nota": 3.2, "data_quality": "LOW",    "audit": False, "attempt_id": "att-053", "fecha": "21/04/2026", "hora": "09:30"},
            "R05": {"nota": 3.0, "data_quality": "MEDIUM", "audit": False, "attempt_id": "att-054", "fecha": "23/04/2026", "hora": "11:00"},
            "R06": None, "R07": None, "R08": None,
        },
        "rutas_completadas": 5,
        "rutas_total": 8,
        "sesiones": 5,
        "ultima": "23/04/2026",
    },
    {
        "id": 8,
        "convocatoria_id": "conv-26a",
        "nombre": "Elena Ruiz",
        "plaza": "008",
        "categoria": "C",
        "notas": {
            "R01": {"nota": 9.6, "data_quality": "HIGH", "audit": False, "attempt_id": "att-060", "fecha": "18/04/2026", "hora": "09:00"},
            "R02": {"nota": 9.3, "data_quality": "HIGH", "audit": False, "attempt_id": "att-061", "fecha": "19/04/2026", "hora": "10:00"},
            "R03": {"nota": 9.1, "data_quality": "HIGH", "audit": False, "attempt_id": "att-062", "fecha": "20/04/2026", "hora": "11:00"},
            "R04": {"nota": 9.5, "data_quality": "HIGH", "audit": False, "attempt_id": "att-063", "fecha": "21/04/2026", "hora": "14:00"},
            "R05": {"nota": 9.4, "data_quality": "HIGH", "audit": False, "attempt_id": "att-064", "fecha": "22/04/2026", "hora": "09:30"},
            "R06": {"nota": 9.2, "data_quality": "HIGH", "audit": False, "attempt_id": "att-065", "fecha": "23/04/2026", "hora": "10:30"},
            "R07": {"nota": 9.0, "data_quality": "HIGH", "audit": False, "attempt_id": "att-066", "fecha": "24/04/2026", "hora": "09:00"},
            "R08": {"nota": 9.3, "data_quality": "HIGH", "audit": False, "attempt_id": "att-067", "fecha": "28/04/2026", "hora": "11:15"},
        },
        "rutas_completadas": 8,
        "rutas_total": 8,
        "sesiones": 8,
        "ultima": "28/04/2026",
    },
    {
        "id": 101,
        "convocatoria_id": "conv-26b",
        "nombre": "Luis Gómez",
        "plaza": "101",
        "categoria": "C",
        "notas": {
            "R01": {"nota": 6.8, "data_quality": "HIGH",   "audit": False, "attempt_id": "att-101", "fecha": "20/04/2026", "hora": "09:00"},
            "R02": {"nota": 7.2, "data_quality": "MEDIUM", "audit": False, "attempt_id": "att-102", "fecha": "22/04/2026", "hora": "10:30"},
            "R03": {"nota": 8.0, "data_quality": "HIGH",   "audit": False, "attempt_id": "att-103", "fecha": "24/04/2026", "hora": "14:00"},
            "R04": {"nota": 5.5, "data_quality": "LOW",    "audit": True,  "attempt_id": "att-104", "fecha": "28/04/2026", "hora": "09:30"},
        },
        "rutas_completadas": 4,
        "rutas_total": 4,
        "sesiones": 4,
        "ultima": "28/04/2026",
    },
    {
        "id": 102,
        "convocatoria_id": "conv-26b",
        "nombre": "Sofia Herrera",
        "plaza": "102",
        "categoria": "C",
        "notas": {
            "R01": {"nota": 9.1, "data_quality": "HIGH", "audit": False, "attempt_id": "att-111", "fecha": "19/04/2026", "hora": "09:00"},
            "R02": {"nota": 8.9, "data_quality": "HIGH", "audit": False, "attempt_id": "att-112", "fecha": "21/04/2026", "hora": "11:00"},
            "R03": {"nota": 9.5, "data_quality": "HIGH", "audit": False, "attempt_id": "att-113", "fecha": "23/04/2026", "hora": "14:00"},
            "R04": {"nota": 9.2, "data_quality": "HIGH", "audit": False, "attempt_id": "att-114", "fecha": "28/04/2026", "hora": "10:15"},
        },
        "rutas_completadas": 4,
        "rutas_total": 4,
        "sesiones": 4,
        "ultima": "28/04/2026",
    },
    {
        "id": 103,
        "convocatoria_id": "conv-26b",
        "nombre": "Diego Navarro",
        "plaza": "103",
        "categoria": "C",
        "notas": {
            "R01": {"nota": 4.5, "data_quality": "HIGH", "audit": False, "attempt_id": "att-121", "fecha": "20/04/2026", "hora": "09:00"},
            "R02": None, "R03": None, "R04": None,
        },
        "rutas_completadas": 1,
        "rutas_total": 4,
        "sesiones": 1,
        "ultima": "20/04/2026",
    },
]

# Auditorías pendientes de resolución por el manager
AUDITORIAS = [
    {
        "id": "aud-001",
        "attempt_id": "att-003",
        "candidato": "Carlos Rodríguez",
        "ruta": "Paso Angosto",
        "nota": 5.2,
        "fecha_solicitud": "26/04/2026",
        "hora_solicitud": "17:45",
        "razon": "Hubo un camión en doble fila que me forzó a detenerme bruscamente sin previo aviso. El sistema detectó frenada brusca pero fue causada por un obstáculo ajeno.",
        "status": "PENDING",
    },
    {
        "id": "aud-002",
        "attempt_id": "att-021",
        "candidato": "Javier Martínez",
        "ruta": "Maniobra T",
        "nota": 4.8,
        "fecha_solicitud": "23/04/2026",
        "hora_solicitud": "09:12",
        "razon": "El sensor del camión falló intermitentemente durante la maniobra. La calidad de datos figura como MEDIUM pero creo que hay lecturas erróneas que influyeron en la nota.",
        "status": "PENDING",
    },
    {
        "id": "aud-003",
        "attempt_id": "att-002",
        "candidato": "Carlos Rodríguez",
        "ruta": "Maniobra T",
        "nota": 7.5,
        "fecha_solicitud": "20/04/2026",
        "hora_solicitud": "14:30",
        "razon": "El sensor registró una frenada pero yo no frené bruscamente. Creo que fue vibración del camión al pasar un badén al inicio de la maniobra.",
        "status": "RESOLVED",
        "resolucion": "CONFIRMED",
        "fecha_resolucion": "22/04/2026",
        "comentario_manager": "Se revisaron los registros del sensor y los datos del Webfleet. Los datos son consistentes con una frenada real. La nota es correcta.",
    },
]

HISTORIAL_EXTRA = {
    "001": [
        {"ruta_id": "R01", "ruta_label": "Salida Cochera", "nota": 6.5, "data_quality": "HIGH",   "fecha": "10/04/2026", "hora": "09:15", "attempt_id": "att-001-a"},
        {"ruta_id": "R02", "ruta_label": "Maniobra T",     "nota": 5.4, "data_quality": "MEDIUM", "fecha": "12/04/2026", "hora": "10:30", "attempt_id": "att-002-a"},
        {"ruta_id": "R03", "ruta_label": "Paso Angosto",   "nota": 4.1, "data_quality": "LOW",    "fecha": "16/04/2026", "hora": "14:45", "attempt_id": "att-003-a"},
    ],
}


def _calcular_nota_media(candidato):
    """Calcula la nota media de las rutas completadas."""
    notas = [v["nota"] for v in candidato["notas"].values() if v is not None]
    if not notas:
        return 0.0
    return sum(notas) / len(notas)


def _tiene_auditoria_pendiente(candidato_id):
    nombre = next((c["nombre"] for c in CANDIDATOS if c["id"] == candidato_id), "")
    return any(a["candidato"] == nombre and a["status"] == "PENDING" for a in AUDITORIAS)


def _calcular_ranking(plazas, conv_id):
    """Ordena candidatos por nota media descendente y calcula posición."""
    entries = []
    candidatos_filtrados = [c for c in CANDIDATOS if c.get("convocatoria_id") == conv_id]
    
    for c in candidatos_filtrados:
        nota_media = _calcular_nota_media(c)
        entries.append({
            "candidato": c,
            "nota_media": nota_media,
            "rutas_completadas": c["rutas_completadas"],
            "rutas_total": c["rutas_total"],
            "tiene_auditoria": _tiene_auditoria_pendiente(c["id"]),
        })

    entries.sort(key=lambda x: x["nota_media"], reverse=True)

    for i, entry in enumerate(entries):
        puesto = i + 1
        entry["puesto"] = puesto
        entry["dentro_del_corte"] = puesto <= plazas

    return entries


# ── RUTAS ──────────────────────────────────────────────────────────────────

@manager_bp.route('/')
def dashboard():
    pendientes_total = sum(
        1 for a in AUDITORIAS if a["status"] == "PENDING"
    )
    return render_template(
        'manager/dashboard.html',
        active_page='dashboard',
        convocatorias=CONVOCATORIAS,
        auditorias=[a for a in AUDITORIAS if a["status"] == "PENDING"],
        pendientes_total=pendientes_total,
    )


@manager_bp.route('/convocatorias')
def convocatorias():
    return render_template(
        'manager/convocatorias.html',
        active_page='convocatorias',
        convocatorias=CONVOCATORIAS,
    )


@manager_bp.route('/matriz')
def matriz():
    from flask import request
    conv_id = request.args.get('conv_id')
    conv = next((c for c in CONVOCATORIAS if c["id"] == conv_id), CONVOCATORIAS[0])
    
    candidatos_filtrados = [c for c in CANDIDATOS if c.get("convocatoria_id") == conv["id"]]
    
    return render_template(
        'manager/matriz.html',
        active_page='matriz',
        candidatos=candidatos_filtrados,
        circuitos=conv["rutas"],
        convocatoria=conv,
        convocatorias=CONVOCATORIAS,
    )


@manager_bp.route('/ranking')
def ranking():
    from flask import request
    conv_id = request.args.get('conv_id')
    conv = next((c for c in CONVOCATORIAS if c["id"] == conv_id), CONVOCATORIAS[0])
    
    plazas = conv["plazas"]
    ranking_entries = _calcular_ranking(plazas, conv["id"])
    nota_corte = None
    if len(ranking_entries) >= plazas:
        nota_corte = ranking_entries[plazas - 1]["nota_media"]
        
    candidatos_filtrados = [c for c in CANDIDATOS if c.get("convocatoria_id") == conv["id"]]
    
    return render_template(
        'manager/ranking.html',
        active_page='ranking',
        ranking=ranking_entries,
        plazas=plazas,
        nota_corte=nota_corte,
        convocatoria=conv,
        convocatorias=CONVOCATORIAS,
        total_candidatos=len(candidatos_filtrados),
    )


@manager_bp.route('/intento/<attempt_id>')
def intento_detalle(attempt_id):
    # Buscar el intento en los datos mock
    candidato = None
    ruta_info = None
    nota_info = None
    conv = None

    for c in CANDIDATOS:
        for ruta_id, info in c["notas"].items():
            if info and info.get("attempt_id") == attempt_id:
                candidato = c
                nota_info = info
                conv = next((cv for cv in CONVOCATORIAS if cv["id"] == c.get("convocatoria_id")), CONVOCATORIAS[0])
                ruta_info = next((r for r in conv["rutas"] if r["id"] == ruta_id), None)
                break
        if candidato:
            break

    if not candidato:
        return "Intento no encontrado", 404

    # Auditoría asociada a este intento (si la hay)
    auditoria = next((a for a in AUDITORIAS if a["attempt_id"] == attempt_id), None)

    # Score breakdown simulado
    score_breakdown = [
        {"familia": "Estabilidad", "obtenido": round(nota_info["nota"] * 0.40, 1), "maximo": 4.0},
        {"familia": "Velocidad",   "obtenido": round(nota_info["nota"] * 0.30, 1), "maximo": 3.0},
        {"familia": "Ruta",        "obtenido": round(nota_info["nota"] * 0.15, 1), "maximo": 1.5},
        {"familia": "Conducción",  "obtenido": round(nota_info["nota"] * 0.15, 1), "maximo": 1.5},
    ]

    # Eventos detectados simulados
    eventos = []
    if nota_info["nota"] < 6:
        eventos = [
            {"tipo": "FRENADA_BRUSCA", "timestamp": "09:34:12", "severidad": 0.85,
             "source": "SENSOR", "confidence": "HIGH",
             "descripcion": "Deceleración de 0.42g en 0.8 segundos"},
            {"tipo": "EXCESO_VELOCIDAD", "timestamp": "09:41:55", "severidad": 0.60,
             "source": "WEBFLEET", "confidence": "HIGH",
             "descripcion": "Velocidad 68 km/h en zona limitada a 50 km/h"},
        ]
    elif nota_info["data_quality"] == "LOW":
        eventos = [
            {"tipo": "ACELERACION_LATERAL", "timestamp": "09:36:22", "severidad": 0.45,
             "source": "SENSOR", "confidence": "LOW",
             "descripcion": "Giro lateral 0.28g — calidad datos baja"},
        ]

    return render_template(
        'manager/intento.html',
        active_page='matriz',
        candidato=candidato,
        ruta=ruta_info,
        nota_info=nota_info,
        attempt_id=attempt_id,
        score_breakdown=score_breakdown,
        eventos=eventos,
        auditoria=auditoria,
        convocatoria=conv,
    )


@manager_bp.route('/auditoria/<audit_id>')
def auditoria_detalle(audit_id):
    auditoria = next((a for a in AUDITORIAS if a["id"] == audit_id), None)
    if not auditoria:
        return "Auditoría no encontrada", 404
    return render_template(
        'manager/auditoria.html',
        active_page='dashboard',
        auditoria=auditoria,
    )


@manager_bp.route('/alumno/<int:candidato_id>')
def alumno_detalle(candidato_id):
    candidato = next((c for c in CANDIDATOS if c["id"] == candidato_id), None)
    if not candidato:
        return "Candidato no encontrado", 404
    
    conv = next((cv for cv in CONVOCATORIAS if cv["id"] == candidato.get("convocatoria_id")), CONVOCATORIAS[0])
    
    # Calcular intentos para mostrar
    intentos = []
    for ruta_id, info in candidato["notas"].items():
        if info:
            ruta_label = next((r["label"] for r in conv["rutas"] if r["id"] == ruta_id), ruta_id)
            intentos.append({
                "ruta_id": ruta_id,
                "ruta_label": ruta_label,
                "nota": info["nota"],
                "data_quality": info["data_quality"],
                "audit": info["audit"],
                "attempt_id": info["attempt_id"]
            })
            
    return render_template(
        'manager/alumno.html',
        active_page='matriz',
        candidato=candidato,
        convocatoria=conv,
        intentos=intentos,
        nota_media=_calcular_nota_media(candidato)
    )
