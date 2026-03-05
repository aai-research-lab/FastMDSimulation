# FastMDSimulation/src/fastmdsimulation/core/pdbfix.py

from __future__ import annotations

from pathlib import Path

from ..utils.logging import get_logger

logger = get_logger("pdbfix")


def fix_pdb_with_pdbfixer(
    input_pdb: str,
    output_pdb: str,
    *,
    ph: float = 7.0,
    keep_heterogens: bool = False,
    keep_water: bool = False,
) -> None:
    """
    Strict PDBFixer wrapper: raises on failure.
    - By default removes heterogens (and waters); set keep_heterogens/keep_water to retain them.
    - Repairs missing residues/atoms and adds hydrogens at the requested pH.
    """
    from openmm.app import PDBFile
    from pdbfixer import PDBFixer

    inp = Path(input_pdb)
    out = Path(output_pdb)
    logger.info(f"Fixing PDB with PDBFixer: {inp} (pH={ph})")
    fixer = PDBFixer(filename=str(inp))
    if not keep_heterogens:
        fixer.removeHeterogens(keepWater=keep_water)
    fixer.findMissingResidues()
    fixer.findMissingAtoms()
    fixer.addMissingAtoms()
    fixer.addMissingHydrogens(pH=float(ph))
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w") as f:
        PDBFile.writeFile(fixer.topology, fixer.positions, f, keepIds=True)
    logger.info(f" - wrote fixed PDB to {out}")
