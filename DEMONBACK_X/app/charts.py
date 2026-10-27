"""Matplotlib chart canvas that re-themes instantly with the app palette."""
from __future__ import annotations

import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt                       # noqa: E402
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg  # noqa: E402

import customtkinter as ctk                           # noqa: E402

from app.theme_manager import theme_manager           # noqa: E402


class ChartFrame(ctk.CTkFrame):
    """Hosts a matplotlib Figure; `draw_fn(fig, ax, palette)` redraws on changes."""

    def __init__(self, master, draw_fn, figsize=(4.5, 3.0), **kw):
        super().__init__(master, fg_color="transparent", **kw)
        self.draw_fn = draw_fn
        self.fig = plt.Figure(figsize=figsize, dpi=100)
        self.canvas = FigureCanvasTkAgg(self.fig, master=self)
        self._widget = self.canvas.get_tk_widget()
        self._widget.pack(fill="both", expand=True, padx=6, pady=6)
        self._apply_fn = lambda p: self.redraw()
        theme_manager.register(self._apply_fn)
        self.redraw()

    def redraw(self):
        p = theme_manager.palette
        self.fig.clear()
        try:
            self.draw_fn(self.fig, p)
        except Exception as e:
            ax = self.fig.add_subplot(111)
            ax.text(0.5, 0.5, f"Chart unavailable\n{e}", ha="center",
                    color=p.TEXT_MUTED)
            for s in ax.spines.values():
                s.set_visible(False)
            ax.set_xticks([]); ax.set_yticks([])
        self.fig.patch.set_facecolor(p.CHART_BG)
        self.canvas.draw_idle()

    def destroy(self):
        theme_manager.unregister(self._apply_fn)
        plt.close(self.fig)
        super().destroy()


def style_axes(ax, palette, title: str = "", ylabel: str = "", xlabel: str = ""):
    ax.set_facecolor(palette.CHART_BG)
    ax.title.set_color(palette.TEXT_PRIMARY)
    ax.xaxis.label.set_color(palette.TEXT_SECONDARY)
    ax.yaxis.label.set_color(palette.TEXT_SECONDARY)
    ax.tick_params(colors=palette.TEXT_MUTED, labelsize=8)
    for spine in ax.spines.values():
        spine.set_color(palette.CHART_GRID)
    ax.grid(color=palette.CHART_GRID, linewidth=0.6, alpha=0.6)
    if title:
        ax.set_title(title, color=palette.TEXT_PRIMARY, fontsize=11, pad=8)
    if ylabel:
        ax.set_ylabel(ylabel, fontsize=9)
    if xlabel:
        ax.set_xlabel(xlabel, fontsize=9)
