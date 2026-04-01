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


class ScrollFrame(tk.Frame):
    """Scroll vertical con drag táctil."""

    def __init__(self, parent, bg):
        super().__init__(parent, bg=bg)

        self.canvas = tk.Canvas(self, bg=bg, highlightthickness=0)
        self.inner = tk.Frame(self.canvas, bg=bg)

        self.scrollbar = tk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)

        self.window = self.canvas.create_window((0, 0), window=self.inner, anchor="nw")

        self.inner.bind("<Configure>", self._on_configure)
        self.canvas.bind("<Configure>", self._on_canvas_configure)

        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        self.canvas.bind_all("<Button-4>", lambda e: self.canvas.yview_scroll(-1, "units"))
        self.canvas.bind_all("<Button-5>", lambda e: self.canvas.yview_scroll(1, "units"))

        self.canvas.bind("<ButtonPress-1>", self._on_press)
        self.canvas.bind("<B1-Motion>", self._on_drag)

        self._start_y = 0

    def _on_configure(self, event):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _on_canvas_configure(self, event):
        self.canvas.itemconfig(self.window, width=event.width)

    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _on_press(self, event):
        self._start_y = event.y

    def _on_drag(self, event):
        delta = self._start_y - event.y
        self.canvas.yview_scroll(int(delta / 2), "units")
        self._start_y = event.y


class BiScrollFrame(tk.Frame):
    """Canvas con scroll horizontal (scrollbar visible ARRIBA) +
    scroll vertical (drag táctil). El contenido se construye en self.inner."""

    def __init__(self, parent, bg):
        super().__init__(parent, bg=bg)

        # Scrollbar horizontal en la parte superior
        self._h_scroll = tk.Scrollbar(self, orient="horizontal")
        self._h_scroll.pack(side="top", fill="x")

        # Canvas que ocupa el resto del espacio
        self.canvas = tk.Canvas(self, bg=bg, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)

        # Enlace canvas ↔ scrollbar horizontal
        self._h_scroll.configure(command=self.canvas.xview)
        self.canvas.configure(xscrollcommand=self._h_scroll.set)

        # Frame interior con el contenido real
        self.inner = tk.Frame(self.canvas, bg=bg)
        self._window = self.canvas.create_window((0, 0), window=self.inner, anchor="nw")

        self.inner.bind("<Configure>", self._on_inner_configure)

        # Drag táctil: mueve en X e Y simultáneamente
        self.canvas.bind("<ButtonPress-1>", self._on_press)
        self.canvas.bind("<B1-Motion>",     self._on_drag)
        self._drag_x = 0
        self._drag_y = 0

    def _on_inner_configure(self, event):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _on_press(self, event):
        self._drag_x = event.x
        self._drag_y = event.y

    def _on_drag(self, event):
        dx = self._drag_x - event.x
        dy = self._drag_y - event.y
        self.canvas.xview_scroll(int(dx / 2), "units")
        self.canvas.yview_scroll(int(dy / 2), "units")
        self._drag_x = event.x
        self._drag_y = event.y


class PiholeMonitorApp(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Pi-hole monitor")
        self.geometry("480x280")
        self.resizable(False, False)
        self.configure(bg=COLOR_BG)
        self.overrideredirect(False)

        self._build_ui()
        self._refresh()

    def _build_ui(self):
        self.topbar = TopBar(self, title="Pi-hole monitor")
        self.topbar.pack(fill="x", side="top")
        self._sep(self)

        stats_row = tk.Frame(self, bg=COLOR_BG)
        stats_row.pack(fill="x", padx=4, pady=(4, 0))

        self.card_queries = StatCard(stats_row, label="QUERIES HOY",  color=COLOR_GREEN)
        self.card_blocked = StatCard(stats_row, label="BLOQUEADAS",   color=COLOR_RED)
        self.card_percent = StatCard(stats_row, label="% BLOQUEADO",  color=COLOR_AMBER)
        self.card_domains = StatCard(stats_row, label="LISTA",        color=COLOR_BLUE)

        for card in (self.card_queries, self.card_blocked,
                     self.card_percent, self.card_domains):
            card.pack(side="left", expand=True, fill="x", padx=2)

        self._sep(self)

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

        body = tk.Frame(self, bg=COLOR_BG)
        body.pack(fill="both", padx=4, pady=4)

        # ── Panel izquierdo (sin cambios) ─────────────────────────────────
        left = tk.Frame(body, bg=COLOR_SURFACE, width=190)
        left.pack(side="left", fill="y", padx=(0, 3))
        left.pack_propagate(False)

        top_container = tk.Frame(left, bg=COLOR_SURFACE, height=90)
        top_container.pack(fill="x")
        top_container.pack_propagate(False)

        tk.Label(
            top_container, text="TOP BLOQUEADOS",
            bg=COLOR_SURFACE, fg=COLOR_MUTED,
            font=("monospace", 7),
        ).pack(anchor="w", padx=8, pady=(6, 2))

        top_scroll = ScrollFrame(top_container, COLOR_SURFACE)
        top_scroll.pack(fill="both", expand=True)

        self.top_blocked_list = DeviceList(top_scroll.inner)
        self.top_blocked_list.pack(fill="x")

        self._sep(left)

        client_container = tk.Frame(left, bg=COLOR_SURFACE, height=90)
        client_container.pack(fill="both", expand=True)
        client_container.pack_propagate(False)

        tk.Label(
            client_container, text="TOP CLIENTES HOY",
            bg=COLOR_SURFACE, fg=COLOR_MUTED,
            font=("monospace", 7),
        ).pack(anchor="w", padx=8, pady=(4, 2))

        client_scroll = ScrollFrame(client_container, COLOR_SURFACE)
        client_scroll.pack(fill="both", expand=True)

        self.clients_list = DeviceList(client_scroll.inner)
        self.clients_list.pack(fill="x")

        # ── Panel derecho: gráfica 24h con scroll H (arriba) + V (drag) ───
        right = tk.Frame(body, bg=COLOR_SURFACE)
        right.pack(side="left", fill="both", expand=True)

        tk.Label(
            right, text="QUERIES ÚLTIMAS 24H",
            bg=COLOR_SURFACE, fg=COLOR_MUTED,
            font=("monospace", 7),
        ).pack(anchor="w", padx=8, pady=(6, 2))

        # BiScrollFrame ocupa el resto del panel derecho
        chart_scroll = BiScrollFrame(right, COLOR_SURFACE)
        chart_scroll.pack(fill="both", expand=True)

        # BarChart más ancho que el panel → activa scroll horizontal
        self.chart = BarChart(chart_scroll.inner, width=480, height=118)
        self.chart.pack(padx=6, pady=(0, 4))

        legend = tk.Frame(chart_scroll.inner, bg=COLOR_SURFACE)
        legend.pack(anchor="w", padx=8)

        for color, label in ((COLOR_BLUE, "permitidas"), (COLOR_RED, "bloqueadas")):
            dot = tk.Canvas(legend, width=8, height=8,
                            bg=COLOR_SURFACE, highlightthickness=0)
            dot.create_oval(1, 1, 7, 7, fill=color, outline="")
            dot.pack(side="left", padx=(0, 2))
            tk.Label(
                legend, text=label,
                bg=COLOR_SURFACE, fg=COLOR_MUTED,
                font=("monospace", 7)
            ).pack(side="left", padx=(0, 8))

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
                "primary":   _truncate(c["name"], 18),
                "secondary": str(c["count"]),
            }
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
            colors={"permitidas": COLOR_BLUE, "bloqueadas": COLOR_RED},
        )

    @staticmethod
    def _sep(parent):
        tk.Frame(parent, bg=COLOR_BORDER, height=1).pack(fill="x")


def _truncate(text: str, max_len: int) -> str:
    return text if len(text) <= max_len else text[:max_len - 1] + "…"


if __name__ == "__main__":
    app = PiholeMonitorApp()
    app.mainloop()
