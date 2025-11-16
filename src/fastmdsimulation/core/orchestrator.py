# FastMDSimulation/src/fastmdsimulation/core/orchestrator.py

from __future__ import annotations

import hashlib
import json
import platform
import shutil
import sys
import time
from pathlib import Path
from typing import Any, Dict, List

import yaml

try:
    # Py>=3.8
    from importlib import metadata as importlib_metadata
except Exception:
    # Fallback if needed
    import importlib_metadata  # type: ignore

from ..engines.openmm_engine import build_simulation_from_spec, run_stage
from ..utils.logging import attach_file_logger, get_logger
from .pdbfix import fix_pdb_with_pdbfixer  # strict fixer (no circular import)

logger = get_logger("orchestrator")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def _pkg_version(name: str) -> str:
    try:
        return importlib_metadata.version(name)
    except Exception:
        return "n/a"


def _collect_versions() -> Dict[str, str]:
    return {
        "fastmdsimulation": _pkg_version("fastmdsimulation"),
        "python": platform.python_version(),
        "os": platform.platform(),
        "openmm": _pkg_version("openmm"),
        "pdbfixer": _pkg_version("pdbfixer"),
        "openmmforcefields": _pkg_version("openmmforcefields"),
    }


def write_example_config(path: str) -> None:
    """
    Minimal, ready-to-run example. If you provide `pdb:`, it will be fixed
    at the specified pH (defaults.ph or system-level ph) into _build/<id>_fixed.pdb.
    If you provide `fixed_pdb:`, PDBFixer is skipped.
    """
    sample = {
        "project": "example-project",
        "defaults": {
            "engine": "openmm",
            "platform": "auto",
            "ph": 7.0,  # <-- default pH used by PDBFixer
            "temperature_K": 300,
            "timestep_fs": 2.0,
            "constraints": "HBonds",
            "minimize_tolerance_kjmol_per_nm": 10.0,
            "minimize_max_iterations": 0,
            "report_interval": 1000,
            "checkpoint_interval": 10000,
            "forcefield": ["charmm36.xml", "charmm36/water.xml"],
            "ionic_strength_molar": 0.15,
            "neutralize": True,
            "ions": "NaCl",
            "box_padding_nm": 1.0,
        },
        "stages": [
            {"name": "minimize", "steps": 0},
            {"name": "nvt", "steps": 250000, "ensemble": "NVT"},
            {"name": "npt", "steps": 500000, "ensemble": "NPT"},
            {"name": "production", "steps": 1000000, "ensemble": "NPT"},
        ],
        "systems": [
            # If you provide pdb: it will be FIXED automatically (at defaults.ph).
            # If you provide fixed_pdb: fixer is skipped.
            {"id": "protA", "pdb": "path/to/protein.pdb"}
        ],
        "sweep": {"temperature_K": [300]},
    }
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w") as f:
        yaml.safe_dump(sample, f, sort_keys=False)
    print(f"Wrote example config to {out}")


# ------------------------------
# Detection & preparation
# ------------------------------
def _detect_system_type(sys_cfg: Dict[str, Any]) -> str:
    if "fixed_pdb" in sys_cfg or "pdb" in sys_cfg:
        return "pdb"
    if "prmtop" in sys_cfg and ("inpcrd" in sys_cfg or "rst7" in sys_cfg):
        return "amber"
    if "top" in sys_cfg and ("gro" in sys_cfg or "g96" in sys_cfg):
        return "gromacs"
    if "psf" in sys_cfg and any(k in sys_cfg for k in ("params", "prm", "rtf", "str")):
        return "charmm"
    raise ValueError(f"Unrecognized system spec: {sys_cfg}")


def _prepare_systems(cfg: Dict[str, Any], base: Path) -> Dict[str, Any]:
    """
    Normalize:
      - YAML `pdb:`       → always fix (strict) to <base>/_build/{id}_fixed.pdb at given pH.
        * pH precedence: systems[i].ph → defaults.ph → 7.0
        * `source_pdb` recorded for provenance.
      - YAML `fixed_pdb:` → use as-is (skip fixer), also archived.
      - AMBER/GROMACS/CHARMM → pass-through (already parameterized).
      Annotate each with 'type'.
    """
    build_dir = base / "_build"
    build_dir.mkdir(parents=True, exist_ok=True)

    defaults = cfg.get("defaults", {}) or {}
    default_ph = float(defaults.get("ph", 7.0))

    new_cfg = dict(cfg)
    new_systems: List[Dict[str, Any]] = []
    for sys_cfg in cfg.get("systems", []):
        s = dict(sys_cfg)
        stype = _detect_system_type(s)
        s["type"] = stype

        if stype == "pdb":
            system_id = s.get("id") or Path(s.get("pdb") or s.get("fixed_pdb")).stem
            # per-system pH overrides defaults if provided
            ph = float(s.get("ph", default_ph))

            if "fixed_pdb" in s and s["fixed_pdb"]:
                used = Path(s["fixed_pdb"]).expanduser().resolve()
                s["pdb"] = str(used)  # normalize downstream to always use 'pdb'
                # keep user-declared source_pdb if any
            else:
                in_pdb = Path(s["pdb"]).expanduser().resolve()
                fixed_path = build_dir / f"{Path(system_id).stem}_fixed.pdb"
                # Strict PDBFixer — raises on failure
                fix_pdb_with_pdbfixer(str(in_pdb), str(fixed_path), ph=ph)
                s["source_pdb"] = str(in_pdb)
                s["pdb"] = str(fixed_path)
                s["fixed_pdb"] = str(fixed_path)  # record where the fixed file lives

        # amber/gromacs/charmm: pass-through
        new_systems.append(s)

    new_cfg["systems"] = new_systems
    return new_cfg


# ------------------------------
# Plan expansion
# ------------------------------
def _expand_runs(cfg: Dict[str, Any], outdir: str) -> Dict[str, Any]:
    defaults = cfg.get("defaults", {})
    project = cfg["project"]
    base = Path(outdir) / project
    temps = cfg.get("sweep", {}).get(
        "temperature_K", [defaults.get("temperature_K", 300)]
    )
    runs = []
    for sys_cfg in cfg["systems"]:
        for T in temps:
            sim_id = f'{sys_cfg.get("id","system")}_T{T}'
            simdir = base / sim_id
            run = {
                "system_id": sys_cfg.get("id", "system"),
                "temperature_K": T,
                "run_dir": str(simdir),
                "stages": cfg["stages"],
                "input": sys_cfg,  # full spec (type + files)
            }
            if "forcefield" in sys_cfg:
                run["forcefield"] = sys_cfg["forcefield"]
            runs.append(run)
    return {"project": project, "output_dir": str(base), "runs": runs}


def _steps_to_ps(steps: int, timestep_fs: float) -> float:
    return steps * timestep_fs / 1000.0


def resolve_plan(config_path: str, outdir: str) -> Dict[str, Any]:
    cfg = yaml.safe_load(open(config_path))
    plan = _expand_runs(cfg, outdir)
    tfs = float(cfg.get("defaults", {}).get("timestep_fs", 2.0))
    enriched = []
    for r in plan["runs"]:
        st = []
        for s in r["stages"]:
            steps = int(s.get("steps", 0))
            st.append(
                {
                    "name": s["name"],
                    "steps": steps,
                    "approx_ps": round(_steps_to_ps(steps, tfs), 3),
                }
            )
        r2 = dict(r)
        r2["stages"] = st
        enriched.append(r2)
    plan["runs"] = enriched
    return plan


# ------------------------------
# inputs/ archiving
# ------------------------------
def _copy_into(dst_dir: Path, src: Path) -> None:
    try:
        if not src:
            return
        p = Path(src)
        if not p.exists():
            return
        dst = dst_dir / p.name
        dst_dir.mkdir(parents=True, exist_ok=True)
        if p.resolve() == dst.resolve():
            return
        shutil.copy2(p, dst)
    except Exception as e:
        logger.warning(f"inputs/: failed to copy {src} -> {dst_dir}: {e}")


def _maybe_copy_forcefields(defaults: Dict[str, Any], inputs_dir: Path) -> None:
    ffs = defaults.get("forcefield") or []
    if not isinstance(ffs, (list, tuple)):
        ffs = [ffs]
    ff_dir = inputs_dir / "forcefields"
    ff_dir.mkdir(parents=True, exist_ok=True)
    for ff in ffs:
        try:
            p = Path(str(ff))
        except Exception:
            continue
        if p.exists() and p.is_file():
            _copy_into(ff_dir, p)


def _collect_system_paths(sys_cfg: Dict[str, Any]) -> List[Path]:
    stype = sys_cfg.get("type")
    paths: List[Path] = []
    if stype == "pdb":
        if sys_cfg.get("pdb"):
            paths.append(Path(sys_cfg["pdb"]))
        if sys_cfg.get("source_pdb"):
            paths.append(Path(sys_cfg["source_pdb"]))
        if sys_cfg.get("fixed_pdb"):
            paths.append(Path(sys_cfg["fixed_pdb"]))
    elif stype == "amber":
        for k in ("prmtop", "inpcrd", "rst7"):
            if sys_cfg.get(k):
                paths.append(Path(sys_cfg[k]))
    elif stype == "gromacs":
        for k in ("top", "gro", "g96"):
            if sys_cfg.get(k):
                paths.append(Path(sys_cfg[k]))
        itps = sys_cfg.get("itp") or []
        if isinstance(itps, (list, tuple)):
            for itp in itps:
                try:
                    paths.append(Path(itp))
                except Exception:
                    pass
    elif stype == "charmm":
        if sys_cfg.get("psf"):
            paths.append(Path(sys_cfg["psf"]))
        for k in ("params", "prm", "rtf", "str"):
            v = sys_cfg.get(k)
            if not v:
                continue
            if isinstance(v, (list, tuple)):
                paths.extend(Path(x) for x in v)
            else:
                paths.append(Path(v))
        for k in ("crd", "pdb"):
            if sys_cfg.get(k):
                paths.append(Path(sys_cfg[k]))
    return paths


def _populate_inputs(cfg: Dict[str, Any], cfg_path: Path, base: Path) -> None:
    inputs_dir = base / "inputs"
    inputs_dir.mkdir(parents=True, exist_ok=True)
    _copy_into(inputs_dir, cfg_path)
    for sys_cfg in cfg.get("systems", []):
        sid = sys_cfg.get("id", "system")
        sys_inputs = inputs_dir / sid
        for p in _collect_system_paths(sys_cfg):
            _copy_into(sys_inputs, p)
    _maybe_copy_forcefields(cfg.get("defaults", {}), inputs_dir)


# ------------------------------
# Run
# ------------------------------
def run_from_yaml(config_path: str, outdir: str) -> str:
    cfg_path = Path(config_path)
    cfg = yaml.safe_load(open(cfg_path))
    project = cfg["project"]
    defaults = cfg.get("defaults", {})
    base = Path(outdir) / project
    base.mkdir(parents=True, exist_ok=True)

    # Attach file logger and print banner + command (like FastMDAnalysis style)
    attach_file_logger(str(base / "fastmds.log"))
    versions = _collect_versions()
    logger.info(
        f"FastMDSimulation {versions['fastmdsimulation']} | Python {versions['python']} | OS {versions['os']}"
    )
    if (
        versions["openmm"] != "n/a"
        or versions["pdbfixer"] != "n/a"
        or versions["openmmforcefields"] != "n/a"
    ):
        logger.info(
            f"openmm {versions['openmm']} | pdbfixer {versions['pdbfixer']} | openmmforcefields {versions['openmmforcefields']}"
        )
    logger.info("Command: " + " ".join(sys.argv))

    logger.info(f"Project: {project}")
    logger.info(f"Output:  {base}")

    shutil.copy2(cfg_path, base / "job.yml")
    (base / "inputs").mkdir(exist_ok=True)

    # Normalize (includes fixing pdb at requested pH if needed)
    cfg = _prepare_systems(cfg, base)
    _populate_inputs(cfg, cfg_path, base)

    meta = {
        "time_start": time.time(),
        "config_sha256": sha256_file(cfg_path),
        "cli_argv": sys.argv,
        "versions": versions,
    }
    (base / "meta.json").write_text(json.dumps(meta, indent=2))

    plan = _expand_runs(cfg, outdir)

    for run in plan["runs"]:
        run_dir = Path(run["run_dir"])
        run_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f'Run: {run["system_id"]} @ {run["temperature_K"]} K -> {run_dir}')

        defaults_run = dict(defaults)
        defaults_run["temperature_K"] = run["temperature_K"]
        if run.get("forcefield"):
            defaults_run["forcefield"] = run["forcefield"]

        sim = build_simulation_from_spec(run["input"], defaults_run, run_dir)
        for st in run["stages"]:
            stage_dir = run_dir / st["name"]
            run_stage(sim, st, stage_dir, defaults_run)

        (run_dir / "done.ok").write_text("simulation completed\n")

    logger.info("All runs completed.")
    meta["time_end"] = time.time()
    (base / "meta.json").write_text(json.dumps(meta, indent=2))
    return str(base)
