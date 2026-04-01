"""
rpi-core · widgets.py
Componentes tkinter reutilizables optimizados para pantalla 480×320.
Todos usan el tema oscuro definido en config.py.

Componentes disponibles:
    StatCard    — tarjeta con label + valor grande + color opcional
    BarChart    — gráfica de barras sobre Canvas de tkinter
    DeviceList  — lista scrollable de dispositivos con alias
    StatusDot   — indicador de estado (verde/rojo) con label
    TopBar      — barra superior con título y timestamp
"""

import tkinter as tk
from datetime import datetime
from typing import Optional

from rpicore.config import (
    COLOR_BG, COLOR_SURFACE, COLOR_BORDER,
    COLOR_TEXT, COLOR_MUTED, COLOR_GREEN, COLOR_RED,
)


# ── StatCard ──────────────────────────────────────────────────────────────────

class StatCard(tk.Frame):
    """
    Tarjeta compacta con label arriba y valor grande abajo.
    Uso:
        card = StatCard(parent, label="Bloqueadas", color="#E24B4A")
        card.set_value("12,304")
    """

    def __init__(self, parent, label: str, color: str = COLOR_TEXT, **kwargs):
        super().__init__(parent, bg=COLOR_SURFACE, **kwargs)
        self._color = color

        self._label_var = tk.StringVar(value=label)
        self._value_var = tk.StringVar(value="—")

        tk.Label(
            self, textvariable=self._label_var,
            bg=COLOR_SURFACE, fg=COLOR_MUTED,
            font=("monospace", 7), anchor="center",
        ).pack(fill="x", padx=6, pady=(6, 0))

        tk.Label(
            self, textvariable=self._value_var,
            bg=COLOR_SURFACE, fg=color,
            font=("monospace", 16, "bold"), anchor="center",
        ).pack(fill="x", padx=6, pady=(2, 6))

    def set_value(self, value: str) -> None:
        self._value_var.set(value)

    def set_color(self, color: str) -> None:
        self._color = color
        for widget in self.winfo_children():
            if isinstance(widget, tk.Label) and widget.cget("font") != ("monospace", 7):
                widget.config(fg=color)


# ── BarChart ──────────────────────────────────────────────────────────────────

class BarChart(tk.Canvas):
    """
    Gráfica de barras apiladas sobre Canvas.
    bg y label_color se pasan en el constructor y se pueden actualizar
    llamando a config(bg=...) y set_label_color(...) al cambiar de tema.
    """

    def __init__(self, parent, width: int = 260, height: int = 110,
                 label_color: str = COLOR_MUTED, **kwargs):
        super().__init__(
            parent, width=width, height=height,
            highlightthickness=0, **kwargs,
        )
        self._chart_w     = width
        self._chart_h     = height
        self._label_color = label_color
        self._last_data: tuple | None = None   # (labels, series, colors) para redibujar

    def set_label_color(self, color: str) -> None:
        self._label_color = color
        if self._last_data:
            self.update_data(*self._last_data)

    def update_data(
        self,
        labels: list[str],
        series: dict[str, list[float]],
        colors: dict[str, str],
    ) -> None:
        self._last_data = (labels, series, colors)
        self.delete("all")
        if not labels:
            return

        n = len(labels)
        padding_x = 4
        bar_area_w = self._chart_w - padding_x * 2
        gap   = max(1, bar_area_w // (n * 6))
        bar_w = max(2, (bar_area_w - gap * (n - 1)) // n)

        totals  = [sum(s[i] for s in series.values()) for i in range(n)]
        max_val = max(totals) if max(totals) > 0 else 1
        chart_h = self._chart_h - 16

        for i, label in enumerate(labels):
            x      = padding_x + i * (bar_w + gap)
            bottom = chart_h

            for key, values in reversed(list(series.items())):
                val   = values[i] if i < len(values) else 0
                bar_h = int((val / max_val) * chart_h)
                if bar_h > 0:
                    self.create_rectangle(
                        x, bottom - bar_h, x + bar_w, bottom,
                        fill=colors.get(key, COLOR_MUTED),
                        outline="", width=0,
                    )
                    bottom -= bar_h

            if i % 2 == 0:
                self.create_text(
                    x + bar_w // 2, self._chart_h - 6,
                    text=label, fill=self._label_color,
                    font=("monospace", 6), anchor="center",
                )


# ── DeviceList ────────────────────────────────────────────────────────────────

class DeviceList(tk.Frame):
    """
    Lista compacta de dispositivos: IP (o alias) + detalle secundario.
    Uso:
        lst = DeviceList(parent, height=80)
        lst.set_items([
            {"primary": "PC principal", "secondary": "192.168.0.10"},
            {"primary": "192.168.0.99", "secondary": "desconocido"},
        ])
    """

    def __init__(self, parent, height: int = 80, **kwargs):
        super().__init__(parent, bg=COLOR_SURFACE, **kwargs)
        self._height = height
        self._rows: list[tk.Frame] = []

    def set_items(self, items: list[dict]) -> None:
        for row in self._rows:
            row.destroy()
        self._rows.clear()

        for item in items:
            row = tk.Frame(self, bg=COLOR_SURFACE)
            row.pack(fill="x", padx=8, pady=1)

            tk.Label(
                row, text=item.get("primary", ""),
                bg=COLOR_SURFACE, fg=COLOR_TEXT,
                font=("monospace", 8), anchor="w",
            ).pack(side="left")

            tk.Label(
                row, text=item.get("secondary", ""),
                bg=COLOR_SURFACE, fg=COLOR_MUTED,
                font=("monospace", 7), anchor="e",
            ).pack(side="right")

            self._rows.append(row)


# ── StatusDot ─────────────────────────────────────────────────────────────────

class StatusDot(tk.Frame):
    """
    Indicador de estado: círculo de color + texto.
    Uso:
        dot = StatusDot(parent, label="Pi-hole")
        dot.set_status(online=True)
    """

    def __init__(self, parent, label: str = "", **kwargs):
        super().__init__(parent, bg=COLOR_SURFACE, **kwargs)

        self._canvas = tk.Canvas(
            self, width=10, height=10,
            bg=COLOR_SURFACE, highlightthickness=0,
        )
        self._canvas.pack(side="left", padx=(4, 3))
        self._dot = self._canvas.create_oval(1, 1, 9, 9, fill=COLOR_MUTED, outline="")

        tk.Label(
            self, text=label,
            bg=COLOR_SURFACE, fg=COLOR_MUTED,
            font=("monospace", 8),
        ).pack(side="left")

    def set_status(self, online: bool) -> None:
        color = COLOR_GREEN if online else COLOR_RED
        self._canvas.itemconfig(self._dot, fill=color)


# ── TopBar ────────────────────────────────────────────────────────────────────

class TopBar(tk.Frame):
    """
    Barra superior con título a la izquierda y timestamp a la derecha.
    Uso:
        bar = TopBar(parent, title="Pi-hole monitor")
        bar.tick()   # actualiza el timestamp al momento actual
    """

    def __init__(self, parent, title: str = "", **kwargs):
        super().__init__(parent, bg=COLOR_SURFACE, height=28, **kwargs)
        self.pack_propagate(False)

        tk.Label(
            self, text=title,
            bg=COLOR_SURFACE, fg=COLOR_MUTED,
            font=("monospace", 8), anchor="w",
        ).pack(side="left", padx=10)

        self._ts_var = tk.StringVar(value="")
        tk.Label(
            self, textvariable=self._ts_var,
            bg=COLOR_SURFACE, fg=COLOR_MUTED,
            font=("monospace", 7), anchor="e",
        ).pack(side="right", padx=10)

    def tick(self) -> None:
        """Actualiza el timestamp al momento actual."""
        self._ts_var.set(datetime.now().strftime("%H:%M:%S"))
