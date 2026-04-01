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
        "active_clients":    0,
        "status":            "unknown",
        "timestamp":         None,
    }


def get_status() -> str:
    doc = _col("stats").find_one(sort=[("timestamp", -1)], projection={"status": 1})
    return doc.get("status", "unknown") if doc else "unknown"


# ── Histórico para la gráfica ─────────────────────────────────────────────────

def get_history_24h() -> list[dict]:
    """
    Devuelve los buckets horarios de las últimas 24h.
    Siempre devuelve exactamente 24 items (rellena con 0 si faltan datos).
    """
    since = datetime.now(timezone.utc) - timedelta(hours=24)
    docs  = list(_col("history").find(
        {"hour": {"$gte": since}},
        {"_id": 0, "hour": 1, "total": 1, "blocked": 1},
        sort=[("hour", 1)],
    ))

    by_hour = {d["hour"].replace(minute=0, second=0, microsecond=0): d for d in docs}

    result = []
    for i in range(24):
        hour     = since.replace(minute=0, second=0, microsecond=0) + timedelta(hours=i)
        hour_key = hour.replace(tzinfo=timezone.utc)
        data     = by_hour.get(hour_key, {})
        result.append({
            "hour":    hour,
            "queries": data.get("total", 0),
            "blocked": data.get("blocked", 0),
            "label":   hour.strftime("%Hh"),
        })
    return result


# ── Top dominios bloqueados ───────────────────────────────────────────────────

def get_top_blocked(limit: int = 8) -> list[dict]:
    doc = _col("top_blocked").find_one({"_id": "current"})
    if not doc:
        return []
    return doc.get("items", [])[:limit]


# ── Top clientes activos ──────────────────────────────────────────────────────

def get_top_clients(limit: int = 5) -> list[dict]:
    """
    Devuelve los clientes más activos con nombre si existe en scanner.dispositivos.
    Flujo: ip → mac (via scanner.scans) → name (via scanner.dispositivos)
    Si no hay nombre registrado, muestra la IP.
    Cada item: {"ip": str, "name": str, "count": int}
    """
    doc = _col("top_clients").find_one({"_id": "current"})
    if not doc:
        return []

    items = doc.get("items", [])[:limit]
    ips   = [item["ip"].split("|")[0] for item in items]

    # ip → mac desde scanner.scans
    scans_col = get_collection("scanner", "scans")
    scan_docs = scans_col.find({"ip": {"$in": ips}}, {"_id": 0, "ip": 1, "mac": 1})
    ip_to_mac = {d["ip"]: d["mac"] for d in scan_docs}

    # mac → name desde scanner.dispositivos
    macs     = list(ip_to_mac.values())
    name_map = resolve_names(macs) if macs else {}

    result = []
    for item in items:
        ip   = item["ip"].split("|")[0]
        mac  = ip_to_mac.get(ip)
        name = name_map.get(mac, ip) if mac else ip
        result.append({"ip": ip, "name": name, "count": item["count"]})

    return result


# ── Última actualización ──────────────────────────────────────────────────────

def get_last_updated() -> str:
    doc = _col("stats").find_one(sort=[("timestamp", -1)], projection={"timestamp": 1})
    if not doc or not doc.get("timestamp"):
        return "sin datos"

    delta = datetime.now(timezone.utc) - doc["timestamp"].replace(tzinfo=timezone.utc)
    secs  = int(delta.total_seconds())
    if secs < 60:
        return f"hace {secs}s"
    return f"hace {secs // 60}m"
