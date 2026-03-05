"""Protein-ligand preparation helpers (OpenMM/OpenFF).

These utilities prepare validated inputs for protein-ligand simulations that
use AMBER ff14SB (protein), TIP3P (water), and OpenFF Sage 2.x (ligand)
through the OpenMM stack.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict

from ..utils.logging import get_logger
from .pdbfix import fix_pdb_with_pdbfixer

logger = get_logger("ligand")


def _detect_format(ligand_file: Path) -> str:
    ext = ligand_file.suffix.lower()
    if ext == ".sdf":
        return "sdf"
    if ext == ".mol2":
        return "mol2"
    raise ValueError(
        f"Unsupported ligand format: {ligand_file}. Use SDF or MOL2 for OpenFF Sage 2.x workflows."
    )


def prepare_protein_ligand_inputs(
    protein_pdb: str,
    ligand_file: str,
    output_dir: str,
    *,
    ph: float = 7.0,
    net_charge: int | None = None,
    ligand_name: str = "LIG",
    keep_heterogens: bool = False,
    keep_water: bool = False,
) -> Dict[str, str]:
    """
    Validate and normalize protein-ligand inputs for OpenMM/OpenFF simulation.

    The protein PDB is fixed via PDBFixer and the ligand file is validated as
    SDF/MOL2 for OpenFF Sage 2.x parameterization at simulation build time.
    """
    protein_path = Path(protein_pdb).expanduser().resolve()
    ligand_path = Path(ligand_file).expanduser().resolve()
    out = Path(output_dir).expanduser().resolve()
    out.mkdir(parents=True, exist_ok=True)

    if not protein_path.exists():
        raise FileNotFoundError(f"Protein PDB not found: {protein_path}")
    if not ligand_path.exists():
        raise FileNotFoundError(f"Ligand file not found: {ligand_path}")

    _detect_format(ligand_path)
    name = ligand_name.upper()

    fixed_protein = out / f"{protein_path.stem}_fixed.pdb"

    fix_pdb_with_pdbfixer(
        str(protein_path),
        str(fixed_protein),
        ph=ph,
        keep_heterogens=keep_heterogens,
        keep_water=keep_water,
    )

    logger.info(
        "Prepared protein-ligand inputs for OpenFF Sage 2.x: protein=%s ligand=%s",
        fixed_protein,
        ligand_path,
    )

    return {
        "pdb": str(fixed_protein),
        "ligand": str(ligand_path),
        "ligand_name": name,
        "ligand_forcefield": "openff-2.2.1",
        "ligand_net_charge": str(net_charge) if net_charge is not None else "",
        "fixed_protein": str(fixed_protein),
    }
