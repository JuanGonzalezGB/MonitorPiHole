"""
pihole-monitor · repository.py
Toda la lógica de lectura de pihole_db.
La GUI solo llama funciones de este módulo — nunca toca Mongo directamente.
"""

from datetime import datetime, timezone, timedelta
from rpicore.db import get_collection
from rpicore.devices import resolve_names


def _col(name: str):
    return get_collection("pihole_db", name)


# ── Stats actuales ────────────────────────────────────────────────────────────

def get_latest_stats() -> dict:
    """
    Devuelve el snapshot más reciente.
    Retorna un dict con valores por defecto si no hay datos aún.
    """
    doc = _col("stats").find_one(
        sort=[("timestamp", -1)],
        projection={"_id": 0},
    )
    if doc:
        return doc
    return {
        "queries_today":     0,
        "blocked_today":     0,
        "percent_blocked":   0.0,
        "domains_blocklist": 0,
        "unique_clients":    0,
        "status":            "unknown",
        "timestamp":         None,
    }


def get_status() -> str:
    """Devuelve 'enabled', 'disabled' o 'unknown'."""
    doc = _col("stats").find_one(sort=[("timestamp", -1)], projection={"status": 1})
    return doc.get("status", "unknown") if doc else "unknown"


# ── Histórico para la gráfica ─────────────────────────────────────────────────

def get_history_24h() -> list[dict]:
    """
    Devuelve los buckets horarios de las últimas 24h.
    Cada item: {"hour": datetime, "queries": int, "blocked": int, "label": "14h"}
    Siempre devuelve exactamente 24 items (rellena con 0 si faltan datos).
    """
    since = datetime.now(timezone.utc) - timedelta(hours=24)
    docs = list(_col("history").find(
        {"hour": {"$gte": since}},
        {"_id": 0, "hour": 1, "queries": 1, "blocked": 1},
        sort=[("hour", 1)],
    ))

    # Índice de lo que hay en db
    by_hour = {d["hour"].replace(minute=0, second=0, microsecond=0): d for d in docs}

    result = []
    now = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)
    for i in range(24):
        hour = since.replace(minute=0, second=0, microsecond=0) + timedelta(hours=i)
        hour_key = hour.replace(tzinfo=timezone.utc)
        data = by_hour.get(hour_key, {})
        result.append({
            "hour":    hour,
            "queries": data.get("queries", 0),
            "blocked": data.get("blocked", 0),
            "label":   hour.strftime("%Hh"),
        })
    return result


# ── Top dominios bloqueados ───────────────────────────────────────────────────

def get_top_blocked(limit: int = 8) -> list[dict]:
    """
    Devuelve los dominios más bloqueados.
    Cada item: {"domain": str, "count": int}
    """
    doc = _col("top_blocked").find_one({"_id": "current"})
    if not doc:
        return []
    return doc.get("items", [])[:limit]


# ── Top clientes activos ──────────────────────────────────────────────────────

def get_top_clients(limit: int = 5) -> list[dict]:
    """
    Devuelve los clientes más activos cruzados con nombres de scanner.dispositivos.
    Pi-hole identifica clientes por IP, así que mostramos IP con nombre si existe.
    Cada item: {"ip": str, "name": str, "count": int}
    """
    doc = _col("top_clients").find_one({"_id": "current"})
    if not doc:
        return []

    items = doc.get("items", [])[:limit]
    return [
        {
            "ip":   item["ip"].split("|")[0],  # Pi-hole a veces añade |hostname
            "name": item["ip"].split("|")[1] if "|" in item["ip"] else item["ip"],
            "count": item["count"],
        }
        for item in items
    ]


# ── Última actualización ──────────────────────────────────────────────────────

def get_last_updated() -> str:
    """
    Devuelve hace cuánto se actualizaron los datos.
    Ejemplo: "hace 8s", "hace 2m"
    """
    doc = _col("stats").find_one(sort=[("timestamp", -1)], projection={"timestamp": 1})
    if not doc or not doc.get("timestamp"):
        return "sin datos"

    delta = datetime.now(timezone.utc) - doc["timestamp"].replace(tzinfo=timezone.utc)
    secs = int(delta.total_seconds())
    if secs < 60:
        return f"hace {secs}s"
    return f"hace {secs // 60}m"
