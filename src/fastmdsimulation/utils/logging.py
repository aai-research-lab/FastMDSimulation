# FastMDSimulation/src/fastmdanalysis/utils/logging.py

import logging
import os
import sys
from datetime import datetime
from pathlib import Path

# --- Colors & icons for pretty console output ---
_COLOR = {
    "DEBUG": "\x1b[38;5;244m",
    "INFO": "\x1b[38;5;33m",
    "WARNING": "\x1b[38;5;214m",
    "ERROR": "\x1b[38;5;196m",
    "CRITICAL": "\x1b[48;5;196m\x1b[97m",
    "RESET": "\x1b[0m",
}
_ICON = {"DEBUG": "·", "INFO": "✓", "WARNING": "⚠", "ERROR": "✗", "CRITICAL": "‼"}


# ---------------------------
# Formatters
# ---------------------------
class _PrettyFormatter(logging.Formatter):
    """Compact, human-friendly formatter. Color only when stderr is a TTY."""

    def __init__(self, use_color: bool):
        super().__init__()
        self.use_color = use_color

    def format(self, record: logging.LogRecord) -> str:
        ts = datetime.fromtimestamp(record.created).strftime("%H:%M:%S")
        lvl = record.levelname
        icon = _ICON.get(lvl, "·")
        msg = record.getMessage()
        if self.use_color:
            c, r = _COLOR.get(lvl, ""), _COLOR["RESET"]
            return f"{ts} {c}{icon} {lvl:<8}{r} {msg}"
        return f"{ts} {icon} {lvl:<8} {msg}"


class _PlainISOFormatter(logging.Formatter):
    """
    ISO-ish formatter (aligns with FastMDAnalysis vibe).
    Includes date and milliseconds: YYYY-MM-DD HH:MM:SS,mmm - LEVEL - message
    """

    def __init__(self):
        fmt = "%(asctime)s - %(levelname)s - %(message)s"
        # add milliseconds like FastMDAnalysis default
        datefmt = "%Y-%m-%d %H:%M:%S"
        super().__init__(fmt=fmt, datefmt=datefmt)

    def format(self, record: logging.LogRecord) -> str:
        # Inject milliseconds as ,mmm to match typical Python logging style
        s = super().format(record)
        # If asctime already rendered, append ,mmm after seconds (best-effort)
        msec = f",{int(record.msecs):03d}"
        # Insert milliseconds if not already present
        if " - " in s:
            left, rest = s.split(" - ", 1)
            if "," not in left[-4:]:
                left = left + msec
            s = " - ".join([left, rest])
        return s


# ---------------------------
# Logger state
# ---------------------------
_console_handler: logging.Handler | None = None
_file_handler: logging.Handler | None = None


def _to_level(val) -> int:
    if isinstance(val, int):
        return val
    if isinstance(val, str):
        try:
            return getattr(logging, val.upper())
        except Exception:
            pass
    return logging.INFO


def _resolve_style(default: str | None = None) -> str:
    """Return 'pretty' or 'plain' using env FASTMDS_LOG_STYLE or provided default."""
    env = os.getenv("FASTMDS_LOG_STYLE", "").strip().lower()
    if env in ("pretty", "plain"):
        return env
    return default or "pretty"


# ---------------------------
# Public API
# ---------------------------
def setup_console(level=logging.INFO, style: str | None = None) -> logging.Logger:
    """
    Initialize console logging for the 'fastmds' logger.
    - style: 'pretty' (default) or 'plain' (ISO-like). Overridable via env FASTMDS_LOG_STYLE.
    - honors FASTMDS_LOGLEVEL (DEBUG/INFO/WARNING/ERROR/CRITICAL).
    Safe to call multiple times; won't add duplicate handlers.
    """
    global _console_handler
    base = logging.getLogger("fastmds")
    base.propagate = False

    # resolve level
    env_level = os.getenv("FASTMDS_LOGLEVEL")
    base.setLevel(_to_level(env_level) if env_level else _to_level(level))

    # resolve style
    style = _resolve_style(style)

    if _console_handler is None:
        handler = logging.StreamHandler(sys.stdout)
        if style == "plain":
            fmt = _PlainISOFormatter()
        else:
            use_color = sys.stdout.isatty() and not os.getenv("NO_COLOR")
            fmt = _PrettyFormatter(use_color)
        handler.setFormatter(fmt)
        handler.setLevel(base.level)
        base.addHandler(handler)
        _console_handler = handler
    else:
        _console_handler.setLevel(base.level)
    return base


def attach_file_logger(
    path: str, level=logging.INFO, style: str | None = "plain"
) -> logging.Logger:
    """
    Attach/replace a per-project file logger.
    - style defaults to 'plain' (ISO-like) for audit-friendly logs.
    - honors FASTMDS_LOGLEVEL.
    """
    global _file_handler
    base = logging.getLogger("fastmds")
    Path(path).parent.mkdir(parents=True, exist_ok=True)

    # Remove previous file handler if present
    if _file_handler is not None:
        try:
            base.removeHandler(_file_handler)
        except Exception:
            pass
        _file_handler = None

    handler = logging.FileHandler(path, mode="a", encoding="utf-8")

    resolved_style = _resolve_style(style)
    if resolved_style == "plain":
        fmt = _PlainISOFormatter()
    else:
        fmt = _PrettyFormatter(use_color=False)
    handler.setFormatter(fmt)

    env_level = os.getenv("FASTMDS_LOGLEVEL")
    handler.setLevel(_to_level(env_level) if env_level else _to_level(level))
    base.addHandler(handler)
    _file_handler = handler
    return base


def get_logger(name: str | None = None) -> logging.Logger:
    """Get the package logger or a namespaced child (e.g., 'engine.openmm')."""
    base = logging.getLogger("fastmds")
    return base if name is None else base.getChild(name)


def set_level(level: int | str) -> None:
    """Programmatically change the log level for all handlers."""
    lvl = _to_level(level)
    base = logging.getLogger("fastmds")
    base.setLevel(lvl)
    for h in list(base.handlers):
        try:
            h.setLevel(lvl)
        except Exception:
            pass
