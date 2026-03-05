# FastMDSimulation — Quick Start

Minimal knobs to run **automated MD with OpenMM**, with optional analysis via **FastMDAnalysis**.

---

## CLI

### YAML-driven (recommended)
```bash
fastmds simulate -system job.yml -o simulate_output   [--analyze] [--frames "0,-1,10"] [--atoms protein] [--slides True|False] [--dry-run]
```

### One-shot from PDB
```bash
fastmds simulate -system protein.pdb -o simulate_output --config config.yml   [--analyze] [--frames "0,-1,10"] [--atoms protein] [--slides True|False] [--dry-run]
```

### One-shot protein–ligand (OpenFF Sage 2.x)
```bash
fastmds simulate -s protein.pdb --ligand ligand.sdf --ligand-charge 0 \
  --ligand-name LIG -o simulate_output
```
Notes: ligand file may be SDF or MOL2. Protein–ligand runs use AMBER ff14SB (protein) + TIP3P (water) + OpenFF Sage 2.x (ligand) through OpenMM. See `examples/protein_ligand.yml` for a minimal YAML-driven setup.

**Protein–ligand YAML example (minimal)**
```yaml
project: prot_lig
defaults:
  forcefield: ["amber14/protein.ff14SB.xml", "amber14/tip3p.xml"]
systems:
  - id: prot_lig
    pdb: protein.pdb
    ligand: ligand.sdf
    ligand_charge: 0
    ligand_name: LIG
```
Run it:
```bash
fastmds simulate -system examples/protein_ligand.yml -o simulate_output
```

**Notes**
- `-system` may also be provided as `-s` or `--system`.
- `--slides` defaults to **True**; set `--slides False` to disable.
- `--frames` uses FastMDAnalysis format (e.g., `"0,-1,10"` or `"200"`).
- `--atoms` is an MD selection string (e.g., `protein`, `"protein and name CA"`).

---

## Python API
```python
from fastmdsimulation import FastMDSimulation

fastmds = FastMDSimulation("protein.pdb", output="simulate_output", config=None)
project_dir = fastmds.simulate(analyze=True, frames="0,-1,10", atoms="protein", slides=True)

# Protein–ligand (Python API)
fastmds = FastMDSimulation(
	system="protein.pdb",
	ligand="ligand.sdf",
	ligand_charge=0,
	ligand_name="LIG",
	output="simulate_output",
)
project_dir = fastmds.simulate()
```

---

## Dry run
See the plan and the exact `fastmda analyze` commands (no compute done):
```bash
# YAML
fastmds simulate -system job.yml -o simulate_output --analyze --frames 0,-1,10 --atoms protein --dry-run

# PDB
fastmds simulate -system protein.pdb -o simulate_output --config config.yml --analyze --dry-run
```

---

## Logging
- Human-readable console logs; a file log is written to `<output>/<project>/fastmds.log`.
- `--dry-run` prints the exact `fastmda analyze` command(s) that would run.

## PLUMED (optional)
- Install (Linux/WSL recommended): `mamba install -c conda-forge openmm-plumed`.
- CLI (all stages):
	```bash
	fastmds simulate -system job.yml --plumed plumed.dat --plumed-log-frequency 100
	```
- YAML (default and per-stage overrides):
	```yaml
	defaults:
	  plumed:
	    enabled: true
	    script: plumed.dat
	    log_frequency: 100
	stages:
	  - { name: nvt, steps: 5000, plumed: { enabled: true, script: stage_nvt.dat } }
	```
- Outputs (COLVAR, HILLS, etc.) are auto-written inside each stage directory.

---

## Tips
- **Ions:** choose salt in YAML via `defaults.ions: NaCl` or `KCl` (custom `{positiveIon, negativeIon}` supported).
- **PDB fixing is strict:** if PDBFixer fails, the run aborts (no silent fallback).
