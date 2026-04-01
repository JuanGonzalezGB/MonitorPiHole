"""
pihole-monitor · gui.py
Interfaz tkinter optimizada para pantalla 480×320.
Lee datos exclusivamente desde repository.py — nunca toca Mongo o la API directamente.

Layout:
  ┌─────────────────── TopBar ───────────────────┐
  │  queries  │ bloqueadas │   %   │ dominios     │  ← 4 StatCards
  ├──────────────────┬───────────────────────────┤
  │  Top dominios    │   Gráfica 24h             │
  │  bloqueados      │                           │
  ├──────────────────┤                           │
  │  Clientes        │                           │
  └──────────────────┴───────────────────────────┘
"""

import tkinter as tk
from rpicore.widgets import StatCard, BarChart, TopBar, StatusDot, DeviceList
from rpicore.config  import (
    SCREEN_W, SCREEN_H, REFRESH_MS,
    COLOR_BG, COLOR_SURFACE, COLOR_BORDER,
    COLOR_TEXT, COLOR_MUTED,
    COLOR_GREEN, COLOR_RED, COLOR_BLUE, COLOR_AMBER,
)
import repository as repo


class PiholeMonitorApp(tk.Tk):
    def __init__(self):
        super().__init__()

        # ── Ventana ────────────────────────────────────────────────────────
        self.title("Pi-hole monitor")
        self.geometry("480x280")
        self.resizable(False, False)
        self.configure(bg=COLOR_BG)
        self.overrideredirect(False)   # sin bordes de ventana en la Pi

        self._build_ui()
        self._refresh()               # primera carga inmediata

    # ── Construcción del UI ───────────────────────────────────────────────────

    def _build_ui(self):
        # TopBar
        self.topbar = TopBar(self, title="Pi-hole monitor")
        self.topbar.pack(fill="x", side="top")

        self._sep(self)

        # Fila de StatCards
        stats_row = tk.Frame(self, bg=COLOR_BG)
        stats_row.pack(fill="x", padx=4, pady=(4, 0))

        self.card_queries  = StatCard(stats_row, label="QUERIES HOY",  color=COLOR_GREEN)
        self.card_blocked  = StatCard(stats_row, label="BLOQUEADAS",   color=COLOR_RED)
        self.card_percent  = StatCard(stats_row, label="% BLOQUEADO",  color=COLOR_AMBER)
        self.card_domains  = StatCard(stats_row, label="LISTA",        color=COLOR_BLUE)

        for card in (self.card_queries, self.card_blocked,
                     self.card_percent, self.card_domains):
            card.pack(side="left", expand=True, fill="both", padx=2)

        self._sep(self)

        # Cuerpo principal: columna izquierda + gráfica derecha
        body = tk.Frame(self, bg=COLOR_BG)
        body.pack(fill="both", expand=True, padx=4, pady=4)

        # ── Columna izquierda ──────────────────────────────────────────────
        left = tk.Frame(body, bg=COLOR_SURFACE, width=190)
        left.pack(side="left", fill="y", padx=(0, 3))
        left.pack_propagate(False)

        tk.Label(
            left, text="TOP BLOQUEADOS",
            bg=COLOR_SURFACE, fg=COLOR_MUTED,
            font=("monospace", 7),
        ).pack(anchor="w", padx=8, pady=(6, 2))

        self.top_blocked_list = DeviceList(left)
        self.top_blocked_list.pack(fill="x")

        self._sep(left)

        tk.Label(
            left, text="CLIENTES ACTIVOS",
            bg=COLOR_SURFACE, fg=COLOR_MUTED,
            font=("monospace", 7),
        ).pack(anchor="w", padx=8, pady=(4, 2))

        self.clients_list = DeviceList(left)
        self.clients_list.pack(fill="x")

        # ── Columna derecha: gráfica ───────────────────────────────────────
        right = tk.Frame(body, bg=COLOR_SURFACE)
        right.pack(side="left", fill="both", expand=True)

        tk.Label(
            right, text="QUERIES ÚLTIMAS 24H",
            bg=COLOR_SURFACE, fg=COLOR_MUTED,
            font=("monospace", 7),
        ).pack(anchor="w", padx=8, pady=(6, 2))

        self.chart = BarChart(right, width=270, height=118)
        self.chart.pack(padx=6, pady=(0, 4))

        # leyenda de colores
        legend = tk.Frame(right, bg=COLOR_SURFACE)
        legend.pack(anchor="w", padx=8)
        for color, label in ((COLOR_BLUE, "permitidas"), (COLOR_RED, "bloqueadas")):
            dot = tk.Canvas(legend, width=8, height=8,
                            bg=COLOR_SURFACE, highlightthickness=0)
            dot.create_oval(1, 1, 7, 7, fill=color, outline="")
            dot.pack(side="left", padx=(0, 2))
            tk.Label(legend, text=label, bg=COLOR_SURFACE, fg=COLOR_MUTED,
                     font=("monospace", 7)).pack(side="left", padx=(0, 8))

        # StatusDot en la esquina inferior derecha
        bottom_bar = tk.Frame(self, bg=COLOR_BG, height=20)
        bottom_bar.pack(fill="x", side="bottom")
        bottom_bar.pack_propagate(False)

        self.status_dot = StatusDot(bottom_bar, label="Pi-hole")
        self.status_dot.pack(side="right", padx=8)

        self._ts_label = tk.Label(
            bottom_bar, text="",
            bg=COLOR_BG, fg=COLOR_MUTED,
            font=("monospace", 7),
        )
        self._ts_label.pack(side="left", padx=8)

    # ── Refresh ───────────────────────────────────────────────────────────────

    def _refresh(self):
        try:
            self._update_stats()
            self._update_top_blocked()
            self._update_clients()
            self._update_chart()
            self.topbar.tick()
            self._ts_label.config(text=repo.get_last_updated())
        except Exception as e:
            self._ts_label.config(text=f"error: {e}")
        finally:
            self.after(REFRESH_MS, self._refresh)

    def _update_stats(self):
        s = repo.get_latest_stats()
        self.card_queries.set_value(f"{s['queries_today']:,}")
        self.card_blocked.set_value(f"{s['blocked_today']:,}")
        self.card_percent.set_value(f"{s['percent_blocked']:.1f}%")
        domains = s["domains_blocklist"]
        self.card_domains.set_value(
            f"{domains // 1000}k" if domains >= 1000 else str(domains)
        )
        self.status_dot.set_status(s.get("status") == "enabled")

    def _update_top_blocked(self):
        items = repo.get_top_blocked(limit=5)
        max_count = items[0]["count"] if items else 1
        self.top_blocked_list.set_items([
            {
                "primary":   _truncate(d["domain"], 22),
                "secondary": str(d["count"]),
            }
            for d in items
        ])

    def _update_clients(self):
        clients = repo.get_top_clients(limit=4)
        self.clients_list.set_items([
            {
                "primary":   _truncate(c["alias"], 18),
                "secondary": str(c["count"]),
            }
            for c in clients
        ])

    def _update_chart(self):
        history = repo.get_history_24h()
        labels  = [h["label"] for h in history]
        allowed = [max(0, h["queries"] - h["blocked"]) for h in history]
        blocked = [h["blocked"] for h in history]

        # Mostrar solo cada 2h para no saturar el eje
        display_labels = [l if i % 2 == 0 else "" for i, l in enumerate(labels)]

        self.chart.update_data(
            labels=display_labels,
            series={"permitidas": allowed, "bloqueadas": blocked},
            colors={"permitidas": COLOR_BLUE, "bloqueadas": COLOR_RED},
        )

    # ── Helpers ───────────────────────────────────────────────────────────────

    @staticmethod
    def _sep(parent):
        tk.Frame(parent, bg=COLOR_BORDER, height=1).pack(fill="x")


def _truncate(text: str, max_len: int) -> str:
    return text if len(text) <= max_len else text[:max_len - 1] + "…"


if __name__ == "__main__":
    app = PiholeMonitorApp()
    app.mainloop()
