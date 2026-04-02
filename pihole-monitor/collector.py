"""
pihole-monitor · collector.py  (Pi-hole API v6)
Proceso independiente que corre como servicio systemd.

Cada REFRESH_MS segundos:
  1. Mantiene sesión activa con Pi-hole (re-autentica si el sid expira)
  2. Obtiene stats/summary, top_clients, top_domains, history
  3. Escribe en pihole_db (Mongo)

REGLA: este proceso NUNCA lee ni escribe en scanner.dispositivos.
"""

import os
import time
import logging
import requests
from datetime import datetime, timezone, timedelta
from pathlib import Path
from dotenv import load_dotenv

from rpicore.db import get_collection, ping
from rpicore.config import PIHOLE_HOST, PIHOLE_PORT, REFRESH_MS

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [collector] %(levelname)s %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

_BASE     = f"http://{PIHOLE_HOST}:{PIHOLE_PORT}/api"
_INTERVAL = REFRESH_MS / 1000

# Cargar password desde .env
_env_path = Path(__file__).resolve()
for _ in range(6):
    candidate = _env_path.parent / ".env"
    if candidate.exists():
        load_dotenv(candidate)
        break
    _env_path = _env_path.parent

PIHOLE_PASSWORD: str = os.getenv("PIHOLE_PASSWORD", "")


# ── Sesión con re-autenticación automática ────────────────────────────────────

class PiholeSession:
    """
    Mantiene un sid válido con Pi-hole v6.
    Re-autentica automáticamente cuando el sid está por expirar (validity = 1800s).
    """

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
                log.info("autenticado con Pi-hole (sid renovado)")
                return True
            log.error(f"autenticación fallida: {session.get('message')}")
            return False
        except requests.RequestException as e:
            log.warning(f"no se pudo autenticar: {e}")
            return False

    def get(self, path: str, params: dict | None = None) -> dict | None:
        """GET autenticado. Re-autentica si el sid está por expirar."""
        if not self._sid or datetime.now(timezone.utc) >= self._expires:
            if not self._authenticate():
                return None
        try:
            r = requests.get(
                f"{_BASE}/{path}",
                headers={"sid": self._sid},
                params=params,
                timeout=5,
            )
            r.raise_for_status()
            return r.json()
        except requests.RequestException as e:
            log.warning(f"GET /{path} falló: {e}")
            self._sid = None   # forzar re-auth en el próximo ciclo
            return None


# ── Escritura en Mongo ────────────────────────────────────────────────────────

def _col(name: str):
    return get_collection("pihole_db", name)


def save_snapshot(summary: dict, blocking: str = "unknown") -> None:
    now    = datetime.now(timezone.utc)
    minute = now.replace(second=0, microsecond=0)

    q = summary.get("queries", {})
    g = summary.get("gravity", {})
    c = summary.get("clients", {})

    doc = {
        "timestamp":         now,
        "queries_today":     q.get("total", 0),
        "blocked_today":     q.get("blocked", 0),
        "percent_blocked":   round(float(q.get("percent_blocked", 0)), 2),
        "domains_blocklist": g.get("domains_being_blocked", 0),
        "active_clients":    c.get("active", 0),
        "cached":            q.get("cached", 0),
        "forwarded":         q.get("forwarded", 0),
        "status":            blocking,
    }

    _col("stats").update_one(
        {"timestamp": minute},
        {"$set": doc},
        upsert=True,
    )
    log.info(
        f"snapshot — total: {doc['queries_today']} "
        f"bloqueadas: {doc['blocked_today']} ({doc['percent_blocked']}%) "
        f"status: {blocking}"
    )


def save_top_blocked(data: dict) -> None:
    domains = data.get("domains", [])
    if not domains:
        log.info("top_blocked: sin dominios bloqueados aún")
        return
    items = [{"domain": d["domain"], "count": d["count"]} for d in domains]
    _col("top_blocked").replace_one(
        {"_id": "current"},
        {"_id": "current", "updated_at": datetime.now(timezone.utc), "items": items},
        upsert=True,
    )


def save_top_clients(data: dict) -> None:
    clients = data.get("clients", [])
    if not clients:
        return
    items = [
        {"ip": c["ip"], "name": c.get("name", ""), "count": c["count"]}
        for c in clients
    ]
    _col("top_clients").replace_one(
        {"_id": "current"},
        {"_id": "current", "updated_at": datetime.now(timezone.utc), "items": items},
        upsert=True,
    )


def save_history(data: dict) -> None:
    """Agrega intervalos de 10min al histórico horario. Idempotente por hora."""
    entries = data.get("history", [])
    if not entries:
        return

    hourly: dict[int, dict] = {}
    for entry in entries:
        ts          = entry["timestamp"]
        bucket      = (ts // 3600) * 3600
        if bucket not in hourly:
            hourly[bucket] = {"total": 0, "blocked": 0, "cached": 0, "forwarded": 0}
        hourly[bucket]["total"]     += entry.get("total", 0)
        hourly[bucket]["blocked"]   += entry.get("blocked", 0)
        hourly[bucket]["cached"]    += entry.get("cached", 0)
        hourly[bucket]["forwarded"] += entry.get("forwarded", 0)

    for hour_ts, vals in hourly.items():
        hour_dt = datetime.fromtimestamp(hour_ts, tz=timezone.utc)
        _col("history").update_one(
            {"hour": hour_dt},
            {"$set": {"hour": hour_dt, **vals}},
            upsert=True,
        )
    log.info(f"history: {len(hourly)} buckets horarios guardados")


def save_active_clients(data: dict) -> None:
    """
    Extrae IPs únicas que hicieron queries en los últimos 5 minutos
    y las guarda en pihole_db.active_clients (documento único).
    """
    queries = data.get("queries", [])
    if not queries:
        return

    cutoff = datetime.now(timezone.utc).timestamp() - 300  # 5 minutos
    active_ips = set()
    for q in queries:
        if q.get("time", 0) >= cutoff:
            ip = q.get("client", {}).get("ip")
            if ip and ip not in {"127.0.0.1", "::1"}:
                active_ips.add(ip)

    _col("active_clients").replace_one(
        {"_id": "current"},
        {
            "_id":        "current",
            "updated_at": datetime.now(timezone.utc),
            "ips":        list(active_ips),
        },
        upsert=True,
    )
    log.info(f"active_clients: {len(active_ips)} activos en últimos 5min")


def ensure_indexes() -> None:
    _col("stats").create_index("timestamp", expireAfterSeconds=172800)  # TTL 48h
    _col("history").create_index("hour")
    log.info("índices verificados")


# ── Loop principal ────────────────────────────────────────────────────────────

def run() -> None:
    log.info(f"collector v6 arrancado — intervalo {_INTERVAL}s — {_BASE}")

    if not PIHOLE_PASSWORD:
        log.error("PIHOLE_PASSWORD no definido en .env — abortando")
        raise SystemExit(1)

    if not ping():
        log.error("MongoDB no responde — abortando")
        raise SystemExit(1)

    ensure_indexes()
    session = PiholeSession()

    while True:
        try:
            summary = session.get("stats/summary")
            if summary:
                blocking_data = session.get("dns/blocking") or {}
                blocking      = blocking_data.get("blocking", "unknown")
                save_snapshot(summary, blocking)
                save_top_clients(
                    session.get("stats/top_clients", params={"count": 10}) or {}
                )
                save_active_clients(
                    session.get("queries/clients", params={"max": 500}) or {}
                )
                if datetime.now().minute % 5 == 0:
                    save_top_blocked(
                        session.get("stats/top_domains",
                                    params={"blocked": "true", "count": 10}) or {}
                    )
                    save_history(session.get("history") or {})
            else:
                log.warning("sin respuesta de Pi-hole — reintentando en el siguiente ciclo")

        except Exception as e:
            log.error(f"error inesperado: {e}", exc_info=True)

        time.sleep(_INTERVAL)


if __name__ == "__main__":
    run()
