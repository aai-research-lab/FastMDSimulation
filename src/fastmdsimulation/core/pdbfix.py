# FastMDSimulation/src/fastmdsimulation/core/pdbfix.py

from __future__ import annotations

from pathlib import Path

from ..utils.logging import get_logger

logger = get_logger("pdbfix")


def fix_pdb_with_pdbfixer(input_pdb: str, output_pdb: str, *, ph: float = 7.0) -> None:
    """
    Strict PDBFixer wrapper: raises on failure.
    - Removes heterogens (keeps no waters), finds/adds missing residues/atoms,
      adds hydrogens at the requested pH.
    """
    from openmm.app import PDBFile
    from pdbfixer import PDBFixer

    inp = Path(input_pdb)
    out = Path(output_pdb)
    logger.info(f"Fixing PDB with PDBFixer: {inp} (pH={ph})")
    fixer = PDBFixer(filename=str(inp))
    fixer.removeHeterogens(keepWater=False)
    fixer.findMissingResidues()
    fixer.findMissingAtoms()
    fixer.addMissingAtoms()
    fixer.addMissingHydrogens(pH=float(ph))
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w") as f:
        PDBFile.writeFile(fixer.topology, fixer.positions, f, keepIds=True)
    logger.info(f" - wrote fixed PDB to {out}")
