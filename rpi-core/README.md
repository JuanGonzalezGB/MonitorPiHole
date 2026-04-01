# rpi-core

Librería interna compartida para todos los proyectos de la Raspberry Pi.

## Instalación (una sola vez)

```bash
cd ~/rpi-projects
cp .env.example .env          # edita con tus valores reales
pip install -e rpi-core/
```

## Verificar que todo funciona

```bash
cd ~/rpi-projects/rpi-core
python check.py
```

## Módulos

| Módulo | Qué hace |
|---|---|
| `config.py` | Carga `.env` y expone constantes (URIs, colores, tamaños) |
| `db.py` | Cliente MongoDB singleton thread-safe |
| `devices.py` | Lectura de alias desde `scanner.devices` (solo lectura) |
| `widgets.py` | Componentes tkinter reutilizables para pantalla 480×320 |

## Uso en otros proyectos

```python
from rpicore.db import get_collection
from rpicore.devices import get_alias, resolve_aliases
from rpicore.widgets import StatCard, BarChart, TopBar, StatusDot
from rpicore import config
```

## Regla de oro

`devices.py` **nunca escribe** en `scanner.devices`.
El único proceso que escribe ahí es la app `scanner`.
Los demás proyectos solo leen — cero riesgo de corrupción.

## Estructura

```
rpi-projects/
├── .env                  ← un solo .env para todos los proyectos
├── rpi-core/
│   ├── rpicore/
│   │   ├── __init__.py
│   │   ├── config.py
│   │   ├── db.py
│   │   ├── devices.py
│   │   └── widgets.py
│   ├── check.py
│   └── setup.py
├── network-monitor/      ← próximo
└── pihole-monitor/       ← próximo
```
