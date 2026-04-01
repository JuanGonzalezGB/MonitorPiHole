# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 Juan S.G. Castellanos

"""
rpicore.estilos.vista.selectema
Selector de temas como Toplevel. Se abre desde cualquier app con:
    from rpicore.estilos.vista.selectema import ThemeSelector
    ThemeSelector(self, self)   # (ventana_raíz, app)
"""

import tkinter as tk

from rpicore.estilos.estilo.estiloFactory import EstiloFactory
from rpicore.estilos.estilo.gui_dictionary import TEMAS, FORMATS
from rpicore.estilos.controlador.controladorTemas import (
    ControladorTemas, etiquetar,
    ROL_BG, ROL_BG2, ROL_BORDER, ROL_COLOR1, ROL_MUTED, ROL_BOTON,
)

F_TITLE  = FORMATS["F_TITLE"]
F_NORMAL = FORMATS["F_NORMAL"]
F_SMALL  = FORMATS["F_SMALL"]


class ThemeSelector(tk.Toplevel):
    def __init__(self, parent_window: tk.Tk, app):
        """
        parent_window : ventana raíz tk.Tk
        app           : expone .estilo, ._controlador_temas, .apply_estilo()
        """
        super().__init__(parent_window)
        self._app            = app
        self._controlador    = app._controlador_temas
        self._tema_original  = app._cfg_tema.get_tema()
        self.estilo          = EstiloFactory.definirEstilo(self._tema_original)

        self.title("Themes")
        self.geometry("480x255")
        self.resizable(False, False)
        self.configure(bg=self.estilo.bg)
        self.grab_set()
        self.focus_set()

        self.tipo = tk.StringVar(value=self._codigo_a_display(self._tema_original))
        self._build_ui()

    def _build_ui(self):
        e = self.estilo

        # ── Header ────────────────────────────────────────────────────────────
        hdr = tk.Frame(self, bg=e.bg)
        etiquetar(hdr, ROL_BG)
        hdr.pack(fill="x", padx=8, pady=(6, 0))

        lbl = tk.Label(hdr, text="THEMES", bg=e.bg, fg=e.color1, font=F_TITLE)
        etiquetar(lbl, ROL_BG, ROL_COLOR1)
        lbl.pack(side="left")

        btn_x = tk.Button(
            hdr, text="✕", bg=e.bg, fg=e.muted,
            relief="flat", bd=0, cursor="hand2",
            activebackground=e.bg, activeforeground=e.color1,
            command=self._cancel,
        )
        etiquetar(btn_x, ROL_BG, ROL_MUTED)
        btn_x.pack(side="right")

        sep1 = tk.Frame(self, bg=e.border, height=1)
        sep1._bg_rol = ROL_BORDER
        sep1.pack(fill="x", padx=8, pady=4)

        # ── Body ──────────────────────────────────────────────────────────────
        body = tk.Frame(self, bg=e.bg)
        etiquetar(body, ROL_BG)
        body.pack(fill="both", expand=True, padx=12, pady=10)

        lbl_sel = tk.Label(body, text="Seleccionar tema",
                           bg=e.bg, fg=e.muted, font=F_NORMAL, anchor="w")
        etiquetar(lbl_sel, ROL_BG, ROL_MUTED)
        lbl_sel.pack(fill="x", pady=(0, 6))

        self.menu = tk.OptionMenu(body, self.tipo, *TEMAS.keys(),
                                  command=self._preview)
        self.menu.config(
            bg=e.bg2, fg=e.color1,
            activebackground=e.bg2, activeforeground=e.color1,
            highlightthickness=1, highlightbackground=e.border, bd=0,
        )
        etiquetar(self.menu, ROL_BG2, ROL_COLOR1)
        self.menu.pack(fill="x", pady=(0, 10))

        self.lbl_preview = tk.Label(
            body, text="Vista previa del tema",
            bg=e.bg2, fg=e.muted, font=F_SMALL, height=4,
        )
        etiquetar(self.lbl_preview, ROL_BG2, ROL_MUTED)
        self.lbl_preview.pack(fill="x", pady=6)

        sep2 = tk.Frame(self, bg=e.border, height=1)
        sep2._bg_rol = ROL_BORDER
        sep2.pack(fill="x", padx=8, pady=4)

        # ── Footer ────────────────────────────────────────────────────────────
        ftr = tk.Frame(self, bg=e.bg)
        etiquetar(ftr, ROL_BG)
        ftr.pack(fill="x", padx=8, pady=(0, 6))

        btn_cancel = tk.Button(
            ftr, text="Cancelar", bg=e.bg, fg=e.muted,
            relief="flat", bd=0, cursor="hand2",
            activebackground=e.bg, activeforeground=e.color1,
            command=self._cancel,
        )
        etiquetar(btn_cancel, ROL_BG, ROL_MUTED)
        btn_cancel.pack(side="left")

        btn_apply = tk.Button(
            ftr, text="Aplicar", bg=e.boton, fg=e.color1,
            relief="flat", bd=0, padx=10, cursor="hand2",
            command=self._apply,
        )
        etiquetar(btn_apply, ROL_BOTON, ROL_COLOR1)
        btn_apply.pack(side="right")

    def _codigo_a_display(self, codigo: str) -> str:
        return next((k for k, v in TEMAS.items() if v == codigo), list(TEMAS)[0])

    def _preview(self, _=None):
        codigo = TEMAS.get(self.tipo.get(), "dark")
        self._controlador.aplicarTema(codigo)
        self._controlador._retemar_arbol(self, self._app.estilo)

    def _cancel(self):
        self._controlador.aplicarTema(self._tema_original)
        self.destroy()

    def _apply(self):
        codigo = TEMAS.get(self.tipo.get(), "dark")
        self._controlador.aceptarTema(codigo)
        self.destroy()
