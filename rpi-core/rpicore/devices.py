"""
rpi-core · devices.py
Lectura de dispositivos desde la db 'scanner' (dueño exclusivo: app scanner).
REGLA: este módulo NUNCA escribe en scanner.devices.
       Solo expone consultas de lectura para los demás proyectos.
"""

from typing import Optional
from rpicore.db import get_collection
from rpicore.config import DB_SCANNER, COLLECTION_DEVICES


def _col():
    return get_collection(DB_SCANNER, COLLECTION_DEVICES)


def get_name(mac: str) -> str:
    """
    Devuelve el nombre guardado para una MAC.
    Si no existe, devuelve la MAC tal cual.

    Ejemplo:
        get_name("86:fd:77:2e:27:cb")  →  "Amor5G"
        get_name("aa:bb:cc:dd:ee:ff")  →  "aa:bb:cc:dd:ee:ff"
    """
    doc = _col().find_one({"mac": mac}, {"name": 1, "_id": 0})
    if doc and doc.get("name"):
        return doc["name"]
    return mac


def get_device(mac: str) -> Optional[dict]:
    """
    Devuelve el documento completo de un dispositivo por MAC.
    Retorna None si no existe.
    """
    return _col().find_one({"mac": mac}, {"_id": 0})


def list_devices() -> list[dict]:
    """
    Devuelve todos los dispositivos conocidos.
    Útil para poblar listas en la GUI.
    """
    return list(_col().find({}, {"_id": 0, "mac": 1, "name": 1}))


def resolve_names(mac_list: list[str]) -> dict[str, str]:
    """
    Recibe una lista de MACs y devuelve un dict {mac: name}.
    Más eficiente que llamar get_name() en loop — una sola query.

    Ejemplo:
        resolve_names(["86:fd:77:2e:27:cb", "aa:bb:cc:dd:ee:ff"])
        → {"86:fd:77:2e:27:cb": "Amor5G", "aa:bb:cc:dd:ee:ff": "aa:bb:cc:dd:ee:ff"}
    """
    docs = _col().find({"mac": {"$in": mac_list}}, {"mac": 1, "name": 1, "_id": 0})
    found = {d["mac"]: d.get("name", d["mac"]) for d in docs}
    # MACs sin registro mantienen su MAC como nombre
    return {mac: found.get(mac, mac) for mac in mac_list}
