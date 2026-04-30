# Notas de migración — Tareas 1+2 del roadmap

## Qué cambió (resumen)

1. **Borrados** los blueprints `geofences`, `telemetry`, `kpis`, `reports` (out-of-scope para Training).
2. **Borrados** los modelos `Geofence`, `KPI`, `Report` (y relaciones colgantes en `Organization`).
3. **Extendido** el enum `UserRole` con 2 valores nuevos: `SUPER_ADMIN`, `STUDENT`.
4. **Agregados** 2 campos al modelo `User`: `managedConvocatorias` (JSONB) y `studentProfileId` (string nullable).
5. **Refactor** del sidebar (`base.html`): Reportes/Dashboard/KPIs Avanzados quitados; Ingesta y Administración solo visibles para `ADMIN` y `SUPER_ADMIN`.
6. **Refactor** del seed (`setup_db.py`): ahora crea 5 usuarios de test (super, admin, manager, 2 alumnos).

---

## ⚠️ Issue crítico: el enum `userrole` en Postgres

El modelo Python tiene `STUDENT` y `SUPER_ADMIN` en el enum, **pero la BD viva NO los tiene** porque Postgres ya creó el tipo `userrole` con los 4 valores antiguos cuando corriste `setup_db.py` la primera vez.

`db.create_all()` **no actualiza enums existentes**. Si intentás crear un user con rol `STUDENT` ahora, Postgres tira:
```
psycopg2.errors.InvalidTextRepresentation: invalid input value for enum userrole: "STUDENT"
```

### Tenés 2 caminos

#### Opción A — Drop BD y rearrancar (RECOMENDADO en dev)

Si NO te importa perder los datos actuales (admin, manager, sesiones importadas):

```bash
# 1. Borrar la BD entera
sudo -u postgres psql -c "DROP DATABASE doback_dev;"

# 2. Rearmar todo limpio
.venv/bin/python setup_db.py

# 3. (Opcional) Re-importar datos del Doback
.venv/bin/python import_data.py ../doback028
```

Vas a tener: 1 org (CMadrid) + 5 usuarios (super/admin/manager/2 alumnos) + tablas vacías.

#### Opción B — ALTER TYPE manual (si querés conservar datos)

```bash
PGPASSWORD=postgres psql -h localhost -U postgres -d doback_dev <<'SQL'
ALTER TYPE userrole ADD VALUE IF NOT EXISTS 'SUPER_ADMIN';
ALTER TYPE userrole ADD VALUE IF NOT EXISTS 'STUDENT';
ALTER TABLE "User" ADD COLUMN IF NOT EXISTS "managedConvocatorias" JSONB DEFAULT '[]';
ALTER TABLE "User" ADD COLUMN IF NOT EXISTS "studentProfileId" VARCHAR;
SQL

# Después corré setup_db.py para que cree los usuarios nuevos (super, alumnos)
.venv/bin/python setup_db.py
```

Las tablas viejas (`Geofence`, `KPI`, `Report`, `Park`, `Zone`, etc.) van a quedar en la BD pero sin uso. Si te molestan:

```bash
PGPASSWORD=postgres psql -h localhost -U postgres -d doback_dev <<'SQL'
DROP TABLE IF EXISTS "GeofenceVehicleState" CASCADE;
DROP TABLE IF EXISTS "GeofenceEvent" CASCADE;
DROP TABLE IF EXISTS "GeofenceRule" CASCADE;
DROP TABLE IF EXISTS "Geofence" CASCADE;
DROP TABLE IF EXISTS "Park" CASCADE;
DROP TABLE IF EXISTS "Zone" CASCADE;
DROP TABLE IF EXISTS "AdvancedVehicleKPI" CASCADE;
DROP TABLE IF EXISTS "VehicleKPI" CASCADE;
DROP TABLE IF EXISTS "ParkKPI" CASCADE;
DROP TABLE IF EXISTS "Lens" CASCADE;
DROP TABLE IF EXISTS "daily_kpi" CASCADE;
DROP TABLE IF EXISTS "ProcessingEvent" CASCADE;
DROP TABLE IF EXISTS "PipelineStep" CASCADE;
DROP TABLE IF EXISTS "Report" CASCADE;
DROP TABLE IF EXISTS "ScheduledReport" CASCADE;
DROP TABLE IF EXISTS "InformeGenerado" CASCADE;
SQL
```

---

## Usuarios de test después del seed

| Email | Password | Rol |
|---|---|---|
| `super@cmadrid.com` | `super123` | `SUPER_ADMIN` |
| `admin@cmadrid.com` | `admin123` | `ADMIN` |
| `manager@cmadrid.com` | `manager123` | `MANAGER` |
| `alumno1@cmadrid.com` | `alumno123` | `STUDENT` |
| `alumno2@cmadrid.com` | `alumno123` | `STUDENT` |

---

## Verificación post-migración

```bash
# 1. La app arranca
.venv/bin/python -c "from app import create_app; create_app(); print('OK')"

# 2. Los roles están todos
PGPASSWORD=postgres psql -h localhost -U postgres -d doback_dev -c "SELECT unnest(enum_range(NULL::userrole));"

# 3. Los 5 usuarios se sembraron
PGPASSWORD=postgres psql -h localhost -U postgres -d doback_dev -c 'SELECT email, role FROM "User";'
```

Tendrías que ver los 6 valores del enum y los 5 usuarios.

---

## Próximas tareas del roadmap

Siguiente: **Tarea 3** — crear modelos `Convocatoria` y `Enrollment`. Ver `TRAINING-ROADMAP.md` §1 y §9.
