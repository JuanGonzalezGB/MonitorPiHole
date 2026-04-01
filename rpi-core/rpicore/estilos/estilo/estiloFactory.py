# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 Juan S.G. Castellanos

from rpicore.estilos.estilo.dark import DarkColor
from rpicore.estilos.estilo.gui_dictionary import CLASESTEMAS


class EstiloFactory:
    @staticmethod
    def definirEstilo(tipo: str):
        clase = CLASESTEMAS.get(tipo, DarkColor)
        return clase()
