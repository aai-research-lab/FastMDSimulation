# FastMDSimulation/src/fastmdsimulation/reporting/analysis_bridge.py

import importlib.util
import subprocess
import sys
from pathlib import Path
from typing import Optional

from ..utils.logging import get_logger


def _get_production_stage(run_dir: Path) -> Optional[Path]:
    prod = run_dir / "production"
    traj, top = prod / "traj.dcd", prod / "topology.pdb"
    if prod.is_dir() and traj.exists() and top.exists():
        return prod
    return None


def iter_runs_with_production(project_dir: Path):
    for run in sorted([p for p in project_dir.iterdir() if p.is_dir()]):
        prod = _get_production_stage(run)
        if prod:
            yield run, prod, prod / "traj.dcd", prod / "topology.pdb"


def build_analyze_cmd(
    traj: Path, top: Path, *, slides: bool, frames: str | None, atoms: str | None
) -> list[str]:
    cmd = ["fastmda", "analyze", "-traj", str(traj), "-top", str(top)]
    if slides:
        cmd.append("--slides")
    if frames:
        cmd += ["--frames", str(frames)]
    if atoms:
        cmd += ["--atoms", str(atoms)]
    return cmd


def _run_and_stream(cmd: list[str], logger, prefix: str = "[fastmda] ") -> int:
    """
    Run a subprocess and stream its stdout/stderr lines through our logger.
    Returns the process return code.
    """
    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True,
        )
    except Exception as e:
        logger.error(f"{prefix}failed to start process: {e}")
        return 127

    assert proc.stdout is not None
    with proc.stdout:
        for line in proc.stdout:
            if line is None:
                continue
            logger.info(f"{prefix}{line.rstrip()}")
    return proc.wait()


def analyze_with_bridge(
    project_dir: str,
    *,
    slides: bool = True,
    frames: str | None = None,
    atoms: str | None = None,
) -> bool:
    logger = get_logger("analysis")
    root = Path(project_dir)
    if not root.exists():
        logger.error(f"project dir not found: {root}")
        return False

    if importlib.util.find_spec("fastmdanalysis") is None:
        logger.warning("FastMDAnalysis not installed. Install it or omit --analyze.")
        return False

    ok = False
    for run_dir, prod, traj, top in iter_runs_with_production(root):
        cmd = build_analyze_cmd(traj, top, slides=slides, frames=frames, atoms=atoms)
        logger.info("run analysis: " + " ".join(cmd))

        rc = _run_and_stream(cmd, logger, prefix="[fastmda] ")
        if rc == 0:
            ok = True
            continue  # next run

        # Fallback: python -m fastmdanalysis
        pycmd = [
            sys.executable,
            "-m",
            "fastmdanalysis",
            "analyze",
            "-traj",
            str(traj),
            "-top",
            str(top),
        ]
        if slides:
            pycmd.append("--slides")
        if frames:
            pycmd += ["--frames", str(frames)]
        if atoms:
            pycmd += ["--atoms", str(atoms)]
        logger.info("run analysis fallback: " + " ".join(pycmd))

        rc2 = _run_and_stream(pycmd, logger, prefix="[fastmda] ")
        if rc2 == 0:
            ok = True
        else:
            logger.error(f"analysis failed for {run_dir.name}: exit {rc2}")

    if not ok:
        logger.warning(
            "no production stages found or analysis failed; skipping analysis."
        )
    return ok
