# FastMDSimulation/src/fastmdsimulation/api.py

from __future__ import annotations

from typing import Optional

from .core.orchestrator import run_from_yaml
from .core.simulate import simulate_from_pdb
from .utils.logging import get_logger

logger = get_logger("api")


class FastMDSimulation:
    """
    High-level Python API for running automated MD simulations.

    Usage:
        fastmds = FastMDSimulation("protein.pdb", output="simulate_output", config=None)
        project_dir = fastmds.simulate(analyze=True, frames="0,-1,10", atoms="protein", slides=True)

    Notes:
    - `system` can be a PDB file or a YAML job file.
    - If a YAML is supplied, any `config` overrides are ignored (the YAML is the full plan).
    - Analysis hooks into FastMDAnalysis (if installed) and mirrors CLI flags.
    """

    def __init__(
        self, system: str, output: str = "simulate_output", config: Optional[str] = None
    ):
        self.system = str(system)  # .pdb or .yml/.yaml
        self.output = str(output)  # base output directory
        self.config = str(config) if config else None

    def simulate(
        self,
        analyze: bool = False,
        frames: Optional[str] = None,
        atoms: Optional[str] = None,
        slides: bool = True,
    ) -> str:
        """
        Run the simulation (and optional analysis).

        Parameters
        ----------
        analyze : bool
            If True, run FastMDAnalysis after simulation (production stage only).
        frames : Optional[str]
            Frame selection (e.g., "0,-1,10" or "200") — consistent with FastMDAnalysis.
        atoms : Optional[str]
            Atom selection string (e.g., "protein", "protein and name CA").
        slides : bool
            If True, include slide deck output in analysis.

        Returns
        -------
        str
            Absolute path to the project directory (<output>/<project>).
        """
        if self.system.lower().endswith((".yml", ".yaml")):
            if self.config:
                logger.warning(
                    "Ignoring `config`: a job YAML was supplied as `system`."
                )
            project = run_from_yaml(self.system, self.output)
        else:
            project = simulate_from_pdb(
                self.system, outdir=self.output, config=self.config
            )

        if analyze:
            try:
                from .reporting.analysis_bridge import analyze_with_bridge

                analyze_with_bridge(project, slides=slides, frames=frames, atoms=atoms)
            except Exception as e:
                logger.error(f"Analysis step failed or is unavailable: {e}")

        return project
