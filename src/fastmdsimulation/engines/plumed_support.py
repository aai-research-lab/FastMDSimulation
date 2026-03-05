"""PLUMED integration for OpenMM simulations."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, Optional

from ..utils.logging import get_logger

logger = get_logger("engine.plumed")


def setup_plumed_force(
    simulation, plumed_config: Dict[str, Any], stage_dir: Path
) -> Optional[Any]:
    """
    Add PLUMED force to simulation if enabled.

    Args:
        simulation: OpenMM Simulation object
        plumed_config: PLUMED configuration dict from YAML
        stage_dir: Directory for this stage (for PLUMED output files)

    Returns:
        PlumedForce object if enabled, None otherwise
    """
    if not plumed_config.get("enabled", False):
        return None

    script_path = plumed_config.get("script")
    if not script_path:
        logger.warning("PLUMED enabled but no script provided; skipping")
        return None

    script_path = Path(script_path)
    if not script_path.exists():
        raise FileNotFoundError(f"PLUMED script not found: {script_path}")

    try:
        from openmmplumed import PlumedForce
    except ImportError:
        raise ImportError(
            "openmm-plumed not installed. Install with: "
            "conda install -c conda-forge openmm-plumed"
        )

    # Read PLUMED script
    with open(script_path, "r") as f:
        plumed_script = f.read()

    # Replace output paths to stage directory
    plumed_script = _adjust_plumed_paths(plumed_script, stage_dir)

    # Create and add PLUMED force
    plumed_force = PlumedForce(plumed_script)
    simulation.system.addForce(plumed_force)

    log_freq = plumed_config.get("log_frequency", 100)
    logger.info(f"PLUMED enabled: {script_path.name} (log every {log_freq} steps)")

    # Save adjusted script to stage directory for reference
    adjusted_script_path = stage_dir / f"plumed_{script_path.name}"
    with open(adjusted_script_path, "w") as f:
        f.write(plumed_script)
    logger.debug(f"Adjusted PLUMED script saved to: {adjusted_script_path}")

    return plumed_force


def _adjust_plumed_paths(script: str, stage_dir: Path) -> str:
    """
    Adjust PLUMED output file paths to write to stage directory.

    This ensures COLVAR, HILLS, and other PLUMED output files
    are written to the correct stage directory.
    """
    lines = []
    for line in script.splitlines():
        if "FILE=" in line:
            match = re.search(r"FILE=(\S+)", line)
            if match:
                filename = Path(match.group(1)).name
                new_path = stage_dir / filename
                line = line.replace(match.group(1), str(new_path).replace("\\", "/"))
        lines.append(line)

    return "\n".join(lines)


def merge_plumed_configs(
    defaults: Dict[str, Any], stage: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Merge default and stage-specific PLUMED configs.
    Stage-specific settings override defaults.
    """
    default_plumed = defaults.get("plumed", {})
    stage_plumed = stage.get("plumed", {})

    return {**default_plumed, **stage_plumed}
