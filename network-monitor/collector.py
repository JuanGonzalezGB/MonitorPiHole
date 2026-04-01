"""
network-monitor · collector.py
Proceso independiente (systemd) que corre scan_network.sh periódicamente
y persiste los resultados en scanner.scans.

Colecciones que escribe (dueño exclusivo):
  scanner.scans  — historial de cada escaneo con {mac, ip, vendor, ping_ms}

Colecciones que lee:
  scanner.dispositivos — para enriquecer los scans con el nombre del dispositivo

REGLA: no escribe en scanner.dispositivos — eso lo hace la GUI del network-monitor.
"""

import os
import json
import logging
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from rpicore.db import get_collection, ping
from rpicore.config import REFRESH_MS, DB_SCANNER, COLLECTION_DEVICES

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [net-collector] %(levelname)s %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

# Cargar .env
_env_path = Path(__file__).resolve()
for _ in range(6):
    candidate = _env_path.parent / ".env"
    if candidate.exists():
        load_dotenv(candidate)
        break
    _env_path = _env_path.parent

SUBNET:   str = os.getenv("NETWORK_SUBNET", "192.168.0.0/24")
INTERVAL: int = int(os.getenv("SCAN_INTERVAL_S", "120"))  # 2 min por defecto

_SCRIPT = Path(__file__).parent / "scan_network.sh"


# ── Escaneo ───────────────────────────────────────────────────────────────────

def run_scan() -> list[dict]:
    """
    Ejecuta scan_network.sh y devuelve la lista de dispositivos encontrados.
    Retorna [] si el script falla o no encuentra nada.
    """
    if not _SCRIPT.exists():
        log.error(f"scan_network.sh no encontrado en {_SCRIPT}")
        return []
    try:
        result = subprocess.run(
            ["bash", str(_SCRIPT), SUBNET],
            capture_output=True, text=True, timeout=60,
        )
        if result.returncode != 0:
            log.warning(f"scan_network.sh salió con código {result.returncode}")
        raw = result.stdout.strip()
        if not raw or raw == "[]":
            log.warning("scan sin resultados")
            return []
        devices = json.loads(raw)
        log.info(f"scan completado — {len(devices)} dispositivos encontrados")
        return devices
    except subprocess.TimeoutExpired:
        log.warning("scan_network.sh tardó más de 60s — abortado")
        return []
    except json.JSONDecodeError as e:
        log.warning(f"JSON inválido del script: {e}")
        return []


# ── Escritura en Mongo ────────────────────────────────────────────────────────

def save_scan(devices: list[dict]) -> None:
    """
    Guarda el resultado del scan en scanner.scans.
    Upsert por MAC — siempre refleja el estado más reciente de cada dispositivo.
    También actualiza scanner.dispositivos solo si la MAC es nueva (primer avistamiento).
    """
    if not devices:
        return

    scans_col = get_collection(DB_SCANNER, "scans")
    now       = datetime.now(timezone.utc)

    for device in devices:
        mac = device.get("mac", "").lower()
        ip  = device.get("ip", "")
        if not mac or not ip:
            continue

        scans_col.update_one(
            {"mac": mac},
            {"$set": {
                "mac":       mac,
                "ip":        ip,
                "vendor":    device.get("vendor", ""),
                "ping_ms":   device.get("ping_ms"),
                "last_seen": now,
            },
             "$setOnInsert": {"first_seen": now}},
            upsert=True,
        )

    log.info(f"{len(devices)} dispositivos guardados en scanner.scans")


def ensure_indexes() -> None:
    col = get_collection(DB_SCANNER, "scans")
    col.create_index("mac", unique=True)
    col.create_index("last_seen")
    log.info("índices verificados")


# ── Loop principal ────────────────────────────────────────────────────────────

def run() -> None:
    log.info(f"network collector arrancado — subnet: {SUBNET} — intervalo: {INTERVAL}s")

    if not ping():
        log.error("MongoDB no responde — abortando")
        raise SystemExit(1)

    ensure_indexes()

    while True:
        try:
            devices = run_scan()
            if devices:
                save_scan(devices)
        except Exception as e:
            log.error(f"error inesperado: {e}", exc_info=True)
        time.sleep(INTERVAL)


if __name__ == "__main__":
    run()
