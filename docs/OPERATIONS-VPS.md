# OPERATIONS VPS — Training (estado real, 2026-04-29)

> Snapshot de la infra del VPS al cierre de día 2 del sprint.
> Reemplaza/complementa `OPERATIONS.md` para todo lo concreto de Training.
> `OPERATIONS.md` sigue valiendo como **plan operativo de futuro** pero su sección de comandos asume el stack viejo (TS/Node/Prisma/pnpm).

---

## 1. Inventario

### 1.1 Servidor

| Item | Valor |
|---|---|
| Host SSH alias | `dobacksoft-vps` (en `~/.ssh/config` de Antonio) |
| Hostname | `srv844849.hstgr.cloud` (Hetzner / Hostinger) |
| User SSH | `root` |
| OS | Ubuntu 24.04 (kernel 6.8) |
| Compartido con | DobackSoft V3, Tickets (CSGWeb), Engram, Landing |

### 1.2 Repo en el VPS

| Item | Valor |
|---|---|
| Path | `/home/training/treini` |
| Owner | user `training` (uid local) |
| Branch | `main` |
| HEAD al 29/04 | `f4f314a feat: tarea 7 - RfidCard + POST /kiosko/tap + cierre manual` |

### 1.3 Acceso público

| URL | Backend interno | Cert |
|---|---|---|
| `https://srv844849.hstgr.cloud:4000/` | `127.0.0.1:5000` | Letsencrypt (managed by Certbot) |

Otros sites en el mismo VPS (NO son Training):
- `https://srv844849.hstgr.cloud/` (`:443`) → DobackSoft V3 frontend (`:5174`) + `/api`,`/ws` → backend `:9998`
- `https://srv844849.hstgr.cloud:8443/` → CSGWeb Tickets gunicorn `:8000`

---

## 2. Servicio Flask en producción (Training)

### 2.1 systemd unit

```
/etc/systemd/system/training-web.service
```

```ini
[Unit]
Description=Training Flask app (CMadrid sprint, Apr 28 - May 11 2026)
After=network.target postgresql.service
Wants=network.target

[Service]
Type=simple
User=training
Group=training
WorkingDirectory=/home/training/treini
EnvironmentFile=/home/training/treini/.env
ExecStart=/home/training/treini/.venv/bin/python wsgi.py
Restart=always
RestartSec=5
StandardOutput=append:/var/log/training-web.log
StandardError=append:/var/log/training-web.log

[Install]
WantedBy=multi-user.target
```

### 2.2 Comandos rápidos

```bash
# Estado
sudo systemctl status training-web
sudo systemctl is-active training-web      # → active
sudo systemctl is-enabled training-web     # → enabled

# Logs en vivo
sudo journalctl -u training-web -f
sudo tail -f /var/log/training-web.log

# Reiniciar (después de git pull, .env edit, etc.)
sudo systemctl restart training-web

# Detener / arrancar
sudo systemctl stop training-web
sudo systemctl start training-web
```

### 2.3 Modo de ejecución

- **Servidor**: `python wsgi.py` invoca `socketio.run(app, host="127.0.0.1", port=5000)` (eventlet).
- **NO** usa gunicorn hoy (decidido el 29/04 — `socketio.run()` + `Restart=always` cumple lo mismo para staging).
- **NO** usa Alembic todavía (schema vía `db.create_all()` + `setup_db.py`).

---

## 3. Base de datos

### 3.1 Cluster Postgres

| Item | Valor |
|---|---|
| Engine | Postgres 16 (host del VPS, **NO container**) |
| Listen | `127.0.0.1:5432` |
| DB de Training | `training` |
| User | `training` (con `CREATEDB` privilege desde 29/04) |
| Password | en `/home/training/treini/.env` (`DATABASE_URL`) |

> Hay **otro** Postgres en el mismo VPS — el container `dobacksoft-db` mapeado a `127.0.0.1:5433`. Ese **NO es de Training**. No tocar.

### 3.2 Backups

#### Diario (DobackSoft) — NO cubre Training todavía

`/opt/dobacksoft/backups/dobacksoft_YYYYMMDD_030000.sql.gz` — cron 03:00 Madrid, 10 días de retención. **Es del proyecto DobackSoft V3, no de Training.**

> Pendiente: agendar un cron similar para `pg_dump training`. Ver `STATE-2026-04-29.md` §Pendientes.

#### Manual (cuando hace falta)

```bash
# Dump
ssh dobacksoft-vps 'cd /home/training/treini && \
  PGPASS=$(grep ^DATABASE_URL= .env | sed -E "s|.*://training:([^@]*)@.*|\1|") && \
  PGPASSWORD="$PGPASS" pg_dump -h 127.0.0.1 -p 5432 -U training -d training | \
  gzip > /tmp/training_$(date +%s).sql.gz'

# Bajar copia local
scp dobacksoft-vps:/tmp/training_*.sql.gz /tmp/
```

#### Reset BD (idempotente)

```bash
ssh dobacksoft-vps 'sudo -u postgres psql -c "DROP DATABASE IF EXISTS training;"'
ssh dobacksoft-vps 'sudo -u postgres psql -c "CREATE DATABASE training OWNER training;"'
ssh dobacksoft-vps 'sudo -u training bash -c "cd /home/training/treini && \
  set -a && . ./.env && set +a && \
  /home/training/treini/.venv/bin/python setup_db.py"'
ssh dobacksoft-vps 'sudo -u training bash -c "cd /home/training/treini && \
  set -a && . ./.env && set +a && \
  /home/training/treini/.venv/bin/python seed_demo.py"'
```

---

## 4. Redis

| Item | Valor |
|---|---|
| Container | `dobacksoft-redis` (compartido con DobackSoft) |
| Listen | `127.0.0.1:6379` |
| Auth | `--requirepass` (password en `/opt/dobacksoft/.env`) |
| Uso por Training | **degradado a memoria** — Training NO conoce el password |

> Hoy `flask_limiter` y `flask_caching` caen a fallback de memoria silenciosamente. App funciona, sin errores en log. Pendiente para tarea 9 (cron daily-ranking) — ver `STATE-2026-04-29.md`.

---

## 5. nginx

### 5.1 Sites enabled (tras la limpieza del 29/04)

```bash
ls /etc/nginx/sites-enabled/
# dobacksoft -> ../sites-available/dobacksoft   (DobackSoft V3 + Tickets :8443)
# engram     -> ../sites-available/engram
# landing    -> ../sites-available/landing
# tickets    -> ../sites-available/tickets
# training   -> ../sites-available/training     (← Training en :4000)
```

Todos son symlinks (convención uniforme). Antes del 29/04, `dobacksoft` era un file regular — ya normalizado.

### 5.2 Config Training

`/etc/nginx/sites-available/training`:

```nginx
server {
    listen 4000 ssl;
    server_name srv844849.hstgr.cloud;

    client_max_body_size 100M;

    ssl_certificate /etc/letsencrypt/live/srv844849.hstgr.cloud/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/srv844849.hstgr.cloud/privkey.pem;
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host:$server_port;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 5.3 Comandos

```bash
sudo nginx -t                        # validar config
sudo systemctl reload nginx          # aplicar cambios
sudo systemctl status nginx
```

---

## 6. Deploy flow (cómo subir cambios)

> Hoy NO hay CI/CD — el deploy es manual. Pendiente de Joel (CI) en próximos días.

```bash
# 1. Mergear el PR en GitHub a main

# 2. SSH al VPS y pull
ssh dobacksoft-vps
sudo -u training git -C /home/training/treini fetch --all
sudo -u training git -C /home/training/treini status -sb
sudo -u training git -C /home/training/treini pull --ff-only origin main

# 3. Si requirements.txt cambió:
sudo -u training /home/training/treini/.venv/bin/pip install -r /home/training/treini/requirements.txt

# 4. Si setup_db.py cambió o hay modelos nuevos:
sudo -u training bash -c "cd /home/training/treini && set -a && . ./.env && set +a && \
  /home/training/treini/.venv/bin/python setup_db.py"

# 5. Reiniciar el servicio
sudo systemctl restart training-web

# 6. Smoke test
curl -sk -o /dev/null -w "HTTP %{http_code}\n" https://srv844849.hstgr.cloud:4000/
curl -sk -o /dev/null -w "HTTP %{http_code}\n" https://srv844849.hstgr.cloud:4000/auth/login
```

---

## 7. Troubleshooting

### "Can't connect to https://srv844849.hstgr.cloud:4000"

```bash
# ¿La app está arriba?
sudo systemctl status training-web

# ¿Está bindeada a :5000?
sudo ss -tlnp | grep :5000

# ¿nginx OK?
sudo nginx -t && sudo systemctl reload nginx

# Logs del último arranque
sudo tail -50 /var/log/training-web.log
sudo journalctl -u training-web -n 100 --no-pager
```

### "training-web no arranca"

```bash
# Probar el comando directo (con la env del .env) y ver el error real
sudo -u training bash -c "cd /home/training/treini && set -a && . ./.env && set +a && \
  /home/training/treini/.venv/bin/python wsgi.py"
```

Causas comunes:
- `.env` con sintaxis inválida → corregir
- Postgres caído → `sudo systemctl status postgresql`
- `:5000` ocupado por otro proceso → `sudo lsof -i :5000`

### "El frontend se ve igual a antes del deploy"

- Verificá que el restart del service se hizo: `sudo systemctl restart training-web`
- ¿El navegador tiene cache? Forzá refresh con Cmd/Ctrl+Shift+R.

### "BD se rompió, hay que rollback"

```bash
# Encontrar el backup más reciente
ls -lh /tmp/training_*.sql.gz

# Restaurar (esto BORRA la BD actual y la reemplaza por el dump)
sudo -u postgres psql -c "DROP DATABASE training;"
sudo -u postgres psql -c "CREATE DATABASE training OWNER training;"
PGPASSWORD=$(grep ^DATABASE_URL= /home/training/treini/.env | sed -E 's|.*://training:([^@]*)@.*|\1|') \
  zcat /tmp/training_<timestamp>.sql.gz | \
  psql -h 127.0.0.1 -p 5432 -U training -d training
```

---

## 8. Cosas que NO están hechas todavía

- [ ] **Cron de backup diario** de la BD `training` (hoy solo hay backup de DobackSoft)
- [ ] **Sentry DSN** configurado (la dep está en `requirements.txt` pero no se usa)
- [ ] **Prometheus exporter** activo (idem)
- [ ] **CI/CD** (Joel)
- [ ] **Redis dedicado para Training** (hoy degradado a memoria)
- [ ] **HSTS / Talisman tuning** revisado (Talisman está activo en production por default)
- [ ] **Migración a Alembic** real (hoy `db.create_all()`)
- [ ] **Migración eventlet** (deprecated upstream)

---

## 9. Contactos / responsables

- **Infra del VPS** y deploy manual: Antonio
- **Backend + modelos + endpoints**: Jesús
- **Frontend / templates**: Alejandro
- **CI / tests / simulador**: Joel

> Comunicación con CMadrid: **solo Antonio.** Bajo NDA.

Para cambios sensibles del VPS (drop DB, cambios de nginx, systemd), **avisar a Antonio antes**.
