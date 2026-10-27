"""Reusable, theme-aware UI components for DEMONBACK X.

Every component registers itself with the ThemeManager so it repaints
instantly when the user switches Light/Dark mode.
"""
from __future__ import annotations

import sys
import tkinter as tk
from datetime import date, timedelta
from typing import Callable

import customtkinter as ctk

from app.theme_manager import theme_manager


# --------------------------------------------------------------- helpers ---
def animations_on() -> bool:
    from database import db
    return db.get_setting("animations_enabled", "1") == "1"


class ThemedFrame(ctk.CTkFrame):
    """Frame that follows palette CARD / BG colors and re-themes live."""

    def __init__(self, master, role: str = "card", corner_radius: int = 10,
                 border: bool = True, **kw):
        super().__init__(master, corner_radius=corner_radius, **kw)
        self.role = role
        self.border = border
        self._apply_fn = lambda p: self.apply_theme(p)
        theme_manager.register(self._apply_fn)

    def apply_theme(self, p):
        bg = {"card": p.CARD, "bg": p.BG, "secondary": p.BG_SECONDARY,
              "elevated": p.ELEVATED, "accent_soft": p.ACCENT_SOFT}.get(self.role, p.CARD)
        self.configure(fg_color=bg,
                       border_width=1 if self.border else 0,
                       border_color=p.BORDER)

    def destroy(self):
        theme_manager.unregister(self._apply_fn)
        super().destroy()


class ThemedLabel(ctk.CTkLabel):
    def __init__(self, master, text="", level: str = "primary", size: int = 14,
                 bold: bool = False, **kw):
        super().__init__(master, text=text, font=_font(size, bold), **kw)
        self.level, self.size, self.bold = level, size, bold
        self._apply_fn = lambda p: self.apply_theme(p)
        theme_manager.register(self._apply_fn)

    def apply_theme(self, p):
        color = {"primary": p.TEXT_PRIMARY, "secondary": p.TEXT_SECONDARY,
                 "muted": p.TEXT_MUTED, "accent": p.ACCENT, "success": p.SUCCESS,
                 "warning": p.WARNING, "danger": p.ACCENT, "info": p.INFO}[self.level]
        self.configure(text_color=color)

    def set_text_level(self, level: str):
        self.level = level
        self.apply_theme(theme_manager.palette)

    def destroy(self):
        theme_manager.unregister(self._apply_fn)
        super().destroy()


def _font(size: int, bold: bool = False):
    return ctk.CTkFont(size=size, weight="bold" if bold else "normal")


class SectionTitle(ThemedLabel):
    def __init__(self, master, text="", **kw):
        super().__init__(master, text=text, level="primary", size=20, bold=True, **kw)


class StatCard(ThemedFrame):
    """Compact metric card: big value + caption + optional trend line."""

    def __init__(self, master, title: str, value="--", accent_role: str = "accent",
                 width: int = 0, **kw):
        super().__init__(master, **kw)
        self.title_text = title
        inner = ctk.CTkFrame(self, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=16, pady=12)
        self.value_lbl = ThemedLabel(inner, text=value, level="primary", size=26, bold=True,
                                     anchor="w")
        self.value_lbl.pack(anchor="w")
        self.caption_lbl = ThemedLabel(inner, text=title.upper(), level="secondary",
                                       size=11, bold=True, anchor="w")
        self.caption_lbl.pack(anchor="w", pady=(2, 0))
        self.accent_bar = ctk.CTkFrame(inner, height=3, corner_radius=2, width=44,
                                       fg_color=theme_manager.palette.ACCENT)
        self.accent_bar.pack(anchor="w", pady=(6, 0))
        if width:
            self.configure(width=width)
        self._accent_role = accent_role
        # override the label's own theming for accent colouring of bar
        orig = self._apply_fn
        self._apply_fn = lambda p: (orig(p), self._paint_accent(p))
        theme_manager.unregister(orig)
        theme_manager.register(self._apply_fn)

    def _paint_accent(self, p):
        color = getattr(p, self._accent_role.upper()) if hasattr(p, self._accent_role.upper()) \
            else p.ACCENT
        self.accent_bar.configure(fg_color=color)

    def set_value(self, value: str):
        self.value_lbl.configure(text=str(value))


class ActionButton(ctk.CTkButton):
    def __init__(self, master, text="", command=None, kind: str = "primary",
                 width: int = 140, height: int = 36, **kw):
        super().__init__(master, text=text, command=command, width=width, height=height, **kw)
        self.kind = kind
        self._apply_fn = lambda p: self.apply_theme(p)
        theme_manager.register(self._apply_fn)

    def apply_theme(self, p):
        styles = {
            "primary": (p.ACCENT, "#FFFFFF", p.ACCENT_HOVER),
            "secondary": (p.ELEVATED, p.TEXT_PRIMARY, p.CARD_HOVER),
            "ghost": ("transparent", p.TEXT_SECONDARY, p.CARD_HOVER),
            "danger": (p.ACCENT, "#FFFFFF", p.ACCENT_HOVER),
        }
        fg, tc, hv = styles[self.kind]
        self.configure(fg_color=fg, text_color=tc, hover_color=hv,
                       border_width=1 if self.kind == "secondary" else 0,
                       border_color=p.BORDER)

    def destroy(self):
        theme_manager.unregister(self._apply_fn)
        super().destroy()


class ToggleSwitch(ctk.CTkSwitch):
    def __init__(self, master, text="", command=None, **kw):
        super().__init__(master, text=text, command=command, **kw)
        self._apply_fn = lambda p: self.configure(
            fg_color=p.PROGRESS_TRACK, progress_color=p.ACCENT,
            button_color=p.TEXT_PRIMARY, button_hover_color="#FFFFFF",
            text_color=p.TEXT_PRIMARY)
        theme_manager.register(self._apply_fn)

    def destroy(self):
        theme_manager.unregister(self._apply_fn)
        super().destroy()


class ThemedEntry(ctk.CTkEntry):
    def __init__(self, master, placeholder="", width=220, **kw):
        super().__init__(master, placeholder_text=placeholder, width=width, **kw)
        self._apply_fn = lambda p: self.configure(
            fg_color=p.INPUT_BG, text_color=p.TEXT_PRIMARY,
            placeholder_text_color=p.TEXT_MUTED, border_color=p.BORDER,
            hover_color=p.BORDER_STRONG)
        theme_manager.register(self._apply_fn)

    def destroy(self):
        theme_manager.unregister(self._apply_fn)
        super().destroy()


class ThemedOptionMenu(ctk.CTkOptionMenu):
    def __init__(self, master, values, command=None, width=180, **kw):
        super().__init__(master, values=values, command=command, width=width, **kw)
        self._apply_fn = lambda p: self.configure(
            fg_color=p.ELEVATED, button_color=p.ACCENT, button_hover_color=p.ACCENT_HOVER,
            text_color=p.TEXT_PRIMARY, dropdown_fg_color=p.ELEVATED,
            dropdown_hover_color=p.ACCENT_SOFT, dropdown_text_color=p.TEXT_PRIMARY)
        theme_manager.register(self._apply_fn)

    def destroy(self):
        theme_manager.unregister(self._apply_fn)
        super().destroy()


class ThemedTextbox(ctk.CTkTextbox):
    def __init__(self, master, width=400, height=140, **kw):
        super().__init__(master, width=width, height=height, wrap="word", **kw)
        self._apply_fn = lambda p: self.configure(
            fg_color=p.INPUT_BG, text_color=p.TEXT_PRIMARY, border_color=p.BORDER,
            border_width=1)
        theme_manager.register(self._apply_fn)

    def destroy(self):
        theme_manager.unregister(self._apply_fn)
        super().destroy()


class ProgressBar(ThemedFrame):
    """Animated horizontal progress bar."""

    def __init__(self, master, height=10, **kw):
        super().__init__(master, corner_radius=height // 2, border=False, height=height, **kw)
        self.height_px = height
        self.fill = ctk.CTkFrame(self, corner_radius=height // 2, fg_color=theme_manager.palette.ACCENT)
        self._frac = 0.0
        self._target = 0.0
        self._apply_fill = lambda p: self.fill.configure(fg_color=p.ACCENT)
        theme_manager.register(lambda p: (self.apply_theme(p), self._apply_fill(p)))

    def apply_theme(self, p):
        self.configure(fg_color=p.PROGRESS_TRACK)

    def set(self, fraction: float, color: str | None = None):
        fraction = max(0.0, min(1.0, fraction))
        self._target = fraction
        if color:
            self.fill.configure(fg_color=color)
        if animations_on():
            self._animate_step()
        else:
            self._frac = fraction
            self._draw()

    def _animate_step(self):
        if not self.winfo_exists():
            return
        diff = self._target - self._frac
        if abs(diff) < 0.01:
            self._frac = self._target
            self._draw()
            return
        self._frac += diff * 0.25
        self._draw()
        self.after(16, self._animate_step)

    def _draw(self):
        w = self.winfo_width() or 100
        self.fill.place(relx=0, rely=0, relheight=1,
                        width=max(0, int(w * self._frac)))


class XPBar(ThemedFrame):
    """Rank progression bar with label."""

    def __init__(self, master, **kw):
        super().__init__(master, **kw)
        top = ctk.CTkFrame(self, fg_color="transparent")
        top.pack(fill="x", padx=12, pady=(8, 0))
        self.rank_lbl = ThemedLabel(top, text="RECRUIT", level="accent", size=13, bold=True)
        self.rank_lbl.pack(side="left")
        self.xp_lbl = ThemedLabel(top, text="0 XP", level="secondary", size=12)
        self.xp_lbl.pack(side="right")
        self.bar = ProgressBar(self, height=8)
        self.bar.pack(fill="x", padx=12, pady=(6, 10))

    def update_rank(self, rank_name: str, xp: int, into_rank: int, needed: int):
        self.rank_lbl.configure(text=rank_name.upper())
        self.xp_lbl.configure(text=f"{xp} XP" + (f" · {needed - into_rank} to next" if needed else ""))
        self.bar.set(into_rank / needed if needed else 1.0)


class Toast(ctk.CTkToplevel):
    """Small in-app notification bubble (bottom-right of parent window)."""

    QUEUE = []

    def __init__(self, master, message: str, kind: str = "info", duration: int = 3200):
        super().__init__(master)
        self.overrideredirect(True)
        try:
            self.attributes("-topmost", True)
        except tk.TclError:
            pass
        p = theme_manager.palette
        color = {"info": p.INFO, "success": p.SUCCESS, "warn": p.WARNING,
                 "error": p.ACCENT}.get(kind, p.INFO)
        frame = ctk.CTkFrame(self, fg_color=p.ELEVATED, border_width=1,
                             border_color=color, corner_radius=10)
        frame.pack(fill="both", expand=True)
        lbl = ctk.CTkLabel(frame, text=message, text_color=p.TEXT_PRIMARY,
                           font=_font(13), wraplength=340, justify="left")
        lbl.pack(padx=16, pady=10)
        self.update_idletasks()
        mw, mh = master.winfo_rootx(), master.winfo_rooty()
        ww, wh = master.winfo_width(), master.winfo_height()
        x = mw + ww - self.winfo_reqwidth() - 24
        y = mh + wh - self.winfo_reqheight() - 24 - 60 * len(Toast.QUEUE)
        self.geometry(f"+{max(mw, x)}+{max(mh, y)}")
        Toast.QUEUE.append(self)
        self.after(duration, self._close)

    def _close(self):
        if self in Toast.QUEUE:
            Toast.QUEUE.remove(self)
        try:
            self.destroy()
        except tk.TclError:
            pass


def toast(master, message: str, kind: str = "info"):
    """Show a transient themed notification bubble."""
    try:
        Toast(master, message, kind)
    except Exception as e:
        print(f"[toast] {message} ({e})", file=sys.stderr)


class ConfirmDialog(ctk.CTkToplevel):
    """Modal confirmation before destructive actions."""

    def __init__(self, master, title: str, message: str, on_yes: Callable[[], None],
                 yes_text: str = "Confirm", danger: bool = True):
        super().__init__(master)
        self.title(title)
        self.resizable(False, False)
        self.transient(master)
        self.grab_set()
        p = theme_manager.palette
        frame = ctk.CTkFrame(self, fg_color=p.CARD, corner_radius=12)
        frame.pack(fill="both", expand=True, padx=4, pady=4)
        ctk.CTkLabel(frame, text=title, font=_font(17, True),
                     text_color=p.ACCENT if danger else p.TEXT_PRIMARY).pack(pady=(18, 6))
        ctk.CTkLabel(frame, text=message, font=_font(13), text_color=p.TEXT_PRIMARY,
                     wraplength=380, justify="left").pack(padx=20, pady=(0, 14))
        btns = ctk.CTkFrame(frame, fg_color="transparent")
        btns.pack(pady=(0, 16))
        b_no = ctk.CTkButton(btns, text="Cancel", width=110, fg_color=p.ELEVATED,
                             hover_color=p.CARD_HOVER, text_color=p.TEXT_PRIMARY,
                             command=self.destroy)
        b_no.grid(row=0, column=0, padx=6)
        b_yes = ctk.CTkButton(btns, text=yes_text, width=110,
                              fg_color=p.ACCENT, hover_color=p.ACCENT_HOVER,
                              text_color="#FFFFFF",
                              command=lambda: (self.destroy(), on_yes()))
        b_yes.grid(row=0, column=1, padx=6)
        self.update_idletasks()
        x = master.winfo_rootx() + (master.winfo_width() - self.winfo_reqwidth()) // 2
        y = master.winfo_rooty() + (master.winfo_height() - self.winfo_reqheight()) // 3
        self.geometry(f"+{max(0, x)}+{max(0, y)}")


class PINDialog(ctk.CTkToplevel):
    """Modal PIN prompt for profile protection."""

    def __init__(self, master, profile_name: str, on_ok: Callable[[str], None]):
        super().__init__(master)
        self.title("Enter PIN")
        self.resizable(False, False)
        self.transient(master)
        self.grab_set()
        p = theme_manager.palette
        frame = ctk.CTkFrame(self, fg_color=p.CARD, corner_radius=12)
        frame.pack(fill="both", expand=True, padx=4, pady=4)
        ctk.CTkLabel(frame, text=f"🔒 {profile_name}", font=_font(16, True),
                     text_color=p.TEXT_PRIMARY).pack(pady=(16, 4))
        ctk.CTkLabel(frame, text="This profile is PIN protected.", font=_font(12),
                     text_color=p.TEXT_SECONDARY).pack()
        self.entry = ctk.CTkEntry(frame, show="•", width=180, fg_color=p.INPUT_BG,
                                  text_color=p.TEXT_PRIMARY, border_color=p.BORDER)
        self.entry.pack(pady=12)
        self.err = ctk.CTkLabel(frame, text="", font=_font(11), text_color=p.ACCENT)
        self.err.pack()
        btns = ctk.CTkFrame(frame, fg_color="transparent")
        btns.pack(pady=(2, 14))
        ctk.CTkButton(btns, text="Cancel", width=90, fg_color=p.ELEVATED,
                      text_color=p.TEXT_PRIMARY, command=self.destroy).grid(row=0, column=0, padx=5)

        def submit():
            pin = self.entry.get()
            if on_ok(pin):
                self.destroy()
            else:
                self.err.configure(text="Wrong PIN. Try again.")
                self.entry.delete(0, "end")

        ctk.CTkButton(btns, text="Unlock", width=90, fg_color=p.ACCENT,
                      text_color="#FFFFFF", command=submit).grid(row=0, column=1, padx=5)
        self.entry.bind("<Return>", lambda e: submit())
        self.entry.focus_force()


class HeatmapGrid(tk.Canvas):
    """Theme-aware consistency heatmap canvas (weeks x 7 days)."""

    def __init__(self, master, **kw):
        super().__init__(master, highlightthickness=0, **kw)
        self._data: dict[str, float] = {}
        self._days: list[date] = []
        self._apply_fn = lambda p: self.redraw(p)
        theme_manager.register(self._apply_fn)

    def set_data(self, day_values: dict[str, float], start: date, end: date):
        self._data = day_values
        self._days = _daterange(start, end)
        self.redraw(theme_manager.palette)

    def redraw(self, p):
        self.delete("all")
        cw, ch = 14, 14
        gap = 3
        cols = max(1, (self.winfo_width() or 700) // (cw + gap))
        # layout: rows = weekday, columns = weeks
        if not self._days:
            return
        start = self._days[0] - timedelta(days=self._days[0].weekday())
        n_weeks = min(cols, ((self._days[-1] - start).days // 7) + 1)
        for wi in range(n_weeks):
            for di in range(7):
                day = start + timedelta(days=wi * 7 + di)
                v = self._data.get(day.isoformat(), -1)
                x = wi * (cw + gap)
                y = di * (ch + gap) + 6
                if v < 0:
                    color = p.BG
                elif v == 0:
                    color = p.HEATMAP_LOW
                else:
                    t = min(1.0, v)
                    color = _blend(p.HEATMAP_LOW, p.HEATMAP_HIGH, t)
                self.create_rectangle(x, y, x + cw, y + ch, fill=color,
                                      outline=p.BORDER, tags="cell")

    def destroy(self):
        theme_manager.unregister(self._apply_fn)
        super().destroy()


def _daterange(a, b):
    from datetime import timedelta
    out = []
    d = a
    while d <= b:
        out.append(d)
        d += timedelta(days=1)
    return out


def _blend(c1: str, c2: str, t: float) -> str:
    def h(c):
        return tuple(int(c[i:i + 2], 16) for i in (1, 3, 5))
    a, b = h(c1), h(c2)
    return "#%02X%02X%02X" % tuple(round(a[i] + (b[i] - a[i]) * t) for i in range(3))


class SidebarItem(ctk.CTkButton):
    """Navigation entry in the left sidebar; shows active state + theme follow."""

    def __init__(self, master, text: str, icon: str, command, **kw):
        display = f"{icon}  {text}"
        super().__init__(master, text=display, anchor="w", height=38,
                         corner_radius=8, command=command, **kw)
        self.active = False
        self._apply_fn = lambda p: self.paint(p)
        theme_manager.register(self._apply_fn)

    def paint(self, p):
        if self.active:
            self.configure(fg_color=p.ACCENT_SOFT, text_color=p.ACCENT,
                           hover_color=p.ACCENT_SOFT)
        else:
            self.configure(fg_color="transparent", text_color=p.TEXT_SECONDARY,
                           hover_color=p.CARD_HOVER)

    def set_active(self, flag: bool):
        self.active = flag
        self.paint(theme_manager.palette)

    def destroy(self):
        theme_manager.unregister(self._apply_fn)
        super().destroy()
