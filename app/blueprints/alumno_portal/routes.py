from flask import render_template, request, redirect, url_for
from . import alumno_bp
from app.blueprints.manager.routes import (
    CANDIDATOS, CONVOCATORIAS, AUDITORIAS, HISTORIAL_EXTRA,
    _calcular_nota_media, _calcular_ranking
)


def _generar_pedagogico(nota, ruta_label):
    if nota >= 9:
        return {
            "resumen": "Recorrido excelente. El sensor no detectó incidencias significativas.",
            "infracciones": [],
            "sugerencias": ["Mantené esta técnica en los próximos circuitos."],
        }
    elif nota >= 7:
        return {
            "resumen": "Buen recorrido con una incidencia menor que afectó levemente la nota.",
            "infracciones": [
                {
                    "tipo": "Frenada brusca puntual",
                    "cantidad": 1,
                    "zona": f"inicio del circuito {ruta_label}",
                    "familia": "Estabilidad",
                    "puntos": round((10 - nota) * 0.4, 1),
                },
            ],
            "sugerencias": [
                "Anticipá el frenado inicial con al menos 3 segundos de margen.",
                "En general vas muy bien — pulir ese punto puede sumar hasta 0.5 puntos.",
            ],
        }
    elif nota >= 5:
        return {
            "resumen": "Recorrido aprobado con incidencias moderadas. Hay margen de mejora claro.",
            "infracciones": [
                {
                    "tipo": "Frenadas bruscas",
                    "cantidad": 2,
                    "zona": f"tramo principal de {ruta_label}",
                    "familia": "Estabilidad",
                    "puntos": round((10 - nota) * 0.40, 1),
                },
                {
                    "tipo": "Exceso de velocidad puntual",
                    "cantidad": 1,
                    "zona": "tramo recto del recorrido",
                    "familia": "Velocidad",
                    "puntos": round((10 - nota) * 0.25, 1),
                },
            ],
            "sugerencias": [
                "Anticipá los frenados — todavía hay margen de mejora en estabilidad.",
                "Mantené velocidad constante en los tramos rectos.",
                "Revisá las velocidades máximas por zona antes del próximo intento.",
            ],
        }
    else:
        return {
            "resumen": "Recorrido con incidencias significativas que afectaron varias familias de puntuación.",
            "infracciones": [
                {
                    "tipo": "Frenadas bruscas",
                    "cantidad": 4,
                    "zona": f"múltiples puntos en {ruta_label}",
                    "familia": "Estabilidad",
                    "puntos": round((10 - nota) * 0.40, 1),
                },
                {
                    "tipo": "Excesos de velocidad",
                    "cantidad": 2,
                    "zona": "tramos rectos",
                    "familia": "Velocidad",
                    "puntos": round((10 - nota) * 0.25, 1),
                },
                {
                    "tipo": "Desviaciones de trayectoria",
                    "cantidad": 2,
                    "zona": "curvas del circuito",
                    "familia": "Ruta",
                    "puntos": round((10 - nota) * 0.15, 1),
                },
            ],
            "sugerencias": [
                "Trabajá especialmente los frenados progresivos — son el factor más importante.",
                "Anticipá las curvas para reducir velocidad antes de entrar, no durante.",
                "Seguí el GPS sin desviarte — cada desviación suma puntos negativos.",
                "Considerá hacer un repaso en vehículo ligero antes del próximo intento en camión.",
            ],
        }


def _calcular_evolucion(candidato, conv):
    nota_media = _calcular_nota_media(candidato)
    previos_por_ruta = {h['ruta_id']: h for h in HISTORIAL_EXTRA.get(candidato['plaza'], [])}
    evolucion = []

    for ruta in conv['rutas']:
        info = candidato['notas'].get(ruta['id'])
        if not info:
            continue

        previo = previos_por_ruta.get(ruta['id'])
        diff_media = info['nota'] - nota_media

        if previo:
            diff_previo = info['nota'] - previo['nota']
            if diff_previo > 0.3:
                tendencia, icono, color = 'subiendo', 'ph-trend-up', 'verde'
            elif diff_previo < -0.3:
                tendencia, icono, color = 'bajando', 'ph-trend-down', 'rojo'
            else:
                tendencia, icono, color = 'estable', 'ph-minus', 'gris'
            signo = '+' if diff_previo >= 0 else ''
            texto_tendencia = f"{signo}{diff_previo:.1f} vs intento anterior"
        else:
            tendencia, icono, color = 'primer', 'ph-flag', 'azul'
            texto_tendencia = "Primer intento de esta ruta"

        evolucion.append({
            'ruta_id': ruta['id'],
            'label': ruta['label'],
            'nota': info['nota'],
            'tendencia': tendencia,
            'icono': icono,
            'color': color,
            'texto_tendencia': texto_tendencia,
            'nota_previa': previo['nota'] if previo else None,
            'diff_media': round(diff_media, 1),
            'attempt_id': info['attempt_id'],
        })

    mejor = max(evolucion, key=lambda x: x['nota']) if evolucion else None
    peor  = min(evolucion, key=lambda x: x['nota']) if evolucion else None
    return evolucion, mejor, peor


@alumno_bp.route('/intento/<attempt_id>')
def intento(attempt_id):
    candidato = None
    ruta_info = None
    nota_info = None
    conv = None

    for c in CANDIDATOS:
        for ruta_id, info in c['notas'].items():
            if info and info.get('attempt_id') == attempt_id:
                candidato = c
                nota_info = info
                conv = next(
                    (cv for cv in CONVOCATORIAS if cv['id'] == c.get('convocatoria_id')),
                    CONVOCATORIAS[0]
                )
                ruta_info = next((r for r in conv['rutas'] if r['id'] == ruta_id), None)
                break
        if candidato:
            break

    if not candidato:
        return redirect(url_for('alumno.login'))

    auditoria = next((a for a in AUDITORIAS if a['attempt_id'] == attempt_id), None)
    puede_solicitar = auditoria is None
    auditoria_solicitada = request.args.get('auditoria') == 'solicitada'

    score_breakdown = [
        {'familia': 'Estabilidad', 'obtenido': round(nota_info['nota'] * 0.40, 1), 'maximo': 4.0},
        {'familia': 'Velocidad',   'obtenido': round(nota_info['nota'] * 0.30, 1), 'maximo': 3.0},
        {'familia': 'Ruta',        'obtenido': round(nota_info['nota'] * 0.15, 1), 'maximo': 1.5},
        {'familia': 'Conducción',  'obtenido': round(nota_info['nota'] * 0.15, 1), 'maximo': 1.5},
    ]

    pedagogico = _generar_pedagogico(
        nota_info['nota'],
        ruta_info['label'] if ruta_info else 'este circuito'
    )

    return render_template(
        'alumno_portal/intento.html',
        candidato=candidato,
        ruta=ruta_info,
        nota_info=nota_info,
        attempt_id=attempt_id,
        score_breakdown=score_breakdown,
        auditoria=auditoria,
        convocatoria=conv,
        puede_solicitar=puede_solicitar,
        auditoria_solicitada=auditoria_solicitada,
        pedagogico=pedagogico,
        active_page='dashboard',
    )


@alumno_bp.route('/')
def login():
    return render_template('alumno_portal/login.html')


@alumno_bp.route('/entrar', methods=['POST'])
def entrar():
    plaza = request.form.get('plaza', '').strip()
    return redirect(url_for('alumno.dashboard', plaza=plaza))


@alumno_bp.route('/dashboard')
def dashboard():
    plaza = request.args.get('plaza', '')
    candidato = next((c for c in CANDIDATOS if c['plaza'] == plaza), None)

    if not candidato:
        return redirect(url_for('alumno.login'))

    conv = next(
        (cv for cv in CONVOCATORIAS if cv['id'] == candidato.get('convocatoria_id')),
        CONVOCATORIAS[0]
    )

    nota_media = _calcular_nota_media(candidato)
    ranking = _calcular_ranking(conv['plazas'], conv['id'])
    mi_entrada = next((e for e in ranking if e['candidato']['id'] == candidato['id']), None)
    mi_posicion = mi_entrada['puesto'] if mi_entrada else None
    dentro_del_corte = mi_entrada['dentro_del_corte'] if mi_entrada else False

    rutas_data = []
    for circ in conv['rutas']:
        info = candidato['notas'].get(circ['id'])
        aud = None
        if info and info.get('audit'):
            aud = next((a for a in AUDITORIAS if a['attempt_id'] == info.get('attempt_id')), None)
        rutas_data.append({'id': circ['id'], 'label': circ['label'], 'info': info, 'auditoria': aud})

    auditoria_resuelta = next(
        (a for a in AUDITORIAS
         if a['candidato'] == candidato['nombre'] and a.get('status') == 'RESOLVED'),
        None
    )

    return render_template(
        'alumno_portal/dashboard.html',
        candidato=candidato,
        convocatoria=conv,
        rutas=rutas_data,
        nota_media=nota_media,
        mi_posicion=mi_posicion,
        total_candidatos=len([c for c in CANDIDATOS if c.get('convocatoria_id') == conv['id']]),
        plazas=conv['plazas'],
        dentro_del_corte=dentro_del_corte,
        auditoria_resuelta=auditoria_resuelta,
        active_page='dashboard',
    )


@alumno_bp.route('/historial')
def historial():
    plaza = request.args.get('plaza', '')
    candidato = next((c for c in CANDIDATOS if c['plaza'] == plaza), None)

    if not candidato:
        return redirect(url_for('alumno.login'))

    conv = next(
        (cv for cv in CONVOCATORIAS if cv['id'] == candidato.get('convocatoria_id')),
        CONVOCATORIAS[0]
    )

    def _fecha_sort_key(fecha_str):
        try:
            d, m, y = fecha_str.split('/')
            return (y, m, d)
        except Exception:
            return ('0000', '00', '00')

    intentos = []
    for ruta in conv['rutas']:
        info = candidato['notas'].get(ruta['id'])
        if info:
            aud = next((a for a in AUDITORIAS if a['attempt_id'] == info['attempt_id']), None)
            intentos.append({
                'ruta_id': ruta['id'],
                'label': ruta['label'],
                'nota': info['nota'],
                'data_quality': info['data_quality'],
                'attempt_id': info['attempt_id'],
                'fecha': info.get('fecha', ''),
                'hora': info.get('hora', ''),
                'auditoria': aud,
                'es_actual': True,
            })

    for p in HISTORIAL_EXTRA.get(plaza, []):
        intentos.append({
            'ruta_id': p['ruta_id'],
            'label': p['ruta_label'],
            'nota': p['nota'],
            'data_quality': p['data_quality'],
            'attempt_id': p['attempt_id'],
            'fecha': p.get('fecha', ''),
            'hora': p.get('hora', ''),
            'auditoria': None,
            'es_actual': False,
        })

    intentos.sort(key=lambda x: _fecha_sort_key(x['fecha']), reverse=True)

    return render_template(
        'alumno_portal/historial.html',
        candidato=candidato,
        convocatoria=conv,
        intentos=intentos,
        active_page='historial',
    )


@alumno_bp.route('/evolucion')
def evolucion():
    plaza = request.args.get('plaza', '')
    candidato = next((c for c in CANDIDATOS if c['plaza'] == plaza), None)

    if not candidato:
        return redirect(url_for('alumno.login'))

    conv = next(
        (cv for cv in CONVOCATORIAS if cv['id'] == candidato.get('convocatoria_id')),
        CONVOCATORIAS[0]
    )

    nota_media = _calcular_nota_media(candidato)
    evolucion_data, mejor, peor = _calcular_evolucion(candidato, conv)

    return render_template(
        'alumno_portal/evolucion.html',
        candidato=candidato,
        convocatoria=conv,
        evolucion=evolucion_data,
        nota_media=nota_media,
        mejor=mejor,
        peor=peor,
        active_page='evolucion',
    )


@alumno_bp.route('/intento/<attempt_id>/auditoria')
def solicitar_auditoria(attempt_id):
    candidato = None
    nota_info = None
    ruta_info = None
    conv = None

    for c in CANDIDATOS:
        for ruta_id, info in c['notas'].items():
            if info and info.get('attempt_id') == attempt_id:
                candidato = c
                nota_info = info
                conv = next((cv for cv in CONVOCATORIAS if cv['id'] == c.get('convocatoria_id')), CONVOCATORIAS[0])
                ruta_info = next((r for r in conv['rutas'] if r['id'] == ruta_id), None)
                break
        if candidato:
            break

    if not candidato:
        return redirect(url_for('alumno.login'))

    auditoria_existente = next((a for a in AUDITORIAS if a['attempt_id'] == attempt_id), None)
    if auditoria_existente:
        return redirect(url_for('alumno.intento', attempt_id=attempt_id))

    razon = request.args.get('razon', '').strip()
    error = None

    if razon:
        if len(razon) < 30:
            error = f"La razón debe tener al menos 30 caracteres. Llevas {len(razon)}."
        else:
            nueva = {
                "id": f"aud-{len(AUDITORIAS) + 1:03d}",
                "attempt_id": attempt_id,
                "candidato": candidato['nombre'],
                "ruta": ruta_info['label'] if ruta_info else '',
                "nota": nota_info['nota'],
                "fecha_solicitud": "29/04/2026",
                "hora_solicitud": "10:00",
                "razon": razon,
                "status": "PENDING",
            }
            AUDITORIAS.append(nueva)
            nota_info['audit'] = True
            return redirect(url_for('alumno.intento', attempt_id=attempt_id, auditoria='solicitada'))

    return render_template(
        'alumno_portal/solicitar_auditoria.html',
        candidato=candidato,
        ruta=ruta_info,
        nota_info=nota_info,
        attempt_id=attempt_id,
        razon_previa=razon,
        error=error,
        active_page='dashboard',
    )
