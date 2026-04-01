# pihole-monitor

Monitor de Pi-hole para pantalla 480×320 en Raspberry Pi.

## Estructura

```
pihole-monitor/
├── collector.py              ← proceso independiente (systemd)
├── repository.py             ← toda la lógica de lectura de Mongo
├── gui.py                    ← interfaz tkinter
├── pihole-collector.service  ← unit file para systemd
└── requirements.txt
```

## Instalación

```bash
# 1. Instalar dependencias (rpi-core ya debe estar instalado)
cd ~/rpi-projects/pihole-monitor
pip install -r requirements.txt

# 2. Instalar el servicio del collector
sudo cp pihole-collector.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable pihole-collector
sudo systemctl start pihole-collector

# 3. Verificar que el collector está corriendo y escribiendo datos
sudo journalctl -u pihole-collector -f

# 4. Lanzar la GUI (en la pantalla de la Pi)
python gui.py
```

## Flujo de datos

```
Pi-hole API
    │
    ▼  cada 30s
collector.py
    │
    ▼  escribe
pihole_db (Mongo)
  ├── stats        ← snapshots con TTL 48h
  ├── history      ← buckets horarios
  ├── top_blocked  ← documento único, reemplazado cada 5min
  └── top_clients  ← documento único, reemplazado cada 30s
    │
    ▼  solo lee
repository.py
    │
    ▼
gui.py  ←  también lee scanner.devices para alias (vía rpi-core)
```

## Logs del collector

```bash
sudo journalctl -u pihole-collector -f
# ejemplo:
# 14:32:01 [collector] INFO snapshot guardado — queries: 47821 bloqueadas: 12304 (25.7%)
```

## Colecciones en Mongo

| Colección | TTL | Contenido |
|---|---|---|
| `pihole_db.stats` | 48h | snapshot cada 30s |
| `pihole_db.history` | permanente | bucket por hora |
| `pihole_db.top_blocked` | — | doc único, reemplazado |
| `pihole_db.top_clients` | — | doc único, reemplazado |
