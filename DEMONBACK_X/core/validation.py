"""Input validation helpers used by all forms."""
from __future__ import annotations

import re


def require_text(value: str, field: str, max_len: int = 200) -> str:
    v = (value or "").strip()
    if not v:
        raise ValueError(f"{field} is required.")
    if len(v) > max_len:
        raise ValueError(f"{field} is too long (max {max_len} characters).")
    return v


def parse_int(value, field: str, lo: int, hi: int, default: int | None = None) -> int:
    try:
        n = int(str(value).strip())
    except (TypeError, ValueError):
        if default is not None:
            return default
        raise ValueError(f"{field} must be a whole number.")
    if n < lo or n > hi:
        raise ValueError(f"{field} must be between {lo} and {hi}.")
    return n


def parse_float(value, field: str, lo: float, hi: float,
                default: float | None = None) -> float:
    try:
        n = float(str(value).strip())
    except (TypeError, ValueError):
        if default is not None:
            return default
        raise ValueError(f"{field} must be a number.")
    if n < lo or n > hi:
        raise ValueError(f"{field} must be between {lo:g} and {hi:g}.")
    return n


DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def valid_iso_date(value: str, field: str) -> str:
    from datetime import date
    v = (value or "").strip()
    if not DATE_RE.match(v):
        raise ValueError(f"{field} must be in YYYY-MM-DD format.")
    try:
        date.fromisoformat(v)
    except ValueError:
        raise ValueError(f"{field} is not a real calendar date.")
    return v


def valid_pin(value: str) -> str:
    v = (value or "").strip()
    if v == "":
        return ""                       # empty means "no PIN"
    if not v.isdigit() or not (4 <= len(v) <= 8):
        raise ValueError("PIN must be 4-8 digits.")
    return v


def valid_time_range(spec: str) -> str:
    """Validate 'HH:MM-HH:MM' quiet-hours string."""
    parts = (spec or "").strip().split("-")
    if len(parts) != 2:
        raise ValueError("Quiet hours must look like 22:00-07:00.")
    for p in parts:
        m = re.match(r"^(\d{1,2}):(\d{2})$", p.strip())
        if not m or not (0 <= int(m.group(1)) <= 23 and 0 <= int(m.group(2)) <= 59):
            raise ValueError(f"Invalid time: {p}")
    return f"{parts[0].strip()}-{parts[1].strip()}"


def safe_filename(name: str) -> str:
    return re.sub(r"[^A-Za-z0-9_\- ]", "", name or "").strip() or "export"
