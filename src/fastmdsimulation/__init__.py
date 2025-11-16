# FastMDSimulation/src/fastmdsimulation/init.py

"""FastMDSimulation — Automated MD with optional FastMDAnalysis handoff."""

from .api import FastMDSimulation

# Expose package version (doesn't crash if metadata is unavailable, e.g., editable installs)
try:
    from importlib.metadata import PackageNotFoundError, version  # Python 3.8+

    try:
        __version__ = version("fastmdsimulation")
    except PackageNotFoundError:
        __version__ = "0.0.0"
except Exception:  # very old Python or unexpected env
    __version__ = "0.0.0"

__all__ = ["FastMDSimulation", "__version__"]
