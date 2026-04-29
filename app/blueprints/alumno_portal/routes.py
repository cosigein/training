from flask import render_template, request, redirect, url_for
from . import alumno_bp
from app.blueprints.manager.routes import (
    CANDIDATOS, CONVOCATORIAS, AUDITORIAS, _calcular_nota_media, _calcular_ranking
)


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

    score_breakdown = [
        {'familia': 'Estabilidad', 'obtenido': round(nota_info['nota'] * 0.40, 1), 'maximo': 4.0},
        {'familia': 'Velocidad',   'obtenido': round(nota_info['nota'] * 0.30, 1), 'maximo': 3.0},
        {'familia': 'Ruta',        'obtenido': round(nota_info['nota'] * 0.15, 1), 'maximo': 1.5},
        {'familia': 'Conducción',  'obtenido': round(nota_info['nota'] * 0.15, 1), 'maximo': 1.5},
    ]

    return render_template(
        'alumno_portal/intento.html',
        candidato=candidato,
        ruta=ruta_info,
        nota_info=nota_info,
        attempt_id=attempt_id,
        score_breakdown=score_breakdown,
        auditoria=auditoria,
        convocatoria=conv,
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

    # Calcular posición en el ranking
    ranking = _calcular_ranking(conv['plazas'], conv['id'])
    mi_entrada = next((e for e in ranking if e['candidato']['id'] == candidato['id']), None)
    mi_posicion = mi_entrada['puesto'] if mi_entrada else None
    dentro_del_corte = mi_entrada['dentro_del_corte'] if mi_entrada else False

    # Rutas con detalle
    rutas_data = []
    for circ in conv['rutas']:
        info = candidato['notas'].get(circ['id'])
        auditoria = None
        if info and info.get('audit'):
            auditoria = next(
                (a for a in AUDITORIAS if a['attempt_id'] == info.get('attempt_id')),
                None
            )
        rutas_data.append({
            'id': circ['id'],
            'label': circ['label'],
            'info': info,
            'auditoria': auditoria,
        })

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
    )
