# rasphole

Suite de monitoreo para Raspberry Pi con pantalla 3.5" (480×320).

## Proyectos

| Proyecto | Estado | Descripción |
|---|---|---|
| `rpi-core` | ✅ listo | Librería interna compartida |
| `network-monitor` | 🔄 collector listo | Escanea la red con arp-scan |
| `pihole-monitor` | ✅ listo | Monitor de Pi-hole con GUI |

## Servicios activos

```bash
sudo systemctl status network-collector
sudo systemctl status pihole-collector
sudo systemctl status pihole-sync
```

## Lanzar GUI

```bash
DISPLAY=:0 python3 ~/rasphole/Source/pihole-monitor/gui.py
```

## Documentación completa

Ver [MANUAL.md](MANUAL.md).
