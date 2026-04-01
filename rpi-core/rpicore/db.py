"""
rpi-core · db.py
Cliente MongoDB singleton. Una sola conexión compartida por proceso.
Uso:
    from rpicore.db import get_client, get_collection

    col = get_collection("pihole_db", "stats")
    col.insert_one({...})
"""

import threading
from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.errors import ConnectionFailure

from rpicore.config import MONGO_URI, MONGO_TIMEOUT_MS

_lock   = threading.Lock()
_client: MongoClient | None = None


def get_client() -> MongoClient:
    """Devuelve el cliente singleton, creándolo si no existe."""
    global _client
    if _client is None:
        with _lock:
            if _client is None:   # doble check tras adquirir el lock
                _client = MongoClient(
                    MONGO_URI,
                    serverSelectionTimeoutMS=MONGO_TIMEOUT_MS,
                    connectTimeoutMS=MONGO_TIMEOUT_MS,
                )
    return _client


def get_collection(db_name: str, collection_name: str) -> Collection:
    """Atajo para obtener una colección directamente."""
    return get_client()[db_name][collection_name]


def ping() -> bool:
    """Comprueba que Mongo es alcanzable. Útil al arrancar."""
    try:
        get_client().admin.command("ping")
        return True
    except ConnectionFailure:
        return False


def close() -> None:
    """Cierra la conexión. Llamar al apagar la app."""
    global _client
    if _client:
        _client.close()
        _client = None
