# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 Juan S.G. Castellanos

"""
rpicore.estilos.modelo.config
Lee y escribe config.json en la carpeta del proyecto que lo usa.

Uso desde cada proyecto:
    from rpicore.estilos.modelo.config import ConfigTema
    cfg = ConfigTema("/ruta/al/proyecto")   # donde vive config.json
    tema = cfg.get_tema()
    cfg.set_tema("light")
"""

import json
import os

_DEFAULTS = {"tema": "dark"}


class ConfigTema:
    def __init__(self, project_dir: str):
        self._path = os.path.join(project_dir, "config.json")

    def _load(self) -> dict:
        if os.path.exists(self._path):
            try:
                with open(self._path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except (json.JSONDecodeError, OSError):
                pass
        return dict(_DEFAULTS)

    def _save(self, data: dict) -> None:
        with open(self._path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def get_tema(self) -> str:
        return self._load().get("tema", _DEFAULTS["tema"])

    def set_tema(self, codigo: str) -> None:
        data = self._load()
        data["tema"] = codigo
        self._save(data)
