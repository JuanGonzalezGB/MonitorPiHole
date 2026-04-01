"""
pihole-monitor · gui.py
Interfaz tkinter optimizada para pantalla 480×320.
Integra el sistema de temas de rpi-core.
"""

import os
import tkinter as tk

from rpicore.estilos.estilo.estiloFactory import EstiloFactory
from rpicore.estilos.controlador.controladorTemas import (
    ControladorTemas, etiquetar,
    ROL_BG, ROL_BG2, ROL_BORDER, ROL_COLOR1, ROL_COLOR2, ROL_COLOR3,
    ROL_OK, ROL_BAD, ROL_MID, ROL_MUTED, ROL_BOTON,
)
from rpicore.estilos.modelo.config import ConfigTema
from rpicore.estilos.vista.selectema import ThemeSelector
from rpicore.widgets import BarChart
from rpicore.config import REFRESH_MS

import repository as repo

_PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))


# ── ScrollFrame ───────────────────────────────────────────────────────────────

class ScrollFrame(tk.Frame):
    def __init__(self, parent, bg, bg_rol=ROL_BG2):
        super().__init__(parent, bg=bg)
        etiquetar(self, bg_rol)
        self.canvas    = tk.Canvas(self, bg=bg, highlightthickness=0)
        self.canvas._bg_rol = bg_rol
        self.inner     = tk.Frame(self.canvas, bg=bg)
        self.inner._bg_rol = bg_rol
        self.scrollbar = tk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        etiquetar(self.scrollbar, bg_rol)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)
        self.window = self.canvas.create_window((0, 0), window=self.inner, anchor="nw")
        self.inner.bind("<Configure>", self._on_configure)
        self.canvas.bind("<Configure>", self._on_canvas_configure)
        self.canvas.bind_all("<Button-4>", lambda e: self.canvas.yview_scroll(-1, "units"))
        self.canvas.bind_all("<Button-5>", lambda e: self.canvas.yview_scroll(1, "units"))
        self.canvas.bind("<ButtonPress-1>", self._on_press)
        self.canvas.bind("<B1-Motion>",     self._on_drag)
        self._start_y = 0

    def _on_configure(self, event):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _on_canvas_configure(self, event):
        self.canvas.itemconfig(self.window, width=event.width)

    def _on_press(self, event):  self._start_y = event.y

    def _on_drag(self, event):
        delta = self._start_y - event.y
        self.canvas.yview_scroll(int(delta / 2), "units")
        self._start_y = event.y


class ScrollFrameXY(ScrollFrame):
    def __init__(self, parent, bg, bg_rol=ROL_BG2):
        super().__init__(parent, bg=bg, bg_rol=bg_rol)
        self._hbar = tk.Scrollbar(self, orient="horizontal", command=self.canvas.xview)
        etiquetar(self._hbar, bg_rol)
        self.canvas.configure(xscrollcommand=self._hbar.set)
        self._hbar.pack(in_=self, side="top", fill="x", before=self.canvas)

    def _on_canvas_configure(self, event):
        pass   # no forzar ancho → permite scroll horizontal


# ── Widgets temizables ────────────────────────────────────────────────────────

class StatCard(tk.Frame):
    def __init__(self, parent, label: str, estilo, val_rol: str, **kwargs):
        super().__init__(parent, bg=estilo.bg2, **kwargs)
        etiquetar(self, ROL_BG2)
        self._val_rol  = val_rol
        self._lbl_var  = tk.StringVar(value=label)
        self._val_var  = tk.StringVar(value="—")

        lbl = tk.Label(self, textvariable=self._lbl_var,
                       bg=estilo.bg2, fg=estilo.muted,
                       font=("monospace", 7), anchor="center")
        etiquetar(lbl, ROL_BG2, ROL_MUTED)
        lbl.pack(fill="x", padx=6, pady=(6, 0))

        self._val_lbl = tk.Label(self, textvariable=self._val_var,
                                 bg=estilo.bg2,
                                 fg=getattr(estilo, val_rol),
                                 font=("monospace", 16, "bold"), anchor="center")
        etiquetar(self._val_lbl, ROL_BG2, val_rol)
        self._val_lbl.pack(fill="x", padx=6, pady=(2, 6))

    def set_value(self, v: str): self._val_var.set(v)


class DeviceList(tk.Frame):
    def __init__(self, parent, estilo, **kwargs):
        super().__init__(parent, bg=estilo.bg2, **kwargs)
        etiquetar(self, ROL_BG2)
        self._estilo = estilo
        self._rows: list[tk.Frame] = []

    def set_items(self, items: list[dict]) -> None:
        for r in self._rows:
            r.destroy()
        self._rows.clear()
        for item in items:
            row = tk.Frame(self, bg=self._estilo.bg2)
            etiquetar(row, ROL_BG2)
            row.pack(fill="x", padx=8, pady=1)
            lp = tk.Label(row, text=item.get("primary", ""),
                          bg=self._estilo.bg2, fg=self._estilo.color3,
                          font=("monospace", 8), anchor="w")
            etiquetar(lp, ROL_BG2, ROL_COLOR3)
            lp.pack(side="left")
            ls = tk.Label(row, text=item.get("secondary", ""),
                          bg=self._estilo.bg2, fg=self._estilo.muted,
                          font=("monospace", 7), anchor="e")
            etiquetar(ls, ROL_BG2, ROL_MUTED)
            ls.pack(side="right")
            self._rows.append(row)

    def update_estilo(self, estilo): 
        self._estilo = estilo
        for row in self._rows:
            row.config(bg=estilo.bg2)
            for child in row.winfo_children():
                if isinstance(child, tk.Label):
                    if child.cget("anchor") == "w":
                        child.config(bg=estilo.bg2, fg=estilo.color3)
                    else:
                        child.config(bg=estilo.bg2, fg=estilo.muted)


class StatusDot(tk.Frame):
    def __init__(self, parent, label: str, estilo, **kwargs):
        super().__init__(parent, bg=estilo.bg, **kwargs)
        etiquetar(self, ROL_BG)
        self._canvas = tk.Canvas(self, width=10, height=10,
                                 bg=estilo.bg, highlightthickness=0)
        etiquetar(self._canvas, ROL_BG)
        self._canvas.pack(side="left", padx=(4, 3))
        self._dot = self._canvas.create_oval(1, 1, 9, 9,
                                             fill=estilo.muted, outline="")
        lbl = tk.Label(self, text=label, bg=estilo.bg, fg=estilo.muted,
                       font=("monospace", 8))
        etiquetar(lbl, ROL_BG, ROL_MUTED)
        lbl.pack(side="left")
        self._online = False

    def set_status(self, online: bool):
        self._online = online

    def refresh_dot(self, estilo):
        color = estilo.colorok if self._online else estilo.colorbad
        self._canvas.itemconfig(self._dot, fill=color)


class TopBar(tk.Frame):
    def __init__(self, parent, title: str, estilo, **kwargs):
        super().__init__(parent, bg=estilo.bg2, height=28, **kwargs)
        etiquetar(self, ROL_BG2)
        self.pack_propagate(False)
        lbl = tk.Label(self, text=title, bg=estilo.bg2, fg=estilo.muted,
                       font=("monospace", 8), anchor="w")
        etiquetar(lbl, ROL_BG2, ROL_MUTED)
        lbl.pack(side="left", padx=10)
        self._ts_var = tk.StringVar(value="")
        self._ts_lbl = tk.Label(self, textvariable=self._ts_var,
                                bg=estilo.bg2, fg=estilo.muted,
                                font=("monospace", 7), anchor="e")
        etiquetar(self._ts_lbl, ROL_BG2, ROL_MUTED)
        self._ts_lbl.pack(side="right", padx=10)

        # Botón de temas
        self._btn_tema = tk.Button(
            self, text="◑", bg=estilo.bg2, fg=estilo.color1,
            relief="flat", bd=0, cursor="hand2",
            activebackground=estilo.bg2, activeforeground=estilo.color1,
            font=("monospace", 9),
        )
        etiquetar(self._btn_tema, ROL_BG2, ROL_COLOR1)
        self._btn_tema.pack(side="right", padx=(0, 4))

    def set_theme_command(self, cmd): self._btn_tema.config(command=cmd)

    def tick(self):
        from datetime import datetime
        self._ts_var.set(datetime.now().strftime("%H:%M:%S"))


# ── App principal ─────────────────────────────────────────────────────────────

class PiholeMonitorApp(tk.Tk):
    def __init__(self):
        super().__init__()

        # ── Tema ──────────────────────────────────────────────────────────────
        self._cfg_tema  = ConfigTema(_PROJECT_DIR)
        self.estilo     = EstiloFactory.definirEstilo(self._cfg_tema.get_tema())
        self._ttk_style = None   # no usamos ttk

        self.title("Pi-hole monitor")
        self.geometry("480x260")
        self.resizable(False, False)
        self.configure(bg=self.estilo.bg)
        self.overrideredirect(False)

        self._build_ui()

        # Instanciar controlador DESPUÉS de build_ui
        self._controlador_temas = ControladorTemas(self)
        self.topbar.set_theme_command(self._open_themes)

        self._refresh()

    # ── Contrato requerido por ControladorTemas ───────────────────────────────

    def apply_estilo(self, nuevo_estilo) -> None:
        self.estilo = nuevo_estilo
        self.configure(bg=nuevo_estilo.bg)
        self.top_blocked_list.update_estilo(nuevo_estilo)
        self.clients_list.update_estilo(nuevo_estilo)
        self.status_dot.refresh_dot(nuevo_estilo)
        self.chart.config(bg=nuevo_estilo.bg2)
        self.chart.set_label_color(nuevo_estilo.muted)
        
        # Actualizar colores de los círculos de la leyenda
        if hasattr(self, 'legend_dots'):
            colors = [nuevo_estilo.colorok, nuevo_estilo.colorbad]
            for dot, color in zip(self.legend_dots, colors):
                dot.delete("all")
                dot.create_oval(1, 1, 7, 7, fill=color, outline="")
        
        self._update_chart()

    # ── UI ────────────────────────────────────────────────────────────────────

    def _build_ui(self):
        e = self.estilo

        self.topbar = TopBar(self, title="Pi-hole monitor", estilo=e)
        self.topbar.pack(fill="x", side="top")
        self._sep(self, e)

        # Stats
        stats_row = tk.Frame(self, bg=e.bg)
        etiquetar(stats_row, ROL_BG)
        stats_row.pack(fill="x", padx=4, pady=(4, 0))

        self.card_queries = StatCard(stats_row, "QUERIES HOY", e, ROL_OK)
        self.card_blocked = StatCard(stats_row, "BLOQUEADAS",  e, ROL_BAD)
        self.card_percent = StatCard(stats_row, "% BLOQUEADO", e, ROL_MID)
        self.card_domains = StatCard(stats_row, "LISTA",       e, ROL_COLOR2)

        for card in (self.card_queries, self.card_blocked,
                     self.card_percent, self.card_domains):
            card.pack(side="left", expand=True, fill="x", padx=2)

        self._sep(self, e)

        # Footer
        bottom_bar = tk.Frame(self, bg=e.bg, height=20)
        etiquetar(bottom_bar, ROL_BG)
        bottom_bar.pack(fill="x", side="bottom")
        bottom_bar.pack_propagate(False)

        self.status_dot = StatusDot(bottom_bar, label="Pi-hole", estilo=e)
        self.status_dot.pack(side="right", padx=8)

        self._ts_label = tk.Label(bottom_bar, text="",
                                  bg=e.bg, fg=e.muted, font=("monospace", 7))
        etiquetar(self._ts_label, ROL_BG, ROL_MUTED)
        self._ts_label.pack(side="left", padx=8)

        # Body
        body = tk.Frame(self, bg=e.bg)
        etiquetar(body, ROL_BG)
        body.pack(fill="both", padx=4, pady=4)

        # Columna izquierda
        left = tk.Frame(body, bg=e.bg2, width=190)
        etiquetar(left, ROL_BG2)
        left.pack(side="left", fill="y", padx=(0, 3))
        left.pack_propagate(False)

        top_container = tk.Frame(left, bg=e.bg2, height=90)
        etiquetar(top_container, ROL_BG2)
        top_container.pack(fill="x")
        top_container.pack_propagate(False)

        lbl_tb = tk.Label(top_container, text="TOP BLOQUEADOS",
                          bg=e.bg2, fg=e.muted, font=("monospace", 7))
        etiquetar(lbl_tb, ROL_BG2, ROL_MUTED)
        lbl_tb.pack(anchor="w", padx=8, pady=(6, 2))

        top_scroll = ScrollFrame(top_container, e.bg2)
        top_scroll.pack(fill="both", expand=True)
        self.top_blocked_list = DeviceList(top_scroll.inner, estilo=e)
        self.top_blocked_list.pack(fill="x")

        self._sep(left, e)

        client_container = tk.Frame(left, bg=e.bg2, height=90)
        etiquetar(client_container, ROL_BG2)
        client_container.pack(fill="both", expand=True)
        client_container.pack_propagate(False)

        lbl_cl = tk.Label(client_container, text="TOP CLIENTES HOY",
                          bg=e.bg2, fg=e.muted, font=("monospace", 7))
        etiquetar(lbl_cl, ROL_BG2, ROL_MUTED)
        lbl_cl.pack(anchor="w", padx=8, pady=(4, 2))

        client_scroll = ScrollFrame(client_container, e.bg2)
        client_scroll.pack(fill="both", expand=True)
        self.clients_list = DeviceList(client_scroll.inner, estilo=e)
        self.clients_list.pack(fill="x")

        # Columna derecha
        right = tk.Frame(body, bg=e.bg2)
        etiquetar(right, ROL_BG2)
        right.pack(side="left", fill="both", expand=True)

        lbl_chart = tk.Label(right, text="QUERIES ÚLTIMAS 24H",
                             bg=e.bg2, fg=e.muted, font=("monospace", 7))
        etiquetar(lbl_chart, ROL_BG2, ROL_MUTED)
        lbl_chart.pack(anchor="w", padx=8, pady=(6, 2))

        chart_scroll = ScrollFrameXY(right, e.bg2)
        chart_scroll.pack(fill="both", expand=True)

        self.chart = BarChart(chart_scroll.inner, width=270, height=118,
                              bg=e.bg2, label_color=e.muted)
        self.chart.pack(padx=6, pady=(0, 4))

        legend = tk.Frame(chart_scroll.inner, bg=e.bg2)
        etiquetar(legend, ROL_BG2)
        legend.pack(anchor="w", padx=8)

        # Guardar referencias a los círculos de la leyenda
        self.legend_dots = []
        for color_attr, label in ((e.colorok, "permitidas"), (e.colorbad, "bloqueadas")):
            dot = tk.Canvas(legend, width=8, height=8,
                            bg=e.bg2, highlightthickness=0)
            etiquetar(dot, ROL_BG2)
            dot.create_oval(1, 1, 7, 7, fill=color_attr, outline="")
            dot.pack(side="left", padx=(0, 2))
            self.legend_dots.append(dot)
            
            lbl = tk.Label(legend, text=label, bg=e.bg2, fg=e.muted,
                           font=("monospace", 7))
            etiquetar(lbl, ROL_BG2, ROL_MUTED)
            lbl.pack(side="left", padx=(0, 8))

    # ── Refresh ───────────────────────────────────────────────────────────────

    def _refresh(self):
        try:
            self._update_stats()
            self._update_top_blocked()
            self._update_clients()
            self._update_chart()
            self.topbar.tick()
            self._ts_label.config(text=repo.get_last_updated())
        except Exception as ex:
            self._ts_label.config(text=f"error: {ex}")
        finally:
            self.after(REFRESH_MS, self._refresh)

    def _update_stats(self):
        s = self.estilo
        data = repo.get_latest_stats()
        self.card_queries.set_value(f"{data['queries_today']:,}")
        self.card_blocked.set_value(f"{data['blocked_today']:,}")
        self.card_percent.set_value(f"{data['percent_blocked']:.1f}%")
        d = data["domains_blocklist"]
        self.card_domains.set_value(f"{d // 1000}k" if d >= 1000 else str(d))
        self.status_dot.set_status(data.get("status") == "enabled")
        self.status_dot.refresh_dot(s)

    def _update_top_blocked(self):
        items = repo.get_top_blocked(limit=5)
        self.top_blocked_list.set_items([
            {"primary": _truncate(d["domain"], 22), "secondary": str(d["count"])}
            for d in items
        ])

    def _update_clients(self):
        clients = repo.get_top_clients(limit=4)
        self.clients_list.set_items([
            {"primary": _truncate(c["name"], 18), "secondary": str(c["count"])}
            for c in clients
        ])

    def _update_chart(self):
        history = repo.get_history_24h()
        labels  = [h["label"] for h in history]
        allowed = [max(0, h["queries"] - h["blocked"]) for h in history]
        blocked = [h["blocked"] for h in history]
        self.chart.update_data(
            labels=labels,
            series={"permitidas": allowed, "bloqueadas": blocked},
            colors={
                "permitidas": self.estilo.colorok,
                "bloqueadas": self.estilo.colorbad,
            },
        )

    def _open_themes(self):
        ThemeSelector(self, self)

    @staticmethod
    def _sep(parent, estilo):
        sep = tk.Frame(parent, bg=estilo.border, height=1)
        sep._bg_rol = ROL_BORDER
        sep.pack(fill="x")


def _truncate(text: str, max_len: int) -> str:
    return text if len(text) <= max_len else text[:max_len - 1] + "…"


if __name__ == "__main__":
    app = PiholeMonitorApp()
    app.mainloop()