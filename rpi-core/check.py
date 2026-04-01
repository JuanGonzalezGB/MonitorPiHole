"""
rpi-core · check.py
Verifica que la instalación y conexión a Mongo funcionan correctamente.
Correr desde la Raspberry con:  python check.py
"""

import sys

print("── rpi-core check ──────────────────────────────")

# 1. Imports
try:
    from rpicore import config
    from rpicore.db import ping, get_collection
    from rpicore.devices import list_devices
    print("✓ imports OK")
except ImportError as e:
    print(f"✗ import error: {e}")
    print("  Asegúrate de haber corrido: pip install -e rpi-core/")
    sys.exit(1)

# 2. Config
print(f"✓ MONGO_URI   = {config.MONGO_URI}")
print(f"✓ DB_SCANNER  = {config.DB_SCANNER}")
print(f"✓ DB_PIHOLE   = {config.DB_PIHOLE}")
print(f"✓ PIHOLE_HOST = {config.PIHOLE_HOST}")
print(f"✓ SCREEN      = {config.SCREEN_W}×{config.SCREEN_H}")

# 3. Conexión Mongo
print("\nConectando a MongoDB...")
if ping():
    print("✓ Mongo OK")
else:
    print("✗ Mongo no responde — revisa que esté corriendo en 192.168.0.108:27017")
    sys.exit(1)

# 4. Leer devices
print("\nLeyendo scanner.dispositivos...")
try:
    devices = list_devices()
    print(f"✓ {len(devices)} dispositivos encontrados")
    for d in devices[:3]:
        name = d.get("name") or "(sin nombre)"
        print(f"  {d.get('mac', '?'):20}  {name}")
    if len(devices) > 3:
        print(f"  ... y {len(devices) - 3} más")
except Exception as e:
    print(f"✗ Error leyendo devices: {e}")

print("\n── todo OK — rpi-core listo para usar ──────────")
