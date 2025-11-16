# FastMDSimulation/src/fastmdsimulation/core/simulate.py

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional

import yaml

from ..utils.logging import get_logger
from .pdbfix import fix_pdb_with_pdbfixer  # <-- moved here

logger = get_logger("simulate")


def _deep_update(dst: Dict[str, Any], src: Dict[str, Any]) -> Dict[str, Any]:
    for k, v in (src or {}).items():
        if isinstance(v, dict) and isinstance(dst.get(k), dict):
            _deep_update(dst[k], v)
        else:
            dst[k] = v
    return dst


def _auto_project_name(pdb_path: Path) -> str:
    return f"{pdb_path.stem}-auto"


def build_auto_config(fixed_pdb: Path, project: Optional[str] = None) -> Dict[str, Any]:
    """
    Default plan; engine will solvate/ionize. We point systems[0].pdb to the *fixed* PDB.
    """
    return {
        "project": project or _auto_project_name(Path(fixed_pdb)),
        "defaults": {
            "engine": "openmm",
            "platform": "auto",
            "temperature_K": 300,
            "timestep_fs": 2.0,
            "constraints": "HBonds",
            "minimize_tolerance_kjmol_per_nm": 10.0,
            "minimize_max_iterations": 0,
            "forcefield": ["charmm36.xml", "charmm36/water.xml"],
            "ionic_strength_molar": 0.15,
            "neutralize": True,
            "ions": "NaCl",
            "box_padding_nm": 1.0,
            "report_interval": 1000,
            "checkpoint_interval": 10000,
        },
        "stages": [
            {"name": "minimize", "steps": 0},
            {"name": "nvt", "steps": 250000, "ensemble": "NVT"},
            {"name": "npt", "steps": 500000, "ensemble": "NPT"},
            {"name": "production", "steps": 1000000, "ensemble": "NPT"},
        ],
        "systems": [
            {
                "id": "auto",
                "pdb": str(fixed_pdb),
                "forcefield": ["charmm36.xml", "charmm36/water.xml"],
            }
        ],
        "sweep": {"temperature_K": [300]},
    }


def simulate_from_pdb(
    system_pdb: str, outdir: str = "simulate_output", config: Optional[str] = None
) -> str:
    # Local import to avoid circular import at module import-time
    from .orchestrator import run_from_yaml

    system_pdb = Path(system_pdb).expanduser().resolve()
    build_dir = Path(outdir) / (_auto_project_name(system_pdb)) / "_build"
    build_dir.mkdir(parents=True, exist_ok=True)

    fixed_pdb = build_dir / f"{system_pdb.stem}_fixed.pdb"

    # STRICT: always fix
    fix_pdb_with_pdbfixer(str(system_pdb), str(fixed_pdb))

    cfg = build_auto_config(fixed_pdb, project=_auto_project_name(system_pdb))
    # record provenance of the original PDB
    cfg["systems"][0]["source_pdb"] = str(system_pdb)

    if config:
        with open(config, "r") as f:
            over = yaml.safe_load(f) or {}
        cfg = _deep_update(cfg, over)

    auto_yml = build_dir / "job.auto.yml"
    with open(auto_yml, "w") as f:
        yaml.safe_dump(cfg, f, sort_keys=False)

    project_dir = run_from_yaml(str(auto_yml), outdir)
    return project_dir
