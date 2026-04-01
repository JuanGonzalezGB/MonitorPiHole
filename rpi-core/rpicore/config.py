"""
rpi-core · config.py
Carga variables de entorno desde .env y expone constantes globales.
Todos los proyectos importan de aquí — nunca hardcodean valores.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Busca .env subiendo hasta encontrarlo (rpi-projects/.env)
_env_path = Path(__file__).resolve()
for _ in range(6):
    candidate = _env_path.parent / ".env"
    if candidate.exists():
        load_dotenv(candidate)
        break
    _env_path = _env_path.parent

# ── Mongo ────────────────────────────────────────────────────────────────────
MONGO_URI: str = os.getenv("MONGO_URI", "mongodb://192.168.0.108:27017")
MONGO_TIMEOUT_MS: int = int(os.getenv("MONGO_TIMEOUT_MS", "3000"))

# ── Base de datos por proyecto ────────────────────────────────────────────────
DB_SCANNER:  str = os.getenv("DB_SCANNER",  "scanner")   # dueño de dispositivos
DB_PIHOLE:   str = os.getenv("DB_PIHOLE",   "pihole_db")

# ── Colecciones (ajustar si tu app usa nombres distintos) ─────────────────────
COLLECTION_DEVICES: str = os.getenv("COLLECTION_DEVICES", "dispositivos")

# ── Red ───────────────────────────────────────────────────────────────────────
PIHOLE_HOST: str = os.getenv("PIHOLE_HOST", "192.168.0.108")
PIHOLE_PORT: int = int(os.getenv("PIHOLE_PORT", "80"))

# ── GUI ───────────────────────────────────────────────────────────────────────
SCREEN_W: int = int(os.getenv("SCREEN_W", "480"))
SCREEN_H: int = int(os.getenv("SCREEN_H", "320"))
REFRESH_MS: int = int(os.getenv("REFRESH_MS", "10000"))   # 30 s por defecto
'''
# ── Colores base para tkinter (tema oscuro) ───────────────────────────────────
COLOR_BG      = "#0f1117"
COLOR_SURFACE = "#161b27"
COLOR_BORDER  = "#2d3748"
COLOR_TEXT    = "#e2e8f0"
COLOR_MUTED   = "#4a5568"
COLOR_GREEN   = "#1D9E75"
COLOR_RED     = "#E24B4A"
COLOR_BLUE    = "#378ADD"
COLOR_AMBER   = "#EF9F27"
COLOR_PURPLE  = "#7F77DD"'''
