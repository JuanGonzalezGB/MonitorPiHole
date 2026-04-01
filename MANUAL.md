# Rasphole — Manual técnico

## Visión general

Suite de microservicios para Raspberry Pi con pantalla 3.5" (480×320) que monitorea
la red local y el servidor DNS Pi-hole. Cada proyecto es independiente, comparte una
librería interna (`rpi-core`) y una instancia de MongoDB.

---

## Arquitectura

```
rpi-projects/
├── rpi-core/               ← librería interna compartida (pip install -e)
├── network-monitor/        ← escanea la red con arp-scan, persiste en Mongo
└── pihole-monitor/         ← monitorea Pi-hole v6, GUI en pantalla táctil
```

### Principios de diseño

- **Un solo escritor por colección**: cada colección de MongoDB tiene exactamente
  un proceso que escribe en ella. Los demás solo leen. Elimina riesgo de corrupción.
- **Microservicios ligeros**: cada proyecto corre como servicio systemd independiente.
  Si la GUI está cerrada, los collectors siguen acumulando datos.
- **Separación en 3 capas**: `collector` (obtiene datos), `repository` (lee Mongo),
  `gui` (pinta). La GUI nunca toca Mongo ni APIs externas directamente.
- **Base compartida**: `rpi-core` evita duplicar código entre proyectos.

### Flujo de datos completo

```
arp-scan (red local)
    │
    ▼  cada 2 min
network-monitor/collector.py
    └── escribe → scanner.scans  {mac, ip, vendor, last_seen}

Pi-hole API v6 (http://192.168.0.108/api)
    │
    ▼  cada 30s
pihole-monitor/collector.py
    └── escribe → pihole_db.stats       (snapshot con TTL 48h)
    └── escribe → pihole_db.history     (buckets horarios)
    └── escribe → pihole_db.top_blocked (doc único)
    └── escribe → pihole_db.top_clients (doc único)

scanner.dispositivos {mac, name}  ← escrito por app scanner (sin cambios)
    +
scanner.scans        {mac, ip}    ← escrito por network-monitor/collector.py
    │
    ▼  cada 5 min
pihole-monitor/sync.py
    └── cruza mac→name + mac→ip
    └── registra en Pi-hole /api/clients con comment=name

pihole_db (Mongo)
    │
    ▼
pihole-monitor/repository.py
    │
    ▼
pihole-monitor/gui.py  (tkinter, pantalla 480×320)
```

---

## Base de datos MongoDB (192.168.0.108:27017)

### scanner (db existente, no modificada en su estructura original)

| Colección | Dueño | Contenido |
|---|---|---|
| `dispositivos` | app scanner | `{mac, name}` — dispositivos con nombre asignado |
| `scans` | network-monitor/collector | `{mac, ip, vendor, ping_ms, last_seen, first_seen}` |

### pihole_db (db nueva)

| Colección | TTL | Contenido |
|---|---|---|
| `stats` | 48h | snapshot cada 30s de Pi-hole |
| `history` | permanente | bucket por hora (total, blocked, cached, forwarded) |
| `top_blocked` | — | documento único reemplazado cada 5min |
| `top_clients` | — | documento único reemplazado cada 30s |

---

## rpi-core

Librería interna instalada en modo editable (`pip install -e rpi-core/`).

### Módulos

**`config.py`** — carga `.env` buscándolo hacia arriba en el árbol de carpetas.
Expone constantes: `MONGO_URI`, `DB_SCANNER`, `DB_PIHOLE`, `PIHOLE_HOST`,
`PIHOLE_PASSWORD`, `COLLECTION_DEVICES`, `SCREEN_W/H`, `REFRESH_MS`, colores.

**`db.py`** — cliente MongoDB singleton thread-safe.
- `get_client()` → `MongoClient` (singleton)
- `get_collection(db, col)` → `Collection`
- `ping()` → `bool`
- `close()`

**`devices.py`** — lectura de `scanner.dispositivos`. NUNCA escribe.
- `get_name(mac)` → nombre o MAC si no tiene nombre
- `get_device(mac)` → documento completo o None
- `list_devices()` → lista de `{mac, name}`
- `resolve_names([mac, ...])` → `{mac: name}` en una sola query

**`widgets.py`** — componentes tkinter para pantalla 480×320, tema oscuro.
- `StatCard(parent, label, color)` — tarjeta con valor grande
- `BarChart(parent, width, height)` — gráfica de barras apiladas sobre Canvas
- `DeviceList(parent)` — lista compacta primary/secondary
- `StatusDot(parent, label)` — indicador verde/rojo
- `TopBar(parent, title)` — barra superior con timestamp

### Variables de entorno (.env)

```env
MONGO_URI=mongodb://192.168.0.108:27017
MONGO_TIMEOUT_MS=3000
DB_SCANNER=scanner
DB_PIHOLE=pihole_db
COLLECTION_DEVICES=dispositivos
PIHOLE_HOST=192.168.0.108
PIHOLE_PORT=80
PIHOLE_PASSWORD=tu_password
NETWORK_SUBNET=192.168.0.0/24
SCAN_INTERVAL_S=120
SCREEN_W=480
SCREEN_H=320
REFRESH_MS=30000
```

---

## network-monitor

### collector.py
Corre `scan_network.sh` (arp-scan) cada `SCAN_INTERVAL_S` segundos y guarda
en `scanner.scans`. Usa upsert por MAC — siempre refleja el estado más reciente.

**Notas importantes:**
- El servicio systemd corre como `root` porque `arp-scan` requiere privilegios.
- El `PYTHONPATH` debe incluir la ruta de `rpi-core` y de los paquetes del usuario.

### scan_network.sh
Script bash que ejecuta `arp-scan --localnet`, detecta la interfaz activa
automáticamente y devuelve JSON con `{ip, mac, vendor, ping_ms}`.

### Servicio systemd: network-collector.service

```ini
[Unit]
Description=Network monitor collector (arp-scan)
After=network-online.target mongod.service

[Service]
Type=simple
User=root
WorkingDirectory=/home/username/rasphole/Source/network-monitor
ExecStart=/usr/bin/python3 /home/username/rasphole/Source/network-monitor/collector.py
Environment=PYTHONPATH=/home/username/rasphole/Source/rpi-core:/home/username/.local/lib/python3.13/site-packages
Restart=always
RestartSec=15
```

---

## pihole-monitor

### collector.py (Pi-hole API v6)
Obtiene datos de Pi-hole cada 30s. Maneja sesión v6 automáticamente:
- Autentica con `POST /api/auth` usando `PIHOLE_PASSWORD`
- El `sid` dura 1800s — renueva con 60s de margen antes de expirar
- Si la API no responde, reintenta en el siguiente ciclo sin caerse

**Endpoints consumidos:**
- `GET /api/stats/summary` — cada ciclo
- `GET /api/stats/top_clients?count=10` — cada ciclo
- `GET /api/stats/top_domains?blocked=true&count=10` — cada 5 min
- `GET /api/history` — cada 5 min

### repository.py
Única fuente de datos para la GUI. Funciones:
- `get_latest_stats()` — snapshot más reciente
- `get_history_24h()` — 24 buckets horarios, rellena con 0 los que faltan
- `get_top_blocked(limit)` — dominios más bloqueados
- `get_top_clients(limit)` — clientes más activos con IP
- `get_last_updated()` — "hace 8s", "hace 2m"

### sync.py
Sincroniza nombres de dispositivos desde MongoDB hacia Pi-hole.

**Flujo:**
1. Lee `scanner.dispositivos` → `{mac: name}`
2. Lee `scanner.scans` → `{mac: ip}` (puente mac→ip)
3. Cruza ambos → `{ip: name}`
4. Compara con clientes actuales en Pi-hole (`GET /api/clients`)
5. Agrega nuevos (`POST /api/clients`) o actualiza nombres cambiados (`PUT /api/clients/{id}`)

**Modos:**
- `python sync.py` — corre una vez y sale
- `python sync.py --watch` — loop cada 5 minutos

**Limitación conocida:** Solo sincroniza dispositivos que aparecen en `scanner.scans`
(es decir, que fueron vistos en un scan reciente). Dispositivos apagados se sincronizan
la próxima vez que el network-collector los detecte.

### gui.py
Interfaz tkinter 480×280. Se refresca cada `REFRESH_MS` (30s por defecto).
Llama exclusivamente a `repository.py`.

Layout:
- TopBar con título y timestamp
- 4 StatCards: queries, bloqueadas, % bloqueado, dominios en lista
- Columna izquierda: top dominios bloqueados + clientes activos (con scroll táctil)
- Columna derecha: gráfica de barras 24h (permitidas vs bloqueadas)
- Footer: StatusDot (verde=activo) + timestamp de última actualización

### Servicios systemd

**pihole-collector.service:**
```ini
[Service]
User=username
WorkingDirectory=/home/username/rasphole/Source/pihole-monitor
ExecStart=/usr/bin/python3 /home/username/rasphole/Source/pihole-monitor/collector.py
Environment=PYTHONPATH=/home/username/rasphole/Source/rpi-core:/home/username/.local/lib/python3.13/site-packages
```

**pihole-sync.service:**
```ini
[Service]
User=username
WorkingDirectory=/home/username/rasphole/Source/pihole-monitor
ExecStart=/usr/bin/python3 /home/username/rasphole/Source/pihole-monitor/sync.py --watch
Environment=PYTHONPATH=/home/username/rasphole/Source/rpi-core:/home/username/.local/lib/python3.13/site-packages
```

---

## Instalación desde cero

```bash
# 1. Instalar rpi-core
cd ~/rasphole/Source
pip3 install -e rpi-core/ --break-system-packages

# 2. Configurar variables de entorno
cp rpi-core/.env.example .env
nano .env   # ajustar PIHOLE_PASSWORD y demás valores

# 3. Verificar conexión
python3 rpi-core/check.py

# 4. Instalar servicios systemd
sudo cp network-monitor/network-collector.service /etc/systemd/system/
sudo cp pihole-monitor/pihole-collector.service   /etc/systemd/system/
sudo cp pihole-monitor/pihole-sync.service        /etc/systemd/system/

# Editar cada service file con rutas y PYTHONPATH correctos
sudo nano /etc/systemd/system/network-collector.service
sudo nano /etc/systemd/system/pihole-collector.service
sudo nano /etc/systemd/system/pihole-sync.service

sudo systemctl daemon-reload
sudo systemctl enable --now network-collector pihole-collector pihole-sync

# 5. Esperar ~2 min a que el network-collector llene scanner.scans
# Verificar:
mongosh scanner --eval "db.scans.find().pretty()"

# 6. Correr sync una vez para registrar dispositivos en Pi-hole
python3 ~/rasphole/Source/pihole-monitor/sync.py

# 7. Lanzar GUI
DISPLAY=:0 python3 ~/rasphole/Source/pihole-monitor/gui.py
```

---

## Diagnóstico rápido

```bash
# Ver logs de cada servicio
journalctl -u network-collector -f
journalctl -u pihole-collector  -f
journalctl -u pihole-sync       -f

# Verificar datos en Mongo
mongosh scanner  --eval "db.scans.find().pretty()"
mongosh pihole_db --eval "db.stats.findOne()"
mongosh pihole_db --eval "db.top_clients.findOne()"

# Probar API de Pi-hole manualmente
curl -s -X POST http://192.168.0.108/api/auth \
  -H "Content-Type: application/json" \
  -d '{"password":"TU_PASSWORD"}' | python3 -m json.tool
```

---

## Estado actual

- **Pi-hole bloqueando anuncios** ✅ — DHCP activado en Pi-hole, desactivado en router.
  Todos los dispositivos de la red reciben `192.168.0.108` como DNS automáticamente,
  incluyendo invitados. YouTube y popups requieren uBlock Origin en el navegador.
- **Nombres en clientes activos** ✅ — la GUI muestra el nombre de `scanner.dispositivos`
  en lugar de la IP. Flujo: `ip → mac (scanner.scans) → name (scanner.dispositivos)`.
- **IP estática en Raspberry** ✅ — configurada via NetworkManager, independiente de DHCP.
- **Reservas DHCP en Pi-hole** ✅ — RaspberryPi `.108` y MyPC `.101` con lease infinito.

## Pendiente

- **Autoarranque de la GUI** al iniciar la Raspberry: configurar con `@reboot` en
  crontab o un servicio systemd con `DISPLAY=:0`
- **GUI del network-monitor**: no aplica — ya existe una app funcional desarrollada
  en sesiones anteriores
