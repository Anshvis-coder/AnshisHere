"""Profile selection screen — two-person arena entry with PIN support."""
from __future__ import annotations

import customtkinter as ctk

from app.components import (ActionButton, ConfirmDialog, PINDialog, SectionTitle,
                            ThemedEntry, ThemedFrame, ThemedLabel, ThemedTextbox,
                            toast)
from app.theme_manager import theme_manager
from core import validation
from database import repositories as repo


class ProfileSelectScreen(ctk.CTkFrame):
    def __init__(self, master, app):
        super().__init__(master)
        self.app = app
        self.configure(fg_color="transparent")
        head = ThemedFrame(self, role="bg", border=False)
        head.pack(fill="x", padx=28, pady=(24, 6))
        SectionTitle(head, text="SELECT YOUR FIGHTER").pack(anchor="w")
        ThemedLabel(head, text="Two minds. One arena. Choose a profile to enter.",
                    level="secondary", size=13).pack(anchor="w", pady=(4, 0))

        self.grid_holder = ctk.CTkFrame(self, fg_color="transparent")
        self.grid_holder.pack(fill="both", expand=True, padx=28, pady=16)

        bottom = ctk.CTkFrame(self, fg_color="transparent")
        bottom.pack(fill="x", padx=28, pady=(0, 20))
        ActionButton(bottom, text="+ New Profile", kind="secondary", width=150,
                     command=self._new_profile_dialog).pack(side="left")
        ActionButton(bottom, text="Back", kind="ghost", width=90,
                     command=lambda: app.navigate("awakening")).pack(side="right")
        self.refresh()

    # ------------------------------------------------------------------ ui --
    def refresh(self):
        for w in self.grid_holder.winfo_children():
            w.destroy()
        profiles = [p for p in repo.Profiles.all() if p["is_active"]]
        if not profiles:
            card = ThemedFrame(self.grid_holder, role="card")
            card.grid(row=0, column=0, padx=8, pady=8, sticky="nsew")
            ThemedLabel(card, text="No fighters yet.\nCreate your first profile below.",
                        level="secondary", size=14, justify="center").pack(expand=True,
                                                                           padx=30, pady=40)
        for i, prof in enumerate(profiles):
            self.grid_holder.grid_columnconfigure(i % 2, weight=1)
            card = self._profile_card(prof)
            card.grid(row=i // 2, column=i % 2, padx=8, pady=8, sticky="nsew")
        self.grid_holder.grid_rowconfigure((0, 1), weight=1)

    def _profile_card(self, prof):
        card = ThemedFrame(self.grid_holder, role="card")
        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=22, pady=22)
        avatar = ctk.CTkLabel(inner, text=prof["name"][:1].upper(), width=64, height=64,
                              corner_radius=32, font=ctk.CTkFont(size=26, bold=True),
                              text_color="#FFFFFF", fg_color=prof["avatar_color"])
        avatar.pack()
        ThemedLabel(inner, text=prof["name"], level="primary", size=20,
                    bold=True).pack(pady=(12, 2))
        rp = self.app.rank_of(prof["id"])
        ThemedLabel(inner, text=f"{rp['rank']} · {rp['total_xp']} XP",
                    level="secondary", size=12).pack()
        btns = ctk.CTkFrame(inner, fg_color="transparent")
        btns.pack(pady=(16, 0))
        ActionButton(btns, text="Enter ▸", width=110,
                     command=lambda: self._select(prof)).grid(row=0, column=0, padx=4)
        ActionButton(btns, text="Edit", kind="secondary", width=80,
                     command=lambda: self._edit_dialog(prof)).grid(row=0, column=1, padx=4)
        return card

    # -------------------------------------------------------------- actions --
    def _select(self, prof):
        pid = prof["id"]
        if repo.Profiles.has_pin(pid):
            PINDialog(self.app, prof["name"], on_ok=lambda pin: self._pin_attempt(pid, pin))
        else:
            self.app.select_profile(pid)

    def _pin_attempt(self, pid: int, pin: str) -> bool:
        """Returns True (closing dialog) only when the PIN is correct."""
        if repo.Profiles.check_pin(pid, pin):
            self.app.select_profile(pid)
            return True
        return False

    def _new_profile_dialog(self, existing=None):
        dlg = ctk.CTkToplevel(self.app)
        dlg.title("Edit Profile" if existing else "New Profile")
        dlg.resizable(False, False)
        dlg.transient(self.app)
        dlg.grab_set()
        frame = ThemedFrame(dlg, role="card", border=False)
        frame.pack(fill="both", expand=True, padx=6, pady=6)

        ThemedLabel(frame, text="Name", level="secondary", size=12).pack(anchor="w",
                                                                        pady=(10, 2))
        name_e = ThemedEntry(frame, placeholder="Fighter name", width=280)
        name_e.pack(anchor="w")
        if existing:
            name_e.insert(0, existing["name"])

        ThemedLabel(frame, text="Personal goals", level="secondary", size=12).pack(
            anchor="w", pady=(10, 2))
        goals_t = ThemedTextbox(frame, width=280, height=70)
        goals_t.pack(anchor="w")
        if existing and existing["goals"]:
            goals_t.insert("1.0", existing["goals"])

        ThemedLabel(frame, text="Avatar colour", level="secondary", size=12).pack(
            anchor="w", pady=(10, 2))
        colors = ["#DC143C", "#4FA3DC", "#2ECC71", "#E8A33D", "#A56EE0", "#20B2AA"]
        sel = {"c": existing["avatar_color"] if existing else colors[0]}
        crow = ctk.CTkFrame(frame, fg_color="transparent")
        crow.pack(anchor="w")
        swatches = []
        for c in colors:
            b = ctk.CTkButton(crow, text="", width=30, height=30, corner_radius=15,
                              fg_color=c, hover_color=c,
                              command=lambda cc=c: set_sel(cc))
            b.pack(side="left", padx=3)
            swatches.append((c, b))

        def set_sel(cc):
            sel["c"] = cc
            for c, bb in swatches:
                bb.configure(border_width=2 if c == cc else 0,
                             border_color=theme_manager.palette.TEXT_PRIMARY)
        set_sel(sel["c"])

        ThemedLabel(frame, text="PIN (optional, 4-8 digits; leave empty for none)",
                    level="secondary", size=12).pack(anchor="w", pady=(10, 2))
        pin_e = ThemedEntry(frame, placeholder="••••", width=120, show="•")
        pin_e.pack(anchor="w")

        btns = ctk.CTkFrame(frame, fg_color="transparent")
        btns.pack(pady=14)

        def save():
            try:
                nm = validation.require_text(name_e.get(), "Name", 24)
                pin = validation.valid_pin(pin_e.get())
                goals = goals_t.get("1.0", "end")
                if existing:
                    repo.Profiles.update(existing["id"], name=nm, avatar_color=sel["c"],
                                         goals=goals)
                    if pin:
                        repo.Profiles.update(existing["id"], pin=pin)
                    toast(self.app, "Profile updated.", "success")
                else:
                    pid = repo.Profiles.create(nm, sel["c"], goals, pin)
                    toast(self.app, f"'{nm}' entered the arena.", "success")
                    if len([p for p in repo.Profiles.all() if p["is_active"]]) == 1:
                        self.app.select_profile(pid)
                dlg.destroy()
                self.refresh()
            except ValueError as e:
                toast(self.app, str(e), "error")

        ActionButton(btns, text="Save", command=save).grid(row=0, column=0, padx=5)
        ActionButton(btns, text="Cancel", kind="secondary",
                     command=dlg.destroy).grid(row=0, column=1, padx=5)
        if existing:
            def do_delete():
                ConfirmDialog(self.app, "Delete profile?",
                              f"Permanently delete '{existing['name']}' and ALL their data? "
                              "A backup is created first.",
                              on_yes=lambda: (repo.db.create_backup("pre_profile_delete"),
                                              repo.Profiles.delete(existing["id"]),
                                              self.app.forget_profile_if(existing["id"]),
                                              self.refresh(),
                                              toast(self.app, "Profile deleted.", "warn")))
                dlg.destroy()
            ActionButton(btns, text="Delete", kind="danger", width=90,
                         command=do_delete).grid(row=0, column=2, padx=5)
        name_e.focus_force()

    def _edit_dialog(self, prof):
        self._new_profile_dialog(existing=prof)
