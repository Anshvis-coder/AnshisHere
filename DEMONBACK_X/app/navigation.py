"""App shell navigation: left sidebar + screen registry."""
from __future__ import annotations

import customtkinter as ctk

from app.components import SidebarItem, ThemedFrame, ThemedLabel
from app.theme_manager import theme_manager


class Navigation(ctk.CTkFrame):
    def __init__(self, master, app):
        super().__init__(master, width=210, corner_radius=0)
        self.app = app
        self.items: dict[str, SidebarItem] = {}
        p = theme_manager.palette
        self.configure(fg_color=p.BG_SECONDARY, border_width=0)
        self._apply_fn = lambda pal: self.configure(fg_color=pal.BG_SECONDARY)
        theme_manager.register(self._apply_fn)

        # Brand -----------------------------------------------------------
        brand = ThemedFrame(self, role="bg", border=False, corner_radius=0)
        brand.pack(fill="x", padx=14, pady=(18, 10))
        ThemedLabel(brand, text="DEMONBACK X", level="accent", size=19,
                    bold=True).pack(anchor="w")
        ThemedLabel(brand, text="TWO MINDS · ONE ARENA · ZERO EXCUSES",
                    level="muted", size=9, bold=True).pack(anchor="w", pady=(1, 0))

        # Profile chip ------------------------------------------------------
        self.profile_chip = ThemedFrame(self, role="elevated")
        self.profile_chip.pack(fill="x", padx=14, pady=(6, 14))
        self.avatar = ctk.CTkLabel(self.profile_chip, text="", width=34, height=34,
                                   corner_radius=17, font=ctk.CTkFont(size=15, bold=True),
                                   text_color="#FFFFFF", fg_color=p.ACCENT)
        self.avatar.pack(side="left", padx=10, pady=8)
        self.profile_name_lbl = ThemedLabel(self.profile_chip, text="No profile",
                                           level="primary", size=13, bold=True)
        self.profile_name_lbl.pack(side="left")

        # Nav entries -------------------------------------------------------
        nav_defs = [
            ("dashboard", "Command Center", "▦"),
            ("habits", "Habit Manager", "☑"),
            ("missions", "Mission Room", "◎"),
            ("mental", "Mental Arena", "◈"),
            ("physical", "Physical Arena", "⬡"),
            ("journal", "Journal", "✎"),
            ("rivalry", "Rivalry", "⚔"),
            ("analytics", "Analytics", "📊"),
            ("settings", "Settings", "⚙"),
        ]
        for key, label, icon in nav_defs:
            btn = SidebarItem(self, label, icon,
                              command=lambda k=key: self.app.navigate(k))
            btn.pack(fill="x", padx=10, pady=2)
            self.items[key] = btn

        # Theme shortcut ----------------------------------------------------
        self.theme_btn = SidebarItem(self, "Theme: Dark", "☾",
                                     command=self._toggle_theme)
        self.theme_btn.pack(fill="x", padx=10, side="bottom", pady=(4, 2))
        self.switch_btn = SidebarItem(self, "Switch Profile", "⇄",
                                      command=lambda: self.app.show_profile_select())
        self.switch_btn.pack(fill="x", padx=10, side="bottom", pady=(2, 12))
        self._theme_apply = lambda p: self._paint_theme_btn()
        theme_manager.register(self._theme_apply)

    def _paint_theme_btn(self):
        mode = theme_manager.mode
        self.theme_btn.configure(text=("☀  Theme: Light" if mode == "light"
                                       else "☾  Theme: Dark"))

    def _toggle_theme(self):
        theme_manager.toggle()

    def set_active(self, key: str):
        for k, item in self.items.items():
            item.set_active(k == key)

    def show_profile(self, name: str, color: str):
        self.profile_name_lbl.configure(text=name)
        self.avatar.configure(text=name[:1].upper() if name else "?",
                              fg_color=color)

    def destroy(self):
        theme_manager.unregister(self._apply_fn)
        theme_manager.unregister(self._theme_apply)
        super().destroy()
