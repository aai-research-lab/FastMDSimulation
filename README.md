# FastMDSimulation

Automated Molecular Dynamics Simulation — with a single command. 

- **Pipeline:** prepare → solvate + ions → minimize → NVT → NPT → production  
- **Reproducible:** YAML job files **or** one‑shot from PDB with optional overrides  
- **Analysis:** Optional post‑MD analysis via `FastMDAnalysis` (supports auto-generated slide deck)  
- **HPC‑ready:** Works on CPU, NVIDIA GPUs (CUDA), and clusters with module‑provided CUDA  
- **MD Engine:** Modern `openmm 8` that defaults to `CHARMM36` forcefile + `TIP3P` water model  
- **Dual Interface:** A simple command-line interface (CLI) and Python API. 

---

## Installation
We recommend installing `FastMDSimulation` using `mamba`. 
> If you don't have `mamba`, see **Mamba Installation** section below.
```bash
git clone https://github.com/aai-research-lab/FastMDSimulation.git
cd FastMDSimulation

# Create environment and install
mamba env create -f environment.yml || conda env create -f environment.yml
conda activate fastmdsimulation

# Optional: Auto-detect and install CUDA support
./scripts/install_cuda.sh
```

### Verify Installation

#### Help & Version
```bash
fastmds -h
fastmds simulate -h
fastmds -v
```
#### Available Platforms
```bash
python - <<'PY'
import openmm as mm
platforms = [mm.Platform.getPlatform(i).getName() for i in range(mm.Platform.getNumPlatforms())]
print('Available platforms:', platforms)
if 'CUDA' in platforms:
    print('CUDA platform available for GPU acceleration')
else:
    print('CPU-only installation - simulations will run on CPU')
PY
```

#### Platform-Specific Notes
CPU-Only Systems: Everything works without CUDA installation.

Local NVIDIA GPU: The installer will auto-detect and install CUDA support.

HPC Systems: Skip the CUDA installer and use your system's CUDA modules:
```bash
module load cuda/11.8  # Use your system's CUDA version
conda activate fastmdsimulation
```
---

## Mamba Installation 
If you don't have `mamba`, we recommend installing **Miniforge** with **Mamba**. 

#### Option A) Grab the installer for your OS from the [Miniforge releases page](https://conda-forge.org/miniforge/) and run it. 
Then: Initialize your shell
```bash
# Initialize your shell (example: zsh on macOS)
source "$HOME/miniforge3/etc/profile.d/conda.sh"
conda init "$(basename "$SHELL")"
exec $SHELL -l
mamba --version || true
conda --version
```

If `mamba` isn’t present after installing Miniforge, add it with:
```bash
conda install -n base -c conda-forge mamba
```

#### Option B) [Alternatively] Install Miniforge from the command line.
#### macOS (Apple Silicon / arm64)
```bash
curl -L -o "$HOME/Miniforge3-MacOSX-arm64.sh" \
  "https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-MacOSX-arm64.sh"
bash "$HOME/Miniforge3-MacOSX-arm64.sh" -b -p "$HOME/miniforge3"
```
#### macOS (Intel / x86_64)
```bash
curl -L -o "$HOME/Miniforge3-MacOSX-x86_64.sh" \
  "https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-MacOSX-x86_64.sh"
bash "$HOME/Miniforge3-MacOSX-x86_64.sh" -b -p "$HOME/miniforge3"
```
#### Linux (x86_64)
```bash
curl -L -o "$HOME/Miniforge3-Linux-x86_64.sh" \
  "https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-Linux-x86_64.sh"
bash "$HOME/Miniforge3-Linux-x86_64.sh" -b -p "$HOME/miniforge3"
```
#### Linux (ARM64 / aarch64)
```bash
curl -L -o "$HOME/Miniforge3-Linux-aarch64.sh" \
  "https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-Linux-aarch64.sh"
bash "$HOME/Miniforge3-Linux-aarch64.sh" -b -p "$HOME/miniforge3"
```
#### Windows (PowerShell)
```powershell
$inst = "$env:USERPROFILE\Downloads\Miniforge3-Windows-x86_64.exe"
Invoke-WebRequest -Uri "https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-Windows-x86_64.exe" -OutFile $inst
Start-Process -Wait $inst
& "$env:USERPROFILE\miniforge3\condabin\conda.bat" init powershell

# Close and reopen PowerShell, then
mamba --version || true
conda --version
```
---

## Quick Start

### Systemic simulation (Recommended for reproducibility)
Perform MD simulation of one or more systems with a single command. All systems and simulation parameters are specified in a `.yml` file.
```bash
fastmds simulate -system examples/waterbox/job.yml
```

### One‑shot simulation (from PDB)
Perform MD simulation from raw PDB with optional `.yml` simulation parameter overrides.
```bash
fastmds simulate -system examples/trpcage/trpcage.pdb --config examples/config.quick.yml
```

> You can always add an explicit output directory with `-o <dir>` and analysis flags like `--analyze`, `--atoms`, `--frames`, `--slides` as needed.

**Analysis flags** (only when `--analyze` is present):
- `--slides` (default **True**; set `--slides False` to disable slides)
- `--frames` (e.g., `"0,-1,10"` subsample; `"200"` first 200 frames; FastMDAnalysis format)
- `--atoms` (e.g., `protein`, `"protein and name CA"`)

Analysis output is streamed line‑by‑line and prefixed with `[fastmda]` in your log.

---

## Accepted Inputs 

Supply **raw PDB structures** or **parameterized systems** in a `.yml` file. The orchestrator normalizes each entry and the engine dispatches to the right OpenMM loader.

### PDB route (auto‑prepared by FastMDSimulation)
```yaml
systems:
  - id: MyProt
    pdb: path/to/protein.pdb        # raw PDB → PDBFixer (strict) → *_fixed.pdb → solvate+ions → run
    # OR if you already vetted a fixed file:
    # fixed_pdb: path/to/protein_fixed.pdb  # skips PDBFixer
```
- PDB inputs are **strictly** fixed with PDBFixer (missing atoms/residues, hydrogens). Failures abort.
- After fixing, the system is **solvated (TIP3P)**, ions are added (NaCl by default), and CHARMM36 is used unless overridden.
- pH for hydrogen addition can be set via `defaults.ph` or per-system `ph` (default 7.0).

### AMBER route (already parameterized)
```yaml
systems:
  - id: MyAmber
    type: amber
    prmtop: path/to/system.prmtop
    inpcrd: path/to/system.inpcrd   # or rst7:
    # rst7: path/to/system.rst7
```

### GROMACS route (already parameterized)
```yaml
systems:
  - id: MyGro
    type: gromacs
    top: path/to/topol.top
    gro: path/to/conf.gro
    # optional
    itp: [path/to/ffcustom.itp, path/to/ligand.itp]
    include_dirs: [path/to/includes]   # these are passed to GromacsTopFile
```

### CHARMM route (already parameterized)
```yaml
systems:
  - id: MyCharmm
    type: charmm
    psf: path/to/system.psf
    # coordinates (choose one)
    crd: path/to/system.crd
    # or
    # pdb: path/to/system.pdb
    # parameters (choose 'params' list OR any of prm/rtf/str)
    params: [toppar/par_all36m_prot.prm]
    # or
    # prm: [file.prm, another.prm]
    # rtf: [file.rtf]
    # str: [file.str]
```

---

## Simulation Parameters
### Minimal YAML Reference 

```yaml
project: TrpCage

defaults:
  engine: openmm
  platform: auto              # auto → CUDA → OpenCL → CPU
  temperature_K: 300
  timestep_fs: 2.0
  constraints: HBonds
  minimize_tolerance_kjmol_per_nm: 10.0
  minimize_max_iterations: 0
  report_interval: 100
  checkpoint_interval: 500
  forcefield: ["charmm36.xml", "charmm36/water.xml"]
  box_padding_nm: 1.0
  ionic_strength_molar: 0.15
  neutralize: true
  ions: NaCl                  # "NaCl" | "KCl" | {positiveIon: "K+", negativeIon: "Cl-"}
  ph: 7.0
  # integrator defaults to 'langevin'; see full reference below

stages:
  - { name: minimize,   steps: 0 }
  - { name: nvt,        steps: 5000,  ensemble: NVT }
  - { name: npt,        steps: 5000,  ensemble: NPT }
  - { name: production, steps: 10000, ensemble: NPT }

systems:
  - id: trpcage
    pdb: examples/trpcage/trpcage.pdb
```


### Comprehensive YAML Reference

Everything shown below is **optional** unless noted. Omitted fields fall back to sensible defaults.

```yaml
project: TrpCage

defaults:
  engine: openmm
  # Platform + properties
  platform: auto                        # auto → CUDA → OpenCL → CPU
  platform_properties:
    CudaPrecision: single               # or double; device‑dependent
    CudaDeviceIndex: "0"                # choose GPU id when using CUDA

  # Thermostat & integrator
  integrator:
    name: langevin_middle               # langevin | brownian | verlet | variable_langevin | variable_verlet | langevin_middle
    timestep_fs: 2.0
    friction_ps: 1.0                    # used by langevin/brownian/langevin_middle
    temperature_K: 300
    error_tolerance: 0.001              # used by variable_*

  # Barostat (used for NPT stages)
  pressure_atm: 1.0

  # Reporting
  report_interval: 1000
  checkpoint_interval: 10000

  # Preparation & FF (PDB route only)
  forcefield: ["charmm36.xml", "charmm36/water.xml"]
  box_padding_nm: 1.0
  ionic_strength_molar: 0.15
  neutralize: true
  ions: NaCl                             # "NaCl" | "KCl" | {positiveIon: "K+", negativeIon: "Cl-"}
  ph: 7.0                                # pH used by PDBFixer

  # Energy minimization
  minimize_tolerance_kjmol_per_nm: 10.0
  minimize_max_iterations: 0

  # Constraint handling (default for createSystem unless overridden there)
  constraints: HBonds                    # HBonds | AllBonds | HAngles | none

  # Pass‑through to ForceField.createSystem(...) across all routes
  create_system:
    nonbondedMethod: PME                 # NoCutoff | CutoffNonPeriodic | CutoffPeriodic | PME | Ewald
    nonbondedCutoff_nm: 1.0
    useSwitchingFunction: true           # Only meaningful for Cutoff* methods
    # switchDistance_nm: 0.9             # Only valid when useSwitchingFunction is true AND a Cutoff* method is used
    ewaldErrorTolerance: 0.0005
    constraints: HBonds                  # overrides defaults.constraints if provided
    rigidWater: true
    hydrogenMass_amu: 3.0                # HMR; enables 3–4 fs with LangevinMiddle
    longRangeDispersionCorrection: true  # maps to useDispersionCorrection
    removeCMMotion: false                # adds a CMMotionRemover force when true

  # Console logging style (file logs are always plain ISO)
  log_style: pretty                      # pretty | plain

stages:
  - { name: minimize,   steps: 25000 }                # increase if you want a deeper minimization
  - { name: nvt,        steps: 250000, ensemble: NVT }     # 500 ps @ 2 fs
  - { name: npt,        steps: 500000, ensemble: NPT }     # 1 ns
  - { name: production, steps: 1000000, ensemble: NPT }    # 2 ns

systems:
  - id: trpcage1
    pdb: examples/trpcage/trpcage.pdb    # raw PDB → PDBFixer (strict) → _build/trpcage2_fixed.pdb
    # fixed_pdb: path/to/already_fixed.pdb  # use this to skip PDBFixer
  - id: trpcage2
    pdb: examples/trpcage/trpcage.pdb

sweep:
  temperature_K: [300, 310, 320]
```

> **Tip:** When you enable `useSwitchingFunction`, only set `switchDistance_nm` if you also choose a `Cutoff*` nonbonded method. Passing `switchingDistance` with PME/Ewald raises an OpenMM error.

---

## Python API

```python
from fastmdsimulation import FastMDSimulation

fastmds = FastMDSimulation(
    "examples/trpcage/trpcage.pdb",
    output="simulate_output",             # optional
    config="examples/config.quick.yml"    # optional overrides when using a PDB
)
project_dir = fastmds.simulate(
    analyze=True,                         # optional
    atoms="protein",                      # optional
    slides=True                           # optional (default True)
)
print("Outputs in:", project_dir)
```

- If `system` ends with `.yml/.yaml`, the YAML is executed; `config` is ignored.
- If `system` is a `.pdb`, PDBFixer runs (strict), then a temporary `job.auto.yml` is generated and executed.

---

## Dry‑run (plan only)

Print stages, approximate ps, output dirs, and the exact `fastmda analyze` commands (when `--analyze` is present):

```bash
# YAML
fastmds simulate -system job.yml --analyze --dry-run

# PDB
fastmds simulate -system examples/trpcage/trpcage.pdb --config examples/config.quick.yml --analyze --dry-run
```

> You can add `-o <output-dir>`, `--atoms`, `--frames`, or `--slides` to both commands as needed.

---

## Outputs

```
<output>/<project>/
  fastmds.log                     # project log (plain text; records versions & CLI)
  inputs/                         # auto-populated provenance bundle
    job.yml
    <system-id>/                  # per-system inputs (engine-ready + originals when applicable)
      protein.pdb | *_fixed.pdb | prmtop | inpcrd | top | gro | psf | prm/rtf/str | ...
  <run_id>/                       # e.g., TrpCage_T300
    minimize/
      state.log | state.chk | stage.json | topology.pdb
    nvt/
      traj.dcd | state.log | state.chk | stage.json | topology.pdb
    npt/
      traj.dcd | state.log | state.chk | stage.json | topology.pdb
    production/
      traj.dcd | state.log | state.chk | stage.json | topology.pdb
    done.ok
  meta.json                       # start/end time, job.yml SHA256, CLI argv, versions
```

---

## Troubleshooting

- **No CUDA in `Platforms:` list**  
  On clusters, load the site CUDA module (e.g., `module load cuda/11.8`) *and* use `environment.yml` (CPU).  
  On local workstations, use `environment.gpu.yml` to bundle `cudatoolkit`.

- **Mixed CUDA runtimes**  
  Avoid mixing module CUDA and conda `cudatoolkit` in the same job. Pick one strategy.

- **PDBFixer failed**  
  The fixer is strict by design. Inspect the error in `fastmds.log`, repair upstream, or provide a vetted `fixed_pdb:` path.

- **Different log look**  
  FastMDSimulation uses a compact, icon‑and‑color console style (or `plain` if you set `defaults.log_style: plain` or `FASTMDS_LOG_STYLE=plain`).  
  Project logs (`fastmds.log`) are always plain ISO timestamps.


---

## License

MIT
