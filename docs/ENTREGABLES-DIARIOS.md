# Sistema de entregables diarios automáticos

> Cómo replicar el flujo de informe consolidado del equipo (Slack + Drive + GitHub → PDF al Drive),
> verificado end-to-end el 2026-04-29.
>
> **Audiencia**: cualquier miembro del equipo (Jesús, Alejandro, Joel) que quiera correr esto en su
> propia mac, o cualquier persona que adapte el flujo a otro proyecto.

---

## 0. ¿Qué hace el sistema?

Cada día a una hora fija (por defecto **14:00 hora Madrid**), un job en macOS:

1. **Lee los commits** del repositorio del proyecto del día (vía `git log` local).
2. **Lee mensajes** de un canal de Slack (vía bot token).
3. **Descarga archivos** que el equipo subió a una carpeta del Drive el día (vía OAuth).
4. **Reconoce uploads "proxy"** (cuando alguien sube por otro porque el dueño no tiene permisos
   todavía — ej. PM que sube `entregable_jesus_29_04.pdf` por Jesús).
5. **Traduce** los commits técnicos a tono ejecutivo no técnico (sin nombres de archivos, classes,
   o jerga técnica), con voz pasiva impersonal.
6. **Consolida** todo en un Markdown estructurado por persona del equipo.
7. **Genera un PDF** con CSS institucional (cabecera, pie con paginación, branding del cliente)
   usando WeasyPrint.
8. **Sube el PDF** automáticamente a una carpeta destino del Drive vía OAuth.

**Tiempo total medido**: ~19 segundos por ejecución (con 22 commits, 33 mensajes Slack, 1 archivo
descargado del Drive, PDF de 37 KB).

---

## 1. Arquitectura

```
┌──────────────────────┐       ┌─────────────────────────────┐
│ launchd (macOS)      │ 14:00 │  generate_team_report.py    │
│ com.cmadrid.training │──────▶│  (entry point)              │
│ -entregable.plist    │       └──────┬──────────────────────┘
└──────────────────────┘              │
                                      ├─▶ git log local repo
                                      │
                                      ├─▶ slack_reader.py
                                      │   └─▶ Slack API (xoxb token)
                                      │
                                      ├─▶ drive_client.py (read)
                                      │   └─▶ Google Drive API (OAuth)
                                      │
                                      ├─▶ markdown.markdown(...)
                                      │
                                      ├─▶ WeasyPrint(html, css)
                                      │
                                      └─▶ drive_client.py (upload)
                                          └─▶ Google Drive API
```

**Ningún componente del cron depende de la sesión interactiva del agente** (esta sesión de Claude
Code, MCPs, etc.). Todo corre standalone con tokens locales.

---

## 2. Componentes (en el repo)

| Archivo | Líneas | Función |
|---|---|---|
| `scripts/generate_team_report.py` | ~270 | Orquestador principal. Configurable. |
| `scripts/slack_reader.py` | ~100 | Lee canal de Slack del día con bot token. |
| `scripts/drive_client.py` | ~140 | OAuth client para listar/descargar/subir archivos del Drive. |

Y configuración local (NO en el repo, queda en cada mac):

- `~/Library/LaunchAgents/com.cmadrid.training-entregable.plist` — el cron de macOS.
- `~/.cmadrid-training/slack.token` — Bot token Slack (`xoxb-...`).
- `~/.cmadrid-training/credentials.json` — OAuth client de Google Cloud.
- `~/.cmadrid-training/token.json` — token de acceso refrescable (se crea automáticamente).
- `~/Desktop/entregables/equipo/` — output local (también el cron lo sube al Drive).
- `~/Desktop/entregables/team_report.log` — log de cada ejecución.

---

## 3. Pre-requisitos

- macOS (para `launchd`). Si usás Linux, equivale a un `cron` o `systemd timer`.
- Python 3.12 + venv del proyecto (`~/repos/training/.venv`).
- Cuenta de Google con acceso al Drive donde se sube el output.
- Permisos de admin del workspace de Slack (o permiso del owner para crear apps).
- Acceso al repo de GitHub (`gh auth login` si querés clone via SSH, no estrictamente necesario para este flow).

Dependencias Python (instaladas en el venv):

```bash
pip install markdown weasyprint pdfplumber slack_sdk google-api-python-client google-auth-httplib2 google-auth-oauthlib
```

---

## 4. Setup paso a paso

### 4.1. Clonar el repo y armar el venv

```bash
git clone https://github.com/cosigein/training ~/repos/training
cd ~/repos/training
python3.12 -m venv .venv
.venv/bin/pip install markdown weasyprint pdfplumber slack_sdk google-api-python-client google-auth-httplib2 google-auth-oauthlib
```

### 4.2. Crear directorio de configuración local

```bash
mkdir -p ~/.cmadrid-training
chmod 700 ~/.cmadrid-training
```

### 4.3. Setup token de Slack

Tutorial detallado: ver `~/Desktop/entregables/SETUP-SLACK.md` (ya está en disco si seguiste la
configuración inicial; si no, los pasos están abajo).

Resumen:
1. https://api.slack.com/apps → "Create New App" → "From scratch" → workspace destino.
2. **OAuth & Permissions** → "Bot Token Scopes" → agregar:
   - `channels:history`
   - `channels:read`
   - `groups:history`
   - `users:read`
3. Si ves la opción **"Token Rotation"**, **DESACTIVALA** (genera tokens `xoxe-` que no
   sirven para este flujo simple).
4. **Install to Workspace** → copiar el **Bot User OAuth Token** (empieza con `xoxb-`).
5. **Invitar al bot al canal**: en Slack, en el canal destino, escribir
   `/invite @<nombre-de-tu-bot>` (en nuestro caso fue `/invite @demo_app`).
6. Guardar el token:
   ```bash
   echo "xoxb-tu-token" > ~/.cmadrid-training/slack.token
   chmod 600 ~/.cmadrid-training/slack.token
   ```
7. Verificar:
   ```bash
   cd ~/repos/training
   .venv/bin/python scripts/slack_reader.py <CHANNEL_ID> <YYYY-MM-DD>
   ```

**Cómo encontrar el `CHANNEL_ID`**: en la URL del canal en el cliente web de Slack, es lo que va
después de `/archives/` (ej. `https://workspace.slack.com/archives/C0AV8A77E9M` → ID es
`C0AV8A77E9M`).

**Cómo confirmar el nombre del bot**: si Slack te dice "usuario inválido" al hacer `/invite`,
correr:
```bash
TOKEN=$(cat ~/.cmadrid-training/slack.token)
curl -sX POST "https://slack.com/api/auth.test" -H "Authorization: Bearer $TOKEN" \
  -H "Content-type: application/x-www-form-urlencoded" | python3 -m json.tool
```
El campo `user` del response es el nombre real del bot.

### 4.4. Setup OAuth de Google Drive

Tutorial detallado: `~/Desktop/entregables/SETUP-DRIVE.md`. Resumen:

1. https://console.cloud.google.com → crear proyecto.
2. **APIs & Services → Library** → buscar "Google Drive API" → **Enable**.
3. **APIs & Services → OAuth consent screen** → External → datos de la app → agregar email del
   usuario como **Test user** (porque la app queda en modo "Testing", no necesita publicación).
4. **APIs & Services → Credentials** → "+ CREATE CREDENTIALS" → "OAuth client ID" → **Desktop app**
   → CREATE → click **DOWNLOAD JSON**.
5. Mover el JSON descargado:
   ```bash
   mv ~/Downloads/client_secret_*.json ~/.cmadrid-training/credentials.json
   chmod 600 ~/.cmadrid-training/credentials.json
   ```
6. Primera autorización (abre browser):
   ```bash
   .venv/bin/python scripts/drive_client.py <FOLDER_ID> <YYYY-MM-DD>
   ```
   - Login con la cuenta que es **dueña** de la carpeta del Drive y **Test user** en la consent
     screen.
   - Pantalla de warning "Google hasn't verified this app" → "Advanced" → "Go to ... (unsafe)" — es
     seguro porque es tu propia app.
   - **Allow** los 2 permisos.
7. El `token.json` se crea automáticamente y se refresca solo durante 6 meses.

**Cómo encontrar el `FOLDER_ID`**: en la URL de la carpeta del Drive,
`https://drive.google.com/drive/folders/<FOLDER_ID>`.

### 4.5. Configurar el script para tu proyecto

Editar `scripts/generate_team_report.py` y ajustar:

```python
# Línea ~50
REPO_PATH = Path("/Users/<TU_USUARIO>/repos/<TU_REPO>")  # path local del repo

# Línea ~54
SLACK_CHANNEL_ID = "<TU_CANAL_SLACK_ID>"
DRIVE_TEAM_FOLDER = "<CARPETA_DRIVE_GENERAL>"   # donde el equipo sube sus entregables
DRIVE_EQUIPO_FOLDER = "<CARPETA_DRIVE_OUTPUT>"  # donde se sube el PDF consolidado
ANTONIO_EMAIL = "<TU_EMAIL>"                    # tu email — se excluye al listar archivos del Drive

# Líneas ~30-45 — mapeo de autores GitHub → personas humanas
TEAM_MAPPING = {
    "<email1>": "<Persona 1 (Rol 1)>",
    "<email2>": "<Persona 2 (Rol 2)>",
    # ...
}

# Líneas ~60-65 — mapeo email del Drive → key (jesus, alejandro, joel, etc.)
DRIVE_EMAIL_TO_KEY = {
    "<email_drive_jesus>": "jesus",
    "<email_drive_alejandro>": "alejandro",
    "<email_drive_joel>": "joel",
}

# Líneas ~70-77 — patrón de "proxy uploader" (cuando un PM sube por otros)
PROXY_UPLOADER_EMAIL = "<email_pm>"
```

### 4.6. Setup del cron (launchd)

Crear el plist `~/Library/LaunchAgents/com.<TU>.training-entregable.plist` con este contenido,
ajustando paths:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.cmadrid.training-entregable</string>

    <key>ProgramArguments</key>
    <array>
        <string>/Users/<TU>/repos/training/.venv/bin/python</string>
        <string>/Users/<TU>/repos/training/scripts/generate_team_report.py</string>
    </array>

    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>14</integer>
        <key>Minute</key>
        <integer>0</integer>
    </dict>

    <key>WorkingDirectory</key>
    <string>/Users/<TU>/repos/training</string>

    <key>StandardOutPath</key>
    <string>/Users/<TU>/Desktop/entregables/team_report.stdout.log</string>

    <key>StandardErrorPath</key>
    <string>/Users/<TU>/Desktop/entregables/team_report.stderr.log</string>

    <key>RunAtLoad</key>
    <false/>

    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin</string>
        <key>LANG</key>
        <string>es_ES.UTF-8</string>
    </dict>
</dict>
</plist>
```

Cargar:
```bash
launchctl load ~/Library/LaunchAgents/com.<TU>.training-entregable.plist
launchctl list | grep training-entregable   # ✓ aparece listado
```

### 4.7. Probar end-to-end

```bash
launchctl kickstart -p gui/$(id -u)/com.<TU>.training-entregable
sleep 20
tail -15 ~/Desktop/entregables/team_report.log
```

Debería terminar en `✅ Informe generado en .../equipo-YYYY-MM-DD.pdf` con todos los pasos en
verde.

---

## 5. Operación diaria

A partir del setup, **no toques nada**. Cada día a las 14:00 hora Madrid:

1. El cron dispara el script.
2. El script lee Slack + Drive + commits.
3. Genera el PDF consolidado.
4. Lo sube al Drive automáticamente.

**Si algún día querés revisar manualmente**:
```bash
.venv/bin/python scripts/generate_team_report.py            # día actual
.venv/bin/python scripts/generate_team_report.py 2026-05-04 # día concreto
```

**Si algún miembro NO subió nada ese día**: la sección correspondiente del PDF dirá "Sin
aportaciones de código registradas hoy" y "Sin aporte directo registrado". El PDF se genera igual.

---

## 6. Verificación end-to-end (registro real)

Verificado el 2026-04-29 a las 16:15:

| Paso | Inicio | Duración |
|---|---|---|
| Disparo cron | 16:15:02 | — |
| `git log` 22 commits encontrados | 16:15:06 | 4s |
| Slack: 33 líneas leídas del canal `#dobacksoft-training` | 16:15:10 | 4s |
| Drive: descargado `entregable_jesus_29_04.pdf` de Jesús | 16:15:16 | 6s |
| Generación de PDF (WeasyPrint) | 16:15:19 | 3s |
| Subida al Drive carpeta `equipo` | 16:15:21 | 2s |
| **Total** | — | **19s** |

Output: PDF de 37 KB, ID Drive `1NgzZ74pORpyhVLJxzhXJdIe4i9UkbL8g`.

---

## 7. Cómo el script "traduce" commits a tono ejecutivo

El módulo `commits_to_executive_paragraph()` aplica reemplazos regex sobre los mensajes:

| Antes (técnico) | Después (ejecutivo) |
|---|---|
| `auth/routes.py` | "el módulo de autenticación" |
| `RBAC` | "sistema de permisos" |
| `JWT` | "tokens de sesión" |
| `CSRF` | "protección frente a falsificación de solicitudes" |
| `Celery` | "tareas en segundo plano" |
| `Redis` | "servicio de cache" |
| `nginx` | "servidor web" |
| `systemd` | "servicio de arranque automático" |
| `VPS` | "servidor de producción" |
| `refactor` | "reorganización" |
| `merge conflicts` | "integración del trabajo del equipo" |
| `feat(area):` / `fix(area):` | (prefijo eliminado) |
| `PR #123` / `(#123)` | (eliminado) |

**Limitación conocida**: la regex `manager` reemplaza a "el portal del manager" indiscriminadamente,
incluso dentro de `MANAGER`/`SUPER_ADMIN`. Resultado: queda raro en algunos casos. Si te molesta,
ajustar el regex con `\b` o lookbehind.

---

## 8. Troubleshooting

| Síntoma | Causa probable | Fix |
|---|---|---|
| `(sin token configurado o slack_sdk faltante)` | Falta `~/.cmadrid-training/slack.token` o no empieza con `xoxb-` | Re-ejecutar setup Slack §4.3 |
| `(no se pudo leer Slack: not_in_channel)` | Bot no fue invitado al canal | `/invite @<bot>` en el canal en Slack |
| `(no se pudo leer Slack: missing_scope)` | Faltan scopes en la app de Slack | Agregar scopes faltantes y **Reinstall** la app |
| `(sin archivos del equipo hoy o sin credenciales)` | Falta `credentials.json` o no hay archivos del día | Ver §4.4 |
| `Access blocked: ... has not completed the Google verification process` | El email no está en "Test users" del consent screen | Agregar como Test user en Google Cloud Console |
| El cron no ejecuta a las 14:00 | macOS dormida o el plist no está cargado | `launchctl list | grep training-entregable` y `launchctl kickstart -p ...` para forzar |
| WeasyPrint error `cannot load library 'libpango'` | Falta dep del sistema | `brew install pango` |
| Tokens caducados (`refresh_token` falla) | Pasaron 6 meses + cuenta inactiva | Borrar `token.json` y re-autorizar |

Logs útiles:
```bash
tail -50 ~/Desktop/entregables/team_report.log         # log estructurado
tail -50 ~/Desktop/entregables/team_report.stdout.log  # stdout del cron
tail -50 ~/Desktop/entregables/team_report.stderr.log  # errores del cron
```

---

## 9. Personalización para OTROS proyectos

Para adaptar este flow a otro proyecto cliente:

1. **Renombrar variables** en `generate_team_report.py`:
   - `SLACK_CHANNEL_ID` → ID del nuevo canal.
   - `DRIVE_TEAM_FOLDER`, `DRIVE_EQUIPO_FOLDER` → IDs de las nuevas carpetas.
   - `TEAM_MAPPING` → equipo del nuevo proyecto.
2. **Renombrar el plist**: `com.<cliente>.<proyecto>-entregable.plist`.
3. **Tokens separados**: usar otro directorio (`~/.<cliente>/`) y ajustar paths en los scripts.
4. **CSS institucional**: editar `CSS_INSTITUCIONAL` en `generate_team_report.py` con cabecera/pie
   del nuevo cliente.

Si tu organización tiene varios proyectos en paralelo, podés tener múltiples cron jobs (uno por
proyecto) con sus propios scripts y tokens. No se pisan.

---

## 10. Seguridad

- **Tokens en disco con permisos `600`**: solo el usuario puede leerlos. Si alguien tiene acceso
  root al equipo, pueden leerlos — usar FileVault.
- **NUNCA pegar tokens en chat (Slack, Discord, ChatGPT, etc.)**: queda en logs y memoria. Si pasa,
  rotarlos inmediatamente en api.slack.com / Google Cloud Console.
- **El Bot de Slack tiene scopes acotados**: solo puede leer mensajes/canales. NO puede escribir
  ni borrar.
- **La OAuth Drive es de tu usuario**: el script tiene los mismos permisos que tu cuenta tiene
  sobre las carpetas. Si revocás la app desde tu cuenta Google, el cron deja de funcionar.

Para revocar todo el acceso (en caso de equipo robado o decisión de salir):
```bash
# Slack: api.slack.com/apps → tu app → OAuth & Permissions → Revoke Tokens
# Drive: myaccount.google.com/permissions → revocar la app
# Local:
rm -rf ~/.cmadrid-training
launchctl unload ~/Library/LaunchAgents/com.<TU>.training-entregable.plist
rm ~/Library/LaunchAgents/com.<TU>.training-entregable.plist
```

---

## 11. Costo

- Slack API: gratis.
- Google Drive API: gratis (cuotas: 1.000 millones de requests/día por proyecto).
- Anthropic Cloud / Claude Code: NO necesario para el cron (solo se usó al armar el sistema).
- WeasyPrint, Python, launchd: gratis.

**Costo recurrente: $0**.

---

## 12. Limitaciones conocidas

- **Mac apagada/dormida a las 14:00**: el job se acumula y se ejecuta apenas la mac vuelve. Si la
  mac está dormida toda la jornada, el reporte NO se hace.
- **Mensajes Slack con archivos**: el script lee el TEXTO del mensaje, NO descarga adjuntos
  (PDF, imágenes). Si un miembro pega un PDF en Slack como entregable, solo se captura el texto del
  mensaje. Para descargar adjuntos, extender `slack_reader.py` con `client.files_info(file_id)` +
  download.
- **Idiomas**: el formato de fecha está hardcodeado en español (`DIAS`, `MESES`). Si querés
  cambiar idioma, editar esos arrays.
- **Zona horaria**: hardcodeada a Europe/Madrid CEST (UTC+2). Si el sprint pasa a CET (UTC+1) en
  octubre, ajustar el offset en `_day_to_unix_range()` y `list_files_in_folder()`.
- **`refresh_token` Google**: caduca a los 6 meses si la cuenta está inactiva. Re-autorizar.

---

## 13. Cambios y mejoras futuras

| Idea | Esfuerzo | Beneficio |
|---|---|---|
| Descargar adjuntos de Slack | 30 min | Captar PDFs que Joel publica directo al canal |
| Notificar por Slack cuando termina | 10 min | El equipo se entera del informe sin chequear el Drive |
| Soportar múltiples canales | 30 min | Ej. canal por área (frontend, backend) |
| Detectar zonas horarias auto | 30 min | DST sin intervención |
| Resumen semanal (lunes 09:00) | 1h | Roll-up de los 5 entregables de la semana |
| Métricas de productividad | 2h | Histograma de commits/día por persona, gráficos |
| Migrar a Linux/Windows | 1-2h | Reemplazar `launchd` con `cron` o Task Scheduler |
| CI con GitHub Actions | 1h | Que el cron corra en GitHub en vez de en una mac |

---

## 14. Mantenimiento

- **Una vez por mes**: revisar `team_report.log` por errores no atendidos.
- **Cada vez que cambia el equipo**: actualizar `TEAM_MAPPING` y `DRIVE_EMAIL_TO_KEY`.
- **Cada vez que se rota un token**: regenerar y reemplazar el archivo en `~/.cmadrid-training/`.
- **Una vez por sprint**: confirmar que el Drive folder destino sigue existiendo.

---

## Apéndice A — Estructura del PDF generado

El PDF tiene esta estructura fija, garantizada por el script:

```
┌─────────────────────────────────────────────────────────┐
│  Training · CMadrid · Informe del equipo  [encabezado]  │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Informe Diario del Equipo                              │
│  Miércoles, 29 de abril de 2026                         │
│                                                         │
│  Proyecto: **Training — Sistema de evaluación...**      │
│                                                         │
│  ──────────                                             │
│                                                         │
│  ## Estado del día                                      │
│  [introducción genérica autogenerada]                   │
│                                                         │
│  ## Avance por miembro del equipo                       │
│                                                         │
│  ### Antonio Hermoso (Director técnico)                 │
│  Trabajos del día:                                      │
│   - [commit 1 traducido]                                │
│   - [commit 2 traducido]                                │
│  ...                                                    │
│                                                         │
│  ### Jesús (Backend)                                    │
│  [commits + texto del archivo entregable_jesus_*.pdf]   │
│                                                         │
│  ### Alejandro (Frontend)                               │
│  [commits o "Sin aportaciones..."]                      │
│                                                         │
│  ### Joel (QA y simulador)                              │
│  [commits + resumen de Slack del día]                   │
│                                                         │
│  ──────────                                             │
│                                                         │
│  _Informe generado automáticamente..._                  │
│                                                         │
├─────────────────────────────────────────────────────────┤
│   Página 1 de N        Confidencial — Bomberos CMadrid  │
│                                          [pie de página]│
└─────────────────────────────────────────────────────────┘
```

Tipografía: serif para cuerpo (Georgia), sans-serif para títulos. Color principal: azul
institucional `#1e3a8a`. Texto justificado.

---

**Última actualización**: 2026-04-29.
**Verificado funcionando**: 2026-04-29 16:15 (ver §6).
**Autor del setup inicial**: Antonio Hermoso.
