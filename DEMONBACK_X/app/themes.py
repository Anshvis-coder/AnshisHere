"""DEMONBACK X — central color palettes for Dark and Light modes.

Every screen must pull colors from the active palette via theme_manager;
hardcoded hex values inside screens are forbidden.
"""
from __future__ import annotations


class DarkPalette:
    MODE = "dark"
    # backgrounds
    BG = "#0B0B0E"               # near-black main background
    BG_SECONDARY = "#15151A"     # dark charcoal secondary
    CARD = "#1D1D24"             # card surface
    CARD_HOVER = "#26262F"
    ELEVATED = "#23232B"
    # text
    TEXT_PRIMARY = "#F2F2F4"
    TEXT_SECONDARY = "#9C9CA6"
    TEXT_MUTED = "#62626C"
    # accent
    ACCENT = "#DC143C"           # crimson
    ACCENT_HOVER = "#B0102F"
    ACCENT_SOFT = "#3A1520"      # crimson-tinted surface
    SUCCESS = "#2ECC71"
    WARNING = "#E8A33D"
    INFO = "#4FA3DC"
    # structure
    BORDER = "#2C2C34"
    BORDER_STRONG = "#3C3C46"
    PROGRESS_TRACK = "#26262E"
    TOOLTIP_BG = "#23232B"
    INPUT_BG = "#18181E"
    SCROLLBAR = "#2C2C34"
    # charts
    CHART_BG = "#1D1D24"
    CHART_GRID = "#33333C"
    CHART_SERIES = ["#DC143C", "#4FA3DC", "#2ECC71", "#E8A33D", "#A56EE0"]
    PLAYER_A = "#DC143C"
    PLAYER_B = "#4FA3DC"
    HEATMAP_LOW = "#1A1A20"
    HEATMAP_HIGH = "#DC143C"
    SHADOW = "#000000"


class LightPalette:
    MODE = "light"
    BG = "#F4F4F6"
    BG_SECONDARY = "#E9E9ED"
    CARD = "#FFFFFF"
    CARD_HOVER = "#F0EFF2"
    ELEVATED = "#FFFFFF"
    TEXT_PRIMARY = "#1E1E24"
    TEXT_SECONDARY = "#55555E"
    TEXT_MUTED = "#8A8A94"
    ACCENT = "#B01030"           # deep red / crimson tuned for light bg
    ACCENT_HOVER = "#8C0C26"
    ACCENT_SOFT = "#F8E4E8"
    SUCCESS = "#1E9E57"
    WARNING = "#B97A18"
    INFO = "#1F6FB2"
    BORDER = "#D8D8DE"
    BORDER_STRONG = "#C2C2CA"
    PROGRESS_TRACK = "#E4E4EA"
    TOOLTIP_BG = "#FFFFFF"
    INPUT_BG = "#FFFFFF"
    SCROLLBAR = "#C9C9D1"
    CHART_BG = "#FFFFFF"
    CHART_GRID = "#DDDDE3"
    CHART_SERIES = ["#B01030", "#1F6FB2", "#1E9E57", "#B97A18", "#7B4FC0"]
    PLAYER_A = "#B01030"
    PLAYER_B = "#1F6FB2"
    HEATMAP_LOW = "#EDEDF2"
    HEATMAP_HIGH = "#B01030"
    SHADOW = "#C8C8CE"


PALETTES = {"dark": DarkPalette, "light": LightPalette}
