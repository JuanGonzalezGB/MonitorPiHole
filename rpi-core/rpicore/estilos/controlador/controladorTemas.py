# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 Juan S.G. Castellanos

"""
rpicore.estilos.controlador.controladorTemas

ControladorTemas recibe la app y puede:
  - aplicarTema(codigo)  → preview en vivo sin guardar
  - aceptarTema(codigo)  → preview + persiste en config.json

Los widgets se retematiztan recorriendo el árbol de tk y leyendo
los atributos _bg_rol y _fg_rol que etiquetar() estampa en cada widget.
El color se resuelve con getattr(estilo, rol).
"""

import tkinter as tk
from tkinter import ttk

from rpicore.estilos.estilo.estiloFactory import EstiloFactory

# ─── Roles semánticos ────────────────────────────────────────────────────────
# Los valores coinciden EXACTAMENTE con los atributos de dark.py / light.py
ROL_BG     = "bg"
ROL_BG2    = "bg2"
ROL_BORDER = "border"
ROL_OK     = "colorok"
ROL_MID    = "colormid"
ROL_BAD    = "colorbad"
ROL_COLOR1 = "color1"
ROL_COLOR2 = "color2"
ROL_COLOR3 = "color3"
ROL_MUTED  = "muted"
ROL_BOTON  = "boton"


def _color(estilo, rol: str) -> str:
    """Resuelve un rol al color correspondiente del estilo activo."""
    return getattr(estilo, rol, estilo.color3)


def etiquetar(widget: tk.Widget, bg_rol: str, fg_rol: str | None = None) -> None:
    """
    Estampa roles semánticos en un widget para que el controlador
    sepa qué colores aplicar al retematizar.

        etiquetar(lbl,   ROL_BG,  ROL_COLOR1)
        etiquetar(frame, ROL_BG2)            # solo bg, sin fg
        etiquetar(sep,   ROL_BORDER)         # separador
    """
    widget._bg_rol = bg_rol
    if fg_rol is not None:
        widget._fg_rol = fg_rol


class ControladorTemas:
    def __init__(self, app):
        """
        app debe exponer:
          app.root              → tk.Tk  (o la ventana raíz)
          app.estilo            → objeto Estilo activo
          app._ttk_style        → ttk.Style (puede ser None si no hay ttk)
          app.apply_estilo(e)   → callback para referencias internas
          app._cfg_tema         → instancia de ConfigTema
        """
        self._app = app

    # ─── API pública ─────────────────────────────────────────────────────────

    def aplicarTema(self, codigo: str) -> None:
        """Cambia el tema en vivo (preview); no guarda en disco."""
        nuevo = EstiloFactory.definirEstilo(codigo)
        self._app.apply_estilo(nuevo)
        self._retemar_arbol(self._app, nuevo)
        if getattr(self._app, "_ttk_style", None):
            self._retemar_ttk(nuevo)

    def aceptarTema(self, codigo: str) -> None:
        """Cambia el tema y lo persiste en config.json."""
        self.aplicarTema(codigo)
        self._app._cfg_tema.set_tema(codigo)

    # ─── Internos ────────────────────────────────────────────────────────────

    def _retemar_arbol(self, widget: tk.Widget, estilo) -> None:
        """Recorre recursivamente el árbol de widgets y aplica colores por rol."""
        bg_rol = getattr(widget, "_bg_rol", None)
        fg_rol = getattr(widget, "_fg_rol", None)

        if bg_rol:
            try:
                color_bg = _color(estilo, bg_rol)
                widget.config(bg=color_bg)
                widget.config(activebackground=color_bg)
            except tk.TclError:
                pass

        if fg_rol:
            try:
                color_fg = _color(estilo, fg_rol)
                widget.config(fg=color_fg)
                widget.config(activeforeground=color_fg)
            except tk.TclError:
                pass

        for child in widget.winfo_children():
            self._retemar_arbol(child, estilo)

    def _retemar_ttk(self, estilo) -> None:
        """Actualiza estilos de barras de progreso ttk."""
        s = self._app._ttk_style
        s.configure("Ok.Horizontal.TProgressbar",
                    troughcolor=estilo.bg2, background=estilo.colorok)
        s.configure("Mid.Horizontal.TProgressbar",
                    troughcolor=estilo.bg2, background=estilo.colormid)
        s.configure("Bad.Horizontal.TProgressbar",
                    troughcolor=estilo.bg2, background=estilo.colorbad)
