# Training
## Sistema de evaluación competitiva para conductores de camión de bomberos

### Propuesta para CMadrid · Cuerpo de Bomberos de la Comunidad de Madrid

---

| | |
|---|---|
| **Documento** | Propuesta comercial |
| **Cliente** | CMadrid · Cuerpo de Bomberos de la Comunidad de Madrid |
| **Versión** | 1.0 — abril de 2026 |
| **Demo en vivo** | Lunes 11 de mayo de 2026 |

---

## Resumen ejecutivo

Training es un sistema de **evaluación automática y competitiva** de candidatos a conductor de camión de bomberos. Diseñado específicamente para procesos de oposición pública española.

**Lo que entrega:**

- Evaluación **objetiva, trazable y reproducible** de cada candidato.
- **Ranking acumulado** publicado diariamente, con visibilidad controlada.
- **Acta firmada** legalmente válida al cierre de cada convocatoria.
- **Procesamiento autónomo de la captura y cálculo**: el sistema mide, normaliza y calcula la nota de cada intento sin intervención humana en el camino.
- **Compliance GDPR** desde el día uno.

**Lo que no es:**

- No es un examen escolar. Es una **oposición**: hay plazas fijas, los candidatos compiten entre sí.
- No reemplaza al instructor. **Le da información objetiva** para apoyar el proceso.
- No es una caja negra. Cada decisión es **explicable** y queda como evidencia.

```
   ┌──────────────────────────────────────────────────────┐
   │                                                      │
   │   Evaluamos sin sesgo subjetivo.                     │
   │   Clasificamos sin discusión.                        │
   │   Documentamos para auditoría.                       │
   │                                                      │
   │   Y lo hacemos automáticamente.                      │
   │                                                      │
   └──────────────────────────────────────────────────────┘
```

---

## 1. El reto de CMadrid

Evaluar a 265 candidatos en cada convocatoria de conductor de camión es **caro, lento y subjetivo** cuando se hace exclusivamente con observación humana. Los riesgos son conocidos:

- **Inconsistencia entre instructores**: cada uno tiene su criterio.
- **Difícil trazabilidad**: cuando un candidato impugna, no hay registro objetivo.
- **Cuello de botella**: el equipo evaluador no escala bien con cohortes grandes.
- **Riesgo legal**: en oposición pública, una evaluación impugnada que carezca de evidencia objetiva puede invalidar el proceso entero.

---

## 2. Cómo Training resuelve estos retos

```
        ┌──────────────────────────────────────────┐
        │                                          │
        │   1. El candidato conduce una ruta real  │
        │                                          │
        │              ↓                           │
        │                                          │
        │   2. Dos sistemas miden lo que pasó      │
        │      (sensor del camión + GPS externo)   │
        │                                          │
        │              ↓                           │
        │                                          │
        │   3. El sistema calcula AUTOMÁTICAMENTE  │
        │      una nota objetiva y la incorpora    │
        │      al ranking de la convocatoria       │
        │                                          │
        │              ↓                           │
        │                                          │
        │   4. Al cierre, los X primeros           │
        │      del ranking obtienen plaza          │
        │                                          │
        └──────────────────────────────────────────┘
```

**Lo que cambia respecto a la evaluación tradicional:**

| Antes | Con Training |
|---|---|
| Criterio variable por instructor | Criterio único, configurado por CMadrid |
| Evaluación lenta, secuencial | Procesamiento automático y paralelo |
| Sin evidencia objetiva | Cada penalización con datos y trazabilidad |
| Difícil resolver impugnaciones | Cada decisión auditable, exportable a la comisión |
| Sin ranking en tiempo real | Ranking publicado diariamente |
| Resultado = decisión humana | Resultado = automático, según reglas que vosotros definís |

---

## 3. Lo que Training entrega a CMadrid

### 3.1 Cuatro portales operativos

```
   ALUMNO                 — Consulta su nota, su puesto, sus errores explicados
                            en lenguaje pedagógico. Puede solicitar auditoría.

   RESPONSABLE/INSTRUCTOR — Ve el ranking, la matriz alumno × ruta,
                            el detalle de cada intento. Solo lectura.
                            Resuelve auditorías cuando los alumnos las solicitan.

   ADMINISTRADOR          — Configura rutas, tarjetas RFID, kioskos,
                            reglas de scoring. Cierra convocatorias.

   CABINA DEL CAMIÓN      — Pantalla simple en cada vehículo. RFID + modo
                            oscuro + sin distracciones. NO muestra notas
                            durante la conducción.
```

### 3.2 Cuatro garantías que tu instructor pedirá

```
   ✓ TRAZABILIDAD
     Cada penalización registra: qué umbral se superó, en qué momento,
     con qué evidencia. Si un candidato impugna, vosotros tenéis los datos.

   ✓ INMUTABILIDAD
     Una nota emitida no se modifica nunca. Las correcciones se hacen
     creando un nuevo intento que queda vinculado al original.

   ✓ REPRODUCIBILIDAD
     Cualquier intento cerrado se puede reproducir desde sus datos crudos.
     Si en seis meses la comisión necesita revisarlo, está disponible.

   ✓ VERSIONADO INMUTABLE DE REGLAS
     Cuando cambian las reglas, los intentos viejos NO se reprocesan.
     Cada candidato fue evaluado con las reglas vigentes en su momento.
```

### 3.3 La pieza más importante: el simulador

Antes de aplicar un cambio en las reglas de evaluación, podéis **simularlo** sobre una convocatoria real:

```
   "¿Qué pasaría si subo el umbral de exceso de velocidad de 10 a 15 km/h?"

   El simulador te dice:
   - 87 intentos cambian de nota
   - 5 candidatos entran al ranking de plazas
   - 5 candidatos salen del ranking de plazas
   - Diferencia media de nota: +0.45 puntos

   Y NADA en producción cambia hasta que vosotros confirmáis.
```

Esto es nuevo y tiene un valor real para CMadrid: **probar políticas de evaluación sin riesgo antes de aplicarlas**.

---

## 4. El proceso, paso por paso

### Paso 1 — El candidato se identifica

Sube al camión, pasa su tarjeta RFID por el lector de la cabina. El sistema reconoce quién es. Selecciona la ruta a evaluar.

> **Es el único momento de interacción humana operativa.** Todo lo demás es automático.

### Paso 2 — Conducción

Mientras conduce, dos sistemas registran información en paralelo:

- **Doback Elite**, dispositivo propio instalado en cada camión: aceleraciones, frenadas, giros, GPS propio.
- **Webfleet** (la plataforma de gestión de flotas que CMadrid ya tiene contratada con Bridgestone): GPS, velocidad, eventos de comportamiento.

> Si Webfleet falla, **Doback Elite cubre con su GPS de respaldo**. El sistema sigue funcionando.

### Paso 3 — Procesamiento automático

Al terminar la ruta, el sistema:

- Limpia los datos.
- Detecta eventos relevantes (frenadas bruscas, excesos, desviaciones).
- Calcula una nota entre 0 y 10 según las reglas que CMadrid configuró.
- Genera la explicación detallada de cómo llegó a esa nota.

### Paso 4 — Publicación diaria

Cada noche, el sistema recalcula el ranking de la convocatoria. A las 6:00 AM del día siguiente está actualizado.

> **No publicamos en tiempo real instantáneo.** Una actualización diaria es estable, predecible y evita la ansiedad de que el puesto cambie cada hora. Vosotros podéis ajustar este intervalo si lo preferís.

### Paso 5 — Consulta del candidato

El candidato entra a su portal y ve:

- Su nota de cada ruta.
- Su nota media acumulada.
- Su puesto provisional (ej.: 74 de 200).
- Si está dentro o fuera del corte provisional.
- El detalle pedagógico de cada intento, en lenguaje claro.

**No ve datos crudos ni gráficas técnicas** — solo lo que un candidato necesita para entender su evaluación.

### Paso 6 — Cierre formal

Cuando llega la fecha de cierre publicada al inicio de la convocatoria, dos administradores distintos confirman el cierre. El sistema:

1. Calcula el ranking final definitivo.
2. Emite la decisión APTO / NO APTO para todos los candidatos.
3. Genera un **acta PDF firmada con sello de integridad SHA256**, con el listado completo de aprobados y no aprobados.
4. Publica los resultados en los portales.

**Tras el cierre hay una ventana de 24 horas** durante la cual un super-administrador puede revertir el cierre en caso de error administrativo, con justificación obligatoria. Pasadas las 24h, el resultado es irrevocable.

---

## 5. Compliance y garantías legales

### 5.1 Conforme a la oposición pública española

```
   ✓ Procedimiento auditable según LPACAP (Ley 39/2015)
   ✓ Acta PDF generada en cada cierre, con hash de integridad
   ✓ Recurso administrativo del candidato soportado dentro del sistema
     (mecanismo formal con plazo legal de 30 días)
   ✓ Doble validación administrativa para el cierre (estándar de oposición)
   ✓ Trazabilidad completa de cada decisión
```

### 5.2 GDPR / Protección de Datos

```
   ✓ Política de retención clara (12 meses para datos crudos,
     indefinido para los intentos como evidencia legal)
   ✓ Derecho de acceso del candidato (GDPR art. 15)
     — el candidato exporta todos sus datos cuando quiera
   ✓ Derecho al olvido respetando la base legal de oposición pública
     (GDPR art. 17, con excepción Ley 39/2015)
   ✓ Audit log inmutable de toda acción administrativa
   ✓ Aviso de privacidad obligatorio en la inscripción
   ✓ Roles definidos: CMadrid es el Data Controller; nosotros el Data Processor
   ✓ DPO a confirmar conjuntamente antes del cutover
```

### 5.3 Recurso del candidato

El sistema soporta el flujo completo de recurso administrativo en oposición:

1. El candidato impugna formalmente desde el portal.
2. El sistema exporta un **paquete de evidencia** completo del candidato (todos sus intentos, datos crudos, score detallado, audit log).
3. La comisión externa lo procesa con esos datos.
4. La resolución se registra en el sistema como `OutcomeAmendment` vinculado al expediente.

> El intento original **nunca se modifica**. El amendment es un registro adicional. Esto preserva la cadena de evidencia legal.

### 5.4 Política de cambio de reglas durante una convocatoria abierta

```
   PRINCIPIO: igualdad de trato dentro de una convocatoria.

   Una vez publicada una convocatoria, las reglas de evaluación
   (umbrales, pesos por familia, criterios de desempate)
   quedan FIRMES y se aplican uniformemente a todos los
   candidatos de esa convocatoria.

   Si durante la convocatoria se detecta un BUG (no un cambio
   de criterio):
     · CMadrid + DobackSoft documentan el bug.
     · Se reprocesan los intentos afectados con la lógica
       correcta, manteniendo la versión documentada del cambio.
     · El audit log refleja el reproceso con su justificación.

   Si CMadrid quiere cambiar reglas que NO son bug:
     · Se aplica solo a la SIGUIENTE convocatoria.
     · El simulador permite previsualizar el impacto antes
       de publicar.

   Esto está alineado con LPACAP (igualdad de trato, transparencia
   procedimental) y se documenta por escrito antes de cada
   convocatoria real.
```

---

## 6. Cómo se opera el sistema

### 6.1 Día a día

| Quién | Qué hace | Cuánto tiempo le toma |
|---|---|---|
| **Candidato** | Pasa tarjeta, conduce, consulta resultado | Minutos |
| **Instructor (responsable)** | Revisa la matriz de su convocatoria, atiende auditorías | ~30 min/día por convocatoria |
| **Administrador** | Configura rutas y reglas (al inicio de convocatoria), cierra al final | Horas iniciales + cierre formal |

### 6.2 Cierre formal (proceso de 3 pasos)

```
   Paso 1 — PREVIEW
   Un administrador revisa el ranking final simulado:
     · Candidatos completados / pendientes
     · Auditorías pendientes
     · Cuántos pasarían a APTO y a NO_APTO

   Paso 2 — INICIO
   El administrador inicia el cierre formal escribiendo
   el nombre exacto de la convocatoria.

   Paso 3 — CONFIRMACIÓN POR SEGUNDO ADMINISTRADOR
   Un administrador DISTINTO confirma. El sistema valida
   que sea otra persona y le pide re-autenticación.
   Solo entonces se ejecuta el cierre + se genera el acta.

   Tras el cierre: ventana de 24 horas para reversa
   por error administrativo. Pasada esta ventana, el
   resultado es irrevocable.
```

### 6.3 Soporte técnico

```
   La captura y el cálculo son autónomos en el flujo normal.
   La DECISIÓN final APTO / NO APTO la toma siempre CMadrid en
   el cierre formal de la convocatoria, con doble validación
   administrativa (3 pasos: preview, initiate, confirm).

   Esto cumple con el artículo 22 del Reglamento General de
   Protección de Datos (GDPR): la decisión que afecta al
   candidato NO es producto exclusivo de un proceso automatizado;
   hay revisión humana significativa en el cierre.

   Casos que requieren intervención (esperados <1% de los intentos):
   · Solicitud de auditoría del candidato → resuelve el responsable
   · Recategorización de fallo técnico → admin con justificación
   · Reversa de cierre por error → SUPER_ADMIN con justificación

   Cualquier acción crítica queda en el audit log:
     · Quién la hizo
     · Cuándo
     · Por qué
     · Desde qué IP
```

---

## 7. Plan de despliegue — fechas y fases

```
   ┌──────────────────────────────────────────────────────────────┐
   │                                                              │
   │   FASE 1 — DEMO (entrega 11 de mayo de 2026)                │
   │     Sistema funcionando end-to-end con datos reales.         │
   │     Validación conjunta con CMadrid.                         │
   │                                                              │
   │   FASE 2 — DEFINICIÓN Y PULIDO (mayo - julio 2026)           │
   │     Definición conjunta de las reglas finales.               │
   │     Notificaciones por email, acta firmada cualificada,      │
   │     recurso administrativo operativo.                        │
   │                                                              │
   │   FASE 3 — DESPLIEGUE GRADUAL (junio - julio 2026)           │
   │     Cutover convocatoria por convocatoria.                   │
   │     Sistema actual y nuevo en paralelo durante el primer     │
   │     periodo, comparando resultados.                          │
   │                                                              │
   │   FASE 4 — OPERACIÓN PLENA (octubre 2026)                    │
   │     Sistema nuevo en producción. Sistema anterior retirado.  │
   │                                                              │
   └──────────────────────────────────────────────────────────────┘
```

### Lo que CMadrid valida en la reunión del 11 de mayo

- ✓ El sistema funciona end-to-end con datos reales (convocatoria demo de 50 candidatos).
- ✓ La matriz del responsable se ve y se navega correctamente.
- ✓ El ranking se calcula y se publica.
- ✓ El simulador permite probar cambios sin tocar producción.
- ✓ El proceso de cierre con doble validación funciona.
- ✓ El portal del alumno respeta la regla de no mostrar telemetría cruda.
- ✓ La cabina del camión opera con tarjeta RFID.

### Lo que se incorpora en Fase 2 (antes del cutover real)

- Notificaciones automáticas por email (al alumno, al manager, al cierre de convocatoria).
- Firma digital cualificada del acta (eIDAS / FirmaProfesional).
- Mecanismo formal del recurso administrativo del candidato.
- Endurecimiento del kiosko frente a casos reales (conexión, batería, hardware extremo).

---

## 8. Lo que necesitamos de CMadrid

Para que el plan se cumpla en los plazos, conviene cerrar conjuntamente algunas cosas:

```
   ▶ Reglas finales de evaluación
     - Umbrales por tipo de infracción (qué se considera "exceso", "brusco")
     - Pesos relativos de cada familia (estabilidad, velocidad, ruta, conducción)
     - Nota mínima orientativa para apto

   ▶ Parámetros de la primera convocatoria real
     - Fecha de cierre publicada
     - Número de plazas
     - Cuál es la "ruta principal" para criterio de desempate
     - Lista de candidatos inscritos

   ▶ Aspectos legales
     - DPO (Delegado de Protección de Datos) designado
     - Texto del aviso de privacidad para los candidatos
     - Procedimiento del recurso administrativo (alineación con vuestro asesor legal)

   ▶ Aspectos técnicos
     - Acceso al sandbox de Webfleet (o confirmación de que solo hay producción)
     - Hardware del kiosko (lector RFID en cada cabina)
     - Acceso para nuestro equipo a un staging compartido
```

Esta es una conversación operativa de **1-2 reuniones**, no un proyecto en sí mismo. La hacemos en paralelo a la Fase 2.

---

## 8.bis Inversión, SLA y términos contractuales

> **Nota:** las cifras concretas (importes, porcentajes de penalización, plazos exactos) se acordarán en la reunión del 11 de mayo. Los modelos descritos aquí son la propuesta de partida.

### 8.bis.1 Modelo económico propuesto

Tres componentes, separados por claridad:

```
   1. SETUP INICIAL (pago único)
      Cubre el sprint de construcción + integración con Webfleet de CMadrid +
      formación del equipo de admins e instructores + traspaso documental.

      Esquema de hitos propuesto (alineado con normativa de contratación
      pública española — pago contra entregable verificable):
        Hito 1 (~30%): firma del contrato.
        Hito 2 (~30%): demo aceptada por CMadrid (lunes 11/05/2026).
        Hito 3 (~25%): cutover validado de la primera convocatoria real.
        Hito 4 (~15%): primera convocatoria cerrada con acta firmada.

      Modelo alternativo (menor preferencia por contratación pública):
        50% al kickoff, 50% tras el cutover validado.

   2. SUSCRIPCIÓN MENSUAL (mantenimiento + operación)
      Incluye:
        - Mantenimiento del backend, frontend, base de datos.
        - Sync con Webfleet y Doback Elite operativos.
        - Actualizaciones de seguridad y dependencias.
        - Backups diarios + verificación + retención según política GDPR.
        - Soporte técnico en horario laboral (ver SLA abajo).
        - Cron de ranking diario, generación de actas, generación de exports GDPR.

   3. POR CONVOCATORIA REAL CERRADA (variable)
      Importe acordado por convocatoria efectivamente cerrada en producción.
      Cubre el coste variable de cuota Webfleet + storage de raw_samples
      durante 12 meses + generación del acta firmada cualificada.

   4. SOPORTE EXTENDIDO PARA DÍA DE CIERRE FORMAL (variable, opcional)
      Para los días de cierre formal de cada convocatoria real:
        - Presencia on-site o stand-by garantizado del equipo.
        - Cobertura ampliada vs el horario laboral estándar.
      Tarifa por convocatoria, acordada en contrato.

   Las cifras concretas se proponen en negociación bilateral antes
   de la firma del contrato.
```

**Por qué este modelo:** separa el coste fijo (mantenimiento del sistema) del coste variable (uso real). CMadrid paga proporcional al volumen real de candidatos evaluados.

### 8.bis.2 SLA — Service Level Agreement

```
   ┌──────────────────────────────────────────────────────────────┐
   │                                                              │
   │   Disponibilidad:    99.5 % mensual (medido sobre /health)   │
   │                      Excluye ventanas de mantenimiento       │
   │                      programadas (notificadas con 7 días).   │
   │                                                              │
   │   Tiempo de respuesta a incidente:                           │
   │     - CRÍTICO (sistema caído, cierre bloqueado)              │
   │       → primera respuesta < 1 hora (laborable)               │
   │       → resolución objetivo < 4 horas                        │
   │     - ALTO (degradación funcional sin pérdida de datos)      │
   │       → primera respuesta < 4 horas (laborable)              │
   │       → resolución objetivo < 24 horas                       │
   │     - MEDIO/BAJO (bug menor, mejora)                         │
   │       → primera respuesta < 2 días laborables                │
   │                                                              │
   │   Soporte:                                                   │
   │     - Horario laboral L-V 09:00-18:30 (Europe/Madrid)        │
   │     - Para días de cierre formal de convocatoria, soporte    │
   │       extendido coordinado con anticipación de 7 días.       │
   │                                                              │
   │   Backups:                                                   │
   │     - DB completa cada 24h                                   │
   │     - Verificación automática + alerta si falla              │
   │     - Retención de backups: 30 días en caliente, 12 meses    │
   │       archivado.                                             │
   │                                                              │
   │   RPO (Recovery Point Objective): < 1 hora                   │
   │   RTO (Recovery Time Objective):  < 4 horas                  │
   │                                                              │
   │   Penalizaciones:                                            │
   │     - Si la disponibilidad mensual cae por debajo del SLA,   │
   │       se aplica un descuento proporcional sobre la cuota     │
   │       mensual (% a acordar bilateralmente).                  │
   │                                                              │
   └──────────────────────────────────────────────────────────────┘
```

### 8.bis.3 Continuidad del equipo y del sistema

Una preocupación legítima: ¿qué pasa si el equipo se va?

```
   ▶ Code escrow — acceso desde día 1, no condicionado al cese
     Desde la firma del contrato, CMadrid recibe acceso de
     LECTURA al repositorio de código (rol "auditor"). Esto
     permite:
       - Auditoría continua del código y su evolución.
       - Verificación de la integridad del sistema en cualquier
         momento por personal técnico de CMadrid o un tercero
         designado.
       - Cláusula opcional: auditoría externa anual del escrow
         por una empresa acordada bilateralmente.

     En caso de cese de la relación, CMadrid puede asumir la
     titularidad operativa o transferir a otro proveedor con
     toda la trazabilidad disponible.

   ▶ Documentación
     Mantenida actualizada en el repositorio. Incluye:
       - Paper Maestro técnico (este nivel de detalle)
       - Runbooks operativos (deploy, backups, rollback)
       - Documento ejecutivo (visión general)

   ▶ Knowledge transfer
     Si el equipo cambia, hay un proceso de traspaso documentado:
     30 días de overlap mínimo entre equipo saliente y entrante.

   ▶ Salida controlada
     Si CMadrid decide cambiar de proveedor o internalizar el
     desarrollo, garantizamos:
       - Export completo de datos en formato estándar
       - Documentación de despliegue para cualquier equipo capaz
       - 60 días de soporte de transición
```

### 8.bis.4 Formación del equipo de CMadrid

Durante Fase 2 (mayo–julio 2026), formación incluida en el setup inicial:

```
   ▶ Sesión para administradores (4h)
     - Cómo configurar convocatorias, plazas, fechas
     - Cómo gestionar tarjetas RFID y kioskos
     - Cómo usar el simulador antes de cambiar reglas
     - Cómo ejecutar el cierre de convocatoria (3 pasos)
     - Manual operativo en PDF de referencia

   ▶ Sesión para instructores / managers (2h)
     - Cómo navegar la matriz alumno × ruta
     - Cómo leer el detalle de un intento
     - Cómo resolver auditorías
     - Manual operativo en PDF de referencia

   ▶ Sesión para alumnos (autoservicio)
     - Vídeo tutorial de 5 minutos al iniciar sesión por primera vez
     - FAQ accesible desde el portal
     - Sin formación presencial requerida

   ▶ Soporte L1 transitorio
     Durante las primeras 4 semanas tras el cutover, atención directa
     a dudas operativas de admins e instructores via Slack o email.
```

### 8.bis.5 Hardware Doback Elite — logística e instalación

El sistema usa un dispositivo propio (**Doback Elite**) instalado en cada camión. Aclaramos quién hace qué para evitar bloqueos operativos.

```
   ▶ Suministro
     Doback Elite es producto propio. Lo entregamos calibrado
     y configurado por unidad, listo para enchufar.

   ▶ Instalación física en el camión
     - PROPUESTA POR DEFECTO: instalación a cargo nuestro,
       coordinada con el responsable de flota de CMadrid.
       Tiempo aproximado: 30-45 minutos por camión.
     - ALTERNATIVA: instalación por personal técnico de CMadrid
       (mecánicos del parque). Entregamos manual paso a paso
       + acompañamiento remoto en la primera unidad.
     - La elección la toma CMadrid según preferencia operativa.

   ▶ Mantenimiento del hardware
     - Sustitución por avería: stock de reposición acordado
       (cantidad a definir según número de camiones).
     - SLA de reposición: dispositivo de repuesto en parque
       en 48h laborables tras notificación de avería confirmada.
     - Diagnóstico previo: nuestro equipo verifica de forma
       remota si el problema es del dispositivo o del entorno
       antes de movilizar reposición.

   ▶ Conectividad
     Doback Elite usa la red 4G del propio dispositivo (SIM data
     incluida en el modelo de suscripción) — no depende del
     wifi del parque ni de la red interna de CMadrid.

   ▶ Coordinación con vuestra flota
     Necesitamos del responsable de flota de CMadrid:
       - Lista de camiones objetivo (matrícula + ubicación parque)
       - Ventana semanal de 2-3h para instalaciones (no bloquea
         la operatividad: instalamos camión por camión)
       - Punto de contacto único para incidencias hardware
```

**Resumen ejecutivo:** vosotros no os ocupáis de logística de hardware salvo que lo prefiráis. Llegamos, instalamos, repuestos en 48h, y si algo falla diagnosticamos antes de movilizar a nadie.

---

### 8.bis.6 Términos contractuales clave

```
   ▶ Propiedad del código
     CMadrid recibe licencia de uso perpetua e irrevocable del código
     desarrollado para el proyecto Training. La titularidad intelectual
     queda según se acuerde en el contrato (modelos posibles: licencia
     de uso, copropiedad, transferencia íntegra).

   ▶ Propiedad de los datos
     Los datos de los candidatos son íntegramente de CMadrid. Nosotros
     somos Data Processor (procesador) en términos GDPR; CMadrid es el
     Data Controller (responsable). Nunca cedemos ni reutilizamos datos
     a terceros.

   ▶ Confidencialidad
     NDA mutuo desde el inicio del contrato. Datos personales de
     candidatos sometidos a estrictas medidas de seguridad acordes al
     Reglamento Europeo de Protección de Datos.

   ▶ Plazos contractuales
     - Sprint inicial (este sprint): cerrado, fecha fija 11 de mayo.
     - Fase 2 + cutover: hasta julio 2026.
     - Suscripción: anual con renovación automática salvo aviso 60 días
       antes de vencimiento.
     - Salida: 60 días de preaviso mínimo desde cualquier parte.

   ▶ Resolución de disputas
     Mediación en primera instancia. Jurisdicción: tribunales de Madrid.

   ▶ Aspectos pendientes de negociación bilateral
     - Importes concretos (los tres componentes del modelo)
     - Porcentajes de penalización por incumplimiento de SLA
     - Cláusulas específicas de propiedad intelectual
     - Garantías adicionales si CMadrid las requiere
```

---

## 9. Sobre el equipo

Equipo dedicado al proyecto Training durante el sprint y la operación posterior. Cada persona tiene un dominio claro y un responsable nombrado.

### Antonio Hermoso — Director técnico y enlace con CMadrid

```
   ▶ Rol
     - Arquitectura del sistema y decisiones estructurales
     - Integración con Webfleet (su código en este proyecto)
     - Único interlocutor técnico con CMadrid

   ▶ Trayectoria
     - +15 años en desarrollo de software
     - Especialización en arquitectura de sistemas y plataformas SaaS
     - Experiencia previa con clientes del sector público y privado
     - Autor del sistema DobackSoft (plataforma de telemetría
       vehicular de la que parten los aprendizajes técnicos
       aplicados a Training)
```

### Jesús — Responsable de backend

```
   ▶ Rol
     - Motor de scoring y ranking
     - Persistencia, modelo de datos, cierre formal de convocatoria
     - Lógica de auditoría y reevaluación

   ▶ Trayectoria
     - Desarrollador backend senior con experiencia en
       sistemas de evaluación con requisitos de trazabilidad
     - Familiarizado con Prisma + PostgreSQL en entornos productivos
```

### Alejandro — Responsable de frontend

```
   ▶ Rol
     - Los 4 portales (candidato, instructor, admin, kiosko)
     - Diseño de experiencia y accesibilidad (WCAG AA)
     - Internacionalización (es / en)

   ▶ Trayectoria
     - Desarrollador frontend con foco en React + TypeScript
     - Experiencia en interfaces para entornos regulados donde la
       claridad de la información es crítica
```

### Joel — Responsable del simulador y QA

```
   ▶ Rol
     - Simulador de reglas (pieza diferencial del producto)
     - Tests automatizados end-to-end
     - Datos de prueba, despliegue continuo, validación pre-demo

   ▶ Trayectoria
     - Perfil de QA con experiencia en automatización de pruebas
     - Trabaja en inglés; el equipo está preparado para colaborar
       en formato bilingüe sin fricción
```

### Forma de trabajar

```
   ▶ Equipo de 4 personas dedicadas durante el sprint
     Reducido por elección, no por limitación: cada decisión técnica
     tiene un responsable claro y la comunicación con CMadrid es directa.

   ▶ Director técnico único como punto de contacto
     CMadrid siempre habla con Antonio. No hay capas intermedias
     ni traspasos de información.

   ▶ Visibilidad operativa
     Status semanal por escrito al cierre de cada viernes durante
     el sprint y reuniones de seguimiento mensuales tras el cutover.
```

> **Sobre las trayectorias detalladas.** Disponemos de los CVs completos del equipo a disposición de CMadrid bajo NDA si vuestro proceso de contratación lo requiere para la fase contractual.

---

## 10. Por qué Training y por qué ahora

```
   ▶ Diseñado específicamente para vuestro caso de uso
     No es un producto genérico adaptado al cuerpo de bomberos:
     se construye con el modelo de oposición, las plazas fijas y
     la decisión final al cierre de convocatoria como núcleo.

   ▶ Arquitectura revisada antes de empezar a construir
     El paper técnico ha pasado por dos rondas de revisión adversarial
     documental antes del sprint. Los 9 invariantes arquitectónicos
     son las reglas de oro que el equipo respeta durante el desarrollo.

   ▶ Conocimiento previo del dominio
     Antonio (director técnico) ha trabajado durante el último año
     con datos reales del cuerpo de bomberos de Madrid en el contexto
     del proyecto DobackSoft Fleet, lo que reduce sustancialmente la
     curva de aprendizaje del problema.

   ▶ Complejidad acotada
     Quitamos lo que no aplica al caso de uso (telemetría general,
     IA, geofencing complejo) y nos enfocamos en lo que sí.

   ▶ Decisiones legales previstas desde el diseño
     LPACAP, GDPR y derecho de recurso administrativo entran en
     el modelo desde la versión inicial — no como capa añadida después.
```

---

## 11. Próximos pasos concretos

```
   1. Reunión del 11 de mayo de 2026
      Demo en vivo del sistema. Validación de la dirección.
      Resolución de las primeras preguntas operativas.

   2. Mayo de 2026
      Definición conjunta de reglas y parámetros de la primera
      convocatoria real. Coordinación con vuestro DPO.

   3. Junio - julio de 2026
      Pulido técnico, integración legal, preparación del cutover.

   4. Cutover gradual
      Convocatoria por convocatoria. Operación en paralelo durante
      el primer periodo. Validación de paridad con sistema actual.

   5. Octubre de 2026
      Sistema en operación plena. Cierre del proyecto de transición.
```

---

## Cierre

Training es un **sistema maduro en su arquitectura, prudente en sus límites y transparente en sus decisiones**. Está diseñado para evaluar candidatos sin sesgo subjetivo, generar evidencia auditable, y sobrevivir a los procesos legales que toda oposición pública requiere.

La parte técnica está resuelta. Lo que queda es una conversación operativa con vosotros sobre las reglas concretas, los plazos, y el procedimiento legal del recurso.

**El equipo está listo. La demo es el 11 de mayo.**

---

### Contacto

```
   Antonio Hermoso González
   Director técnico — proyecto Training
   ia@cosigein.es
```

---

*Esta propuesta es la versión comercial del proyecto. Existe documentación técnica detallada disponible bajo NDA si vuestro equipo de IT desea revisarla.*
