"""
pihole-monitor · sync.py
Sincroniza dispositivos con nombre desde scanner.dispositivos → Pi-hole v6.

Flujo:
  1. Lee scanner.dispositivos  → {mac, name}  (solo los que tienen nombre real)
  2. Lee scanner.scans         → {mac, ip}    (última IP conocida por MAC)
  3. Cruza ambos               → {ip, name}
  4. Registra en Pi-hole       → POST/PUT /api/clients con comment=name

Restricciones:
  - Solo sincroniza dispositivos que aparecen en scanner.scans (IP conocida)
  - No elimina clientes de Pi-hole que no estén en scanner.dispositivos
  - No escribe en scanner.dispositivos ni scanner.scans

Uso:
    python sync.py           # corre una vez y sale
    python sync.py --watch   # loop cada 5 minutos
"""

import os
import sys
import time
import logging
import argparse
import requests
from datetime import datetime, timezone, timedelta
from pathlib import Path
from dotenv import load_dotenv

from rpicore.db import get_collection
from rpicore.config import PIHOLE_HOST, PIHOLE_PORT, DB_SCANNER, COLLECTION_DEVICES

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [sync] %(levelname)s %(message)s",
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

PIHOLE_PASSWORD: str = os.getenv("PIHOLE_PASSWORD", "")
_BASE            = f"http://{PIHOLE_HOST}:{PIHOLE_PORT}/api"
_WATCH_INTERVAL  = 300  # 5 minutos


# ── Sesión Pi-hole v6 ─────────────────────────────────────────────────────────

class PiholeSession:
    def __init__(self):
        self._sid:     str | None = None
        self._expires: datetime   = datetime.min.replace(tzinfo=timezone.utc)

    def _authenticate(self) -> bool:
        try:
            r = requests.post(
                f"{_BASE}/auth",
                json={"password": PIHOLE_PASSWORD},
                timeout=5,
            )
            session = r.json().get("session", {})
            if session.get("valid"):
                self._sid     = session["sid"]
                validity      = session.get("validity", 1800)
                self._expires = datetime.now(timezone.utc) + timedelta(seconds=validity - 60)
                return True
            log.error(f"autenticación fallida: {session.get('message')}")
            return False
        except requests.RequestException as e:
            log.error(f"no se pudo conectar a Pi-hole: {e}")
            return False

    def _headers(self) -> dict | None:
        if not self._sid or datetime.now(timezone.utc) >= self._expires:
            if not self._authenticate():
                return None
        return {"sid": self._sid}

    def get_clients(self) -> list[dict]:
        headers = self._headers()
        if not headers:
            return []
        try:
            r = requests.get(f"{_BASE}/clients", headers=headers, timeout=5)
            r.raise_for_status()
            return r.json().get("clients", [])
        except requests.RequestException as e:
            log.warning(f"error obteniendo clientes: {e}")
            return []

    def add_client(self, ip: str, name: str) -> bool:
        headers = self._headers()
        if not headers:
            return False
        try:
            r = requests.post(
                f"{_BASE}/clients",
                headers={**headers, "Content-Type": "application/json"},
                json={"client": ip, "comment": name},
                timeout=5,
            )
            r.raise_for_status()
            errors = r.json().get("processed", {}).get("errors", [])
            if errors:
                log.warning(f"Pi-hole rechazó {ip}: {errors}")
                return False
            return True
        except requests.RequestException as e:
            log.warning(f"error agregando {ip}: {e}")
            return False

    def update_client(self, client_id: int, ip: str, name: str) -> bool:
        headers = self._headers()
        if not headers:
            return False
        try:
            r = requests.put(
                f"{_BASE}/clients/{client_id}",
                headers={**headers, "Content-Type": "application/json"},
                json={"client": ip, "comment": name},
                timeout=5,
            )
            r.raise_for_status()
            return True
        except requests.RequestException as e:
            log.warning(f"error actualizando cliente {client_id}: {e}")
            return False


# ── Leer datos desde MongoDB ──────────────────────────────────────────────────

def get_named_devices() -> dict[str, str]:
    """
    Lee scanner.dispositivos y devuelve {mac: name}
    solo para dispositivos con nombre real (distinto a la MAC).
    """
    col  = get_collection(DB_SCANNER, COLLECTION_DEVICES)
    docs = col.find(
        {"name": {"$exists": True, "$ne": ""}},
        {"_id": 0, "mac": 1, "name": 1},
    )
    return {
        d["mac"].lower(): d["name"]
        for d in docs
        if d.get("mac") and d.get("name", "").lower() != d.get("mac", "").lower()
    }


def get_mac_to_ip() -> dict[str, str]:
    """
    Lee scanner.scans y devuelve {mac: ip} con la IP más reciente por MAC.
    Este es el puente entre scanner.dispositivos (mac→name) y Pi-hole (ip→name).
    """
    col  = get_collection(DB_SCANNER, "scans")
    docs = col.find(
        {"mac": {"$exists": True}, "ip": {"$exists": True}},
        {"_id": 0, "mac": 1, "ip": 1},
    )
    return {d["mac"].lower(): d["ip"] for d in docs}


# ── Lógica de sincronización ──────────────────────────────────────────────────

def sync_once(session: PiholeSession) -> None:
    log.info("iniciando sincronización...")

    named_devices = get_named_devices()   # {mac: name}
    mac_to_ip     = get_mac_to_ip()       # {mac: ip}

    if not named_devices:
        log.info("no hay dispositivos con nombre en scanner.dispositivos")
        return

    if not mac_to_ip:
        log.warning(
            "scanner.scans está vacío — el network-monitor collector "
            "debe correr al menos una vez antes del sync"
        )
        return

    # Cruzar: solo dispositivos con nombre Y con IP conocida
    to_sync: list[dict] = []
    sin_ip: list[str]   = []

    for mac, name in named_devices.items():
        ip = mac_to_ip.get(mac)
        if ip:
            to_sync.append({"ip": ip, "name": name, "mac": mac})
        else:
            sin_ip.append(name)

    if sin_ip:
        log.info(f"sin IP conocida (no aparecen en scans): {', '.join(sin_ip)}")

    if not to_sync:
        log.info("ningún dispositivo con nombre tiene IP conocida aún")
        return

    # Estado actual en Pi-hole: {ip: {id, comment}}
    pihole_clients = session.get_clients()
    pihole_by_ip   = {
        c["client"]: {"id": c["id"], "comment": c.get("comment", "")}
        for c in pihole_clients
    }

    agregados    = 0
    actualizados = 0
    sin_cambios  = 0

    for device in to_sync:
        ip   = device["ip"]
        name = device["name"]

        if ip not in pihole_by_ip:
            if session.add_client(ip, name):
                log.info(f"  + agregado:    {ip:18} → '{name}'")
                agregados += 1
            else:
                log.warning(f"  ✗ falló agregar {ip} ('{name}')")

        elif pihole_by_ip[ip]["comment"] != name:
            client_id = pihole_by_ip[ip]["id"]
            if session.update_client(client_id, ip, name):
                old = pihole_by_ip[ip]["comment"]
                log.info(f"  ~ actualizado: {ip:18} '{old}' → '{name}'")
                actualizados += 1
            else:
                log.warning(f"  ✗ falló actualizar {ip}")

        else:
            sin_cambios += 1

    log.info(
        f"sync completado — "
        f"agregados: {agregados}, actualizados: {actualizados}, sin cambios: {sin_cambios}"
    )


# ── Entry points ──────────────────────────────────────────────────────────────

def run_once() -> None:
    if not PIHOLE_PASSWORD:
        log.error("PIHOLE_PASSWORD no definido en .env")
        sys.exit(1)
    sync_once(PiholeSession())


def run_watch() -> None:
    if not PIHOLE_PASSWORD:
        log.error("PIHOLE_PASSWORD no definido en .env")
        sys.exit(1)
    log.info(f"modo watch — sincronizando cada {_WATCH_INTERVAL // 60} minutos")
    session = PiholeSession()
    while True:
        try:
            sync_once(session)
        except Exception as e:
            log.error(f"error inesperado: {e}", exc_info=True)
        time.sleep(_WATCH_INTERVAL)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Sincroniza dispositivos → Pi-hole")
    parser.add_argument("--watch", action="store_true",
                        help="Loop cada 5 minutos en vez de una sola vez")
    args = parser.parse_args()
    run_watch() if args.watch else run_once()
