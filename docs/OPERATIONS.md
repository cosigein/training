# Operations — incidentes, rollback, secretos, soporte

> Guía operacional del equipo para los momentos donde algo falla o donde hace falta una decisión bajo presión. **Léela una vez, volvé a ella cuando aplique.**

---

## 1. Severidad de incidentes

Antes de actuar, calificás:

| Severidad | Qué significa | Tiempo de respuesta objetivo |
|---|---|---|
| **P0** | Sistema caído. Cierre de convocatoria bloqueado. Pérdida de datos. | Inmediata. Antonio se involucra siempre. |
| **P1** | Degradación funcional sin pérdida de datos. Usuarios ven errores. | <1 hora laboral. |
| **P2** | Bug recuperable. Workaround disponible. | <24 horas laborables. |
| **P3** | Mejora, sugerencia, deuda técnica menor. | Próxima ventana de pulido. |

**Regla:** ante duda, escalá una arriba. Mejor 2 personas mirando un P1 que un P0 ignorado.

---

## 2. Respuesta a incidentes (durante una convocatoria real)

```
   PASO 1 — Detección
   ▶ El que detecta el incidente lo escribe en el chat del equipo
     en menos de 5 minutos. Mensaje template:
        [P?] Qué pasa: __ · Desde cuándo: __ · A quiénes afecta: __

   PASO 2 — Triage (5 min)
   ▶ El que lo detectó propone severidad.
   ▶ Antonio confirma o ajusta. Si Antonio no responde en 10 min,
     el más senior disponible decide.

   PASO 3 — Contención (objetivo: parar el sangrado)
   ▶ NO se debugea en producción. NO se hacen pushes en caliente.
   ▶ Si el bug afecta el cierre formal de una convocatoria → activar
     rollback del último deploy (ver §3).
   ▶ Si afecta a usuarios pero el cierre no está activo → comunicar
     a CMadrid + workaround si existe.

   PASO 4 — Comunicación al cliente (CMadrid)
   ▶ La hace Antonio. Solo Antonio.
   ▶ Plantilla mínima:
        "Detectamos [qué]. Estimamos resolución [cuándo].
         Workaround mientras tanto: [si existe].
         Próxima actualización en [tiempo]."
   ▶ Frecuencia: cada 30 min hasta resolución para P0,
     cada 2 horas para P1.

   PASO 5 — Postmortem
   ▶ Para todo incidente P0/P1: postmortem escrito en menos de 48h.
   ▶ Plantilla: qué pasó, cuándo, impacto, causa raíz, qué
     cambia (proceso, código, monitoring).
   ▶ Se discute en el daily siguiente. SIN buscar culpables.
```

---

## 3. Rollback

### 3.1 Migración Prisma rota

```bash
# 1. Identificar la migración problemática:
pnpm --filter @training/api prisma migrate status

# 2. Marcar como rolled back en la tabla _prisma_migrations:
pnpm --filter @training/api prisma migrate resolve --rolled-back <migration_name>

# 3. Si los datos quedaron inconsistentes, restaurar el último backup
#    de la DB (ver §5 disaster recovery).

# 4. NO marques una migración aplicada manualmente como "applied" en prod.
#    Si necesitás eso, escalalo a Antonio antes.
```

### 3.2 Deploy roto (frontend o backend)

```
   1. Identificar el último commit en `main` que estaba verde:
        git log --oneline main
   2. Volver a ese commit en el VPS:
        ssh deploy@staging.training
        cd /srv/training && git checkout <commit-bueno>
        pnpm install --frozen-lockfile && pnpm build
        sudo systemctl restart training-api training-worker
   3. Verificar que /health/deep devuelve 200.
   4. Comunicar al equipo en chat: "rolled back to <commit>".
   5. Abrir issue postmortem.
```

### 3.3 Decisión: ¿hotfix o rollback?

```
   ¿Tenés la causa raíz identificada Y un fix de <30 minutos? → HOTFIX.
   ¿No tenés causa raíz, o el fix supera 30 min?              → ROLLBACK.
```

Hotfix bajo presión casi siempre genera el siguiente bug. Si dudás, rollback.

---

## 4. Gestión de secretos

### 4.1 Reglas duras

- **Nunca** se commitean secretos al repo. Ni en `.env`, ni en YAML, ni en docs, ni en comentarios.
- **Nunca** se mandan secretos por chat o email en claro.
- **Nunca** se loguean secretos (Winston redacta `password`, `token`, `secret` por defecto — verificar configuración el día 2).

### 4.2 Dónde viven los secretos

| Entorno | Dónde | Cómo se rotan |
|---|---|---|
| **Desarrollo local** | `.env` en cada repo (gitignored) | Cada quien el suyo. No compartido. |
| **Staging** | Variables de entorno del VPS (Hetzner CX22) | Cuando Antonio rote, avisa al equipo |
| **Producción (Fase 3+)** | Vault o 1Password Teams (a decidir antes de cutover) | Política formal a definir antes de octubre 2026 |

### 4.3 Rotación periódica

| Secreto | Frecuencia |
|---|---|
| `JWT_SECRET` | Cada 90 días en producción |
| `CSRF_SECRET` | Cada 90 días en producción |
| Password de DB | Cada 6 meses |
| Webfleet credentials | A demanda (cuando CMadrid los rote en su lado) |
| API keys de terceros | Anual o si hay sospecha de leak |

### 4.4 Si sospechás de un leak

1. Asumí que el secreto está comprometido.
2. Rotalo INMEDIATAMENTE.
3. Auditá los últimos 30 días de logs en busca de uso anómalo.
4. Postmortem si fue real.

---

## 5. Disaster recovery

### 5.1 Backups de DB

- **Diario:** dump completo a las 03:00 (Europe/Madrid). Cron en el VPS.
- **Retención:** 30 días en caliente (mismo VPS), 12 meses archivado (S3-compatible).
- **Verificación:** un job comprueba que el backup se completó y que es restaurable contra una DB de prueba **una vez por semana**.

### 5.2 Restauración

Tiempo objetivo (RTO): **<4 horas** desde la decisión de restaurar.
Pérdida máxima de datos (RPO): **<1 hora** si el backup más reciente es de hace <24h.

```bash
# En el VPS de producción:
psql $DATABASE_URL < /backups/training-YYYY-MM-DD.sql

# Si el backup es S3-archivado:
aws s3 cp s3://training-backups/YYYY-MM/training-YYYY-MM-DD.sql.gz - | gunzip | psql $DATABASE_URL
```

### 5.3 Snapshots del VPS

- **Semanal** (los domingos de madrugada). Hetzner soporta esto nativamente.
- Útiles si hay corrupción de archivos del sistema, no de DB.

### 5.4 Test de DR

**Una vez al mes** durante Fase 3, alguien del equipo simula la pérdida de la DB de staging y la restaura desde backup. Cronómetro corriendo. Si excede 4h, postmortem.

---

## 6. Soporte post-cutover (CMadrid)

A partir del cutover validado de la primera convocatoria real (julio 2026 según roadmap):

### 6.1 Punto único de contacto

**Antonio** durante los primeros 6 meses post-cutover.
Después, según evolución: o Antonio sigue, o se asigna un Customer Success.

### 6.2 Canales

| Canal | Para qué | Tiempo de respuesta |
|---|---|---|
| **Email dedicado** (ej: training-soporte@cosigein.es) | Dudas operativas, tickets P2/P3 | <2 días laborables |
| **WhatsApp directo a Antonio** | Solo P0/P1 con sistema en producción | <1 hora laboral |
| **Llamada telefónica** | Solo P0 si los anteriores no funcionan | Inmediata |

### 6.3 Horario garantizado

- **Estándar:** L-V 09:00-18:30 (Europe/Madrid).
- **Días de cierre formal de convocatoria:** soporte extendido on-site o stand-by garantizado, coordinado con 7 días de anticipación.
- **Fines de semana / festivos:** solo atención de incidentes P0 reportados a WhatsApp.

### 6.4 L1 transición a CMadrid

Durante las primeras **4 semanas post-cutover**:
- Antonio atiende dudas operativas directamente.
- Cada duda recibida se documenta y entra en un FAQ que se va publicando en el portal interno de CMadrid.

A las 4 semanas:
- El FAQ se entrega a los admins de CMadrid.
- Las dudas operativas se filtran: las que están en el FAQ las resuelve CMadrid; las que no, escalan a nosotros.
- Esto baja el volumen de soporte progresivamente.

---

## 7. Plantillas operacionales

### 7.1 Mensaje de incidente al chat del equipo

```
[P0/P1/P2] Incidente en [API / Web / Kiosko / Webfleet]
Síntoma: __
Desde: __ (timestamp)
Afecta a: __ (qué usuarios / qué flujos)
Yo me ocupo / Necesito ayuda con: __
```

### 7.2 Comunicación a CMadrid (Antonio)

```
Estimado [contacto],

Detectamos [síntoma observable, sin tecnicismos].
Impacto: [qué pueden o no hacer ahora].
Estimación de resolución: [hora].
Workaround: [si existe, en pasos cortos].
Próxima actualización: [hora].

Quedamos atentos.
[Antonio]
```

### 7.3 Postmortem (formato corto, <1 página)

```
INCIDENTE [fecha] · [P0/P1/P2]

Qué pasó:
Desde cuándo / hasta cuándo:
Impacto (usuarios, datos, tiempo):
Causa raíz:
Cómo lo resolvimos:

Qué cambia para que no vuelva a pasar:
   - Cambio en código:
   - Cambio en proceso:
   - Cambio en monitoring/alertas:

Lecciones (sin buscar culpables):
```

---

**Si una situación operativa NO está cubierta acá**, escribilo en el chat y lo añadimos. Un runbook que no cubre la realidad no sirve.
