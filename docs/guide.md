# Simulation Guide

This guide expands on the README and quickstart with more detail on how FastMDSimulation structures simulations, runs them, and produces analysis.

## Workflows at a glance
- **Systemic (YAML)**: describe one or many systems, defaults, and staged MD plan in a single file. Best for reproducibility and sweep-style runs.
- **One-shot (PDB)**: point at a PDB (plus optional config overrides) for a fast, single-system run.
- **One-shot (protein–ligand)**: point at a protein PDB plus a ligand SDF/MOL2; the tool fixes the protein and runs with AMBER ff14SB (protein) + TIP3P (water) + OpenFF Sage 2.x (ligand) through OpenMM.
- **Dry run**: add `--dry-run` to see the resolved plan and the exact `fastmda analyze` commands (no compute).

## Pipeline anatomy
1. **Prep**: PDBFixer (strict) repairs missing atoms/residues/hydrogens; fails fast on errors. Optional pre-fixed PDBs can skip this step.
2. **Solvation + ions**: TIP3P water; salt via `defaults.ions` (`NaCl`, `KCl`, or custom `{positiveIon, negativeIon}`).
3. **Staged MD**: defaults use CHARMM36 with stages like `minimize → nvt → npt → production`. Each stage can override ensemble, steps, reporters, PLUMED.
4. **Reporting**: coordinates, velocities, checkpoints, logs per stage; optional PLUMED outputs (COLVAR, HILLS, etc.).
5. **Analysis (optional)**: if `--analyze`, FastMDAnalysis runs with your `--frames` / `--atoms` / `--slides` selections and writes reports in the project output.

## Configuration patterns (YAML)
- **Defaults block**: global MD knobs (temperature, timestep, report/checkpoint intervals, pH, ions, barostat/thermostat settings, PLUMED defaults).
- **Stages list**: ordered stages with per-stage overrides (name, steps, ensemble, reporters, PLUMED per-stage settings).
- **Systems list**: one or more systems, each with its own coordinates/parameters (PDB, Amber, GROMACS, CHARMM). Per-system overrides for pH, forcefield, ions, constraints.
- **Template usage**: start from `examples/job_full.yml` (comprehensive) or `examples/config_quick.yml` (minimal) and trim.

## Analysis details
- Trigger with `--analyze` (CLI) or `analyze=True` (API). Runs **after** MD completes.
- **Frames**: subsample with FastMDAnalysis syntax (e.g., `"0,-1,10"` or `"200"`).
- **Atoms**: MD selection strings (e.g., `protein`, `"protein and name CA"`).
- **Slides**: `--slides True|False`; defaults to True. Produces a slide deck alongside analysis outputs.
- **Output**: analysis logs are prefixed `[fastmda]` in the run log; artifacts are placed in the project output directory under each run.

## PLUMED integration
- Enable globally: `--plumed plumed.dat` (CLI) or `defaults.plumed.enabled: true` (YAML).
- Per-stage overrides: `stages[*].plumed` can flip `enabled`, change `script`, adjust `log_frequency`.
- Outputs: PLUMED writes per-stage files (e.g., COLVAR, HILLS) in the corresponding stage directory.

## Outputs and structure
- **Project root**: `<output>/<project>/` containing logs, configs, and stage subfolders.
- **Per stage**: state/data reporters, checkpoints, optional PLUMED logs, and stage-level timing.
- **Analysis** (when enabled): FastMDAnalysis reports and slides under the project directory.

## Protein–ligand usage
- Uses OpenMM-native setup with AMBER ff14SB + TIP3P + OpenFF Sage 2.x.
- CLI one-shot: `fastmds simulate -s protein.pdb --ligand ligand.sdf --ligand-charge 0 --ligand-name LIG -o simulate_output`.
- YAML: set per-system fields `ligand`, `ligand_charge`, `ligand_name`; force field is applied as ff14SB + TIP3P for protein–ligand systems.
- Example YAML: `examples/protein_ligand.yml`.
- You can retain heterogens/waters during PDB fixing with `keep_heterogens: true` / `keep_water: true` in the system entry.

## Running on clusters
- PBS/SLURM templates are in `examples/pbs_options.yml` and `examples/slurm_options.yml`; submit helpers live in `scripts/submit_pbs_with_analysis.sh` and `scripts/submit_slurm_with_analysis.sh`.
- The systemic YAML flow is scheduler-friendly: define many systems, expand, and submit.

## Troubleshooting hints
- **PDB fixing fails**: check missing residues/atoms; supply `fixed_pdb` to skip fixing if you already vetted the structure.
- **No CUDA**: runs on CPU; to add GPU support install `openmm` with CUDA (see `scripts/install_cuda.sh`).
- **Analysis mismatch**: ensure FastMDAnalysis is installed (`pip install .[analysis]`) and that `--atoms`/`--frames` use valid selections.
