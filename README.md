# FastMDSimulation

[![Tests](https://github.com/aai-research-lab/FastMDSimulation/actions/workflows/tests.yml/badge.svg)](https://github.com/aai-research-lab/FastMDSimulation/actions)
[![codecov](https://codecov.io/gh/aai-research-lab/FastMDSimulation/branch/main/graph/badge.svg)](https://codecov.io/gh/aai-research-lab/FastMDSimulation)
[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

### Automated Molecular Dynamics Simulation — with a single command 

- PDB → prepare → solvate + ions → minimize → NVT → NPT → production MD 
- Supports both **Systemic** (multiple systems) and **One-Shot** (PDB) Simulations 
- Automated post‑MD analysis via `FastMDAnalysis` (with auto-generated slide deck)  
- Runs on CPU, NVIDIA GPUs, and HPC clusters with built-in CUDA support
- Simple **CLI** for quick runs + **Python API** for custom workflows 

---

## Installation

```bash
git clone https://github.com/aai-research-lab/FastMDSimulation.git
```
```bash
cd FastMDSimulation
```

#### Create environment and install
We recommend installing `FastMDSimulation` using `mamba`. 
> If you don't have `mamba`, see **Mamba Installation** section below.
```bash
mamba env create -f environment.yml || conda env create -f environment.yml
```
```bash
conda activate fastmdsimulation
```
```bash
pip install .
```

#### [Optional] Auto-detect and install NVIDIA GPU CUDA support
```bash
./scripts/install_cuda.sh
```

### Verify Installation

#### Get help 
```bash
fastmds -h
```
```bash
fastmds simulate -h
```
#### Check available platforms
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
```
```bash
conda activate fastmdsimulation
```
---

## Mamba Installation 
If you don't have `mamba`, we recommend installing **Miniforge**. Please see **options A or B** below.

After installing **Miniforge**, initialize your shell
```bash
source "$HOME/miniforge3/etc/profile.d/conda.sh"
conda init "$(basename "$SHELL")"
exec $SHELL -l
```
```bash
mamba --version
```

If `mamba` isn’t present after installing **Miniforge**, add it with:
```bash
conda install -n base -c conda-forge mamba
```

### Option A) Install Miniforge from the command line.
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

### Option B) [Alternatively]  

**Grab the installer for your OS from the [Miniforge releases page](https://conda-forge.org/miniforge/) and run it.**
  
---

## Quick Start

### Multi-Shot (Systemic) Simulation
For simulating one or multiple systems. 
> All systems and simulation parameters are specified in a `.yml` file.
```bash
fastmds simulate -system waterbox2nm.yml
```

### One‑Shot Simulation
For simulations from a single raw PDB.
```bash
fastmds simulate -system trpcage.pdb
```
[Optionally] provide `.yml` simulation parameter overrides.
```bash
fastmds simulate -system trpcage.pdb --config config_trpcage.yml
```

> You can always add an explicit output directory with `-o <dir>` and analysis flags like `--analyze`, `--atoms`, `--frames`, `--slides`.

**Analysis flags** (only when `--analyze` is present):
- `--slides` (default **True**; set `--slides False` to disable slides)
- `--frames` (e.g., `"0,-1,10"` subsample every 10 frames; FastMDAnalysis format)
- `--atoms` (e.g., `protein`, `"protein and name CA"`)

Analysis output is streamed line‑by‑line and prefixed with `[fastmda]` in the log.

---

## Accepted Inputs 

Supply **raw PDB structures** or **parameterized systems** in a `.yml` file. 

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
Simulation parameters are specified in a `.yml` file.
### Minimal `.yml` Reference 

```yaml
project: TrpCage

defaults:
  temperature_K: 300
  timestep_fs: 2.0
  report_interval: 100
  checkpoint_interval: 500
  
stages:
  - { name: minimize,   steps: 0 }
  - { name: nvt,        steps: 5000,  ensemble: NVT }
  - { name: npt,        steps: 5000,  ensemble: NPT }
  - { name: production, steps: 10000, ensemble: NPT }

systems:
  - id: trpcage
    pdb: trpcage.pdb
```


### Comprehensive `.yml` Reference

Everything shown below is **optional**. Omitted fields fall back to sensible defaults.

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
    pdb: trpcage.pdb                     # raw PDB → PDBFixer (strict) → _build/trpcage2_fixed.pdb
    # fixed_pdb: path/to/already_fixed.pdb  # use this to skip PDBFixer
  - id: trpcage2
    pdb: trpcage.pdb

sweep:
  temperature_K: [300, 310, 320]         # for each system perform simulations at multiple temperatures
```

> **Tip:** When you enable `useSwitchingFunction`, only set `switchDistance_nm` if you also choose a `Cutoff*` nonbonded method. Passing `switchingDistance` with PME/Ewald raises an OpenMM error.

---

## Python API
### Multi-Shot (Systemic) Simulation
Simulate a 2nm water box:
```python
from fastmdsimulation import FastMDSimulation

fastmds = FastMDSimulation("waterbox2nm.yml")
fastmds.simulate()
```

### One-Shot Simulation 
Simulate Trp-cage miniprotein with post-MD analysis + auto-generated slide deck:
```python
from fastmdsimulation import FastMDSimulation

fastmds = FastMDSimulation(
    system="trpcage.pdb",
    config="config_trpcage.yml"    # optional overrides when using a PDB
)
fastmds.simulate(
    analyze=True,                         # optional
    atoms="protein",                      # optional
    slides=True                           # optional (default True)
)
```

- If `system` ends with `.yml/.yaml`, Systemic Simulation executed; `config` is ignored.
- If `system` is a `.pdb`, PDBFixer runs (strict), then a temporary `job.auto.yml` is generated and executed.

---

## Dry‑run (plan only)

Print stages, approximate ps, output dirs, and the exact `fastmda analyze` commands (when `--analyze` is present):

```bash
# YAML
fastmds simulate -system job.yml --analyze --dry-run

# PDB
fastmds simulate -system protein.pdb --config config.yml --analyze --dry-run
```

> You can add `-o <output-dir>`, `--atoms`, `--frames`, or `--slides` to both commands as needed.

---

## Expected Output
After running any simulation, you'll get:
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

- **No CUDA in `Platforms` list**  
  - **Local workstations**: Run `./scripts/install_cuda.sh` after creating the environment to auto-detect and install CUDA support.
  - **HPC/Cluster systems**: Use your system's CUDA modules (e.g., `module load cuda/11.8`) instead of the CUDA installer script.
  - **CPU-only systems**: Simulations will run on CPU - no action needed.

- **Mixed CUDA runtimes**  
  Avoid mixing module CUDA and conda `cudatoolkit` in the same job. Pick one strategy:
  - **HPC**: Use `module load cuda/X.X` + base environment (no cudatoolkit)
  - **Local**: Use `./scripts/install_cuda.sh` to install cudatoolkit in conda environment

- **CUDA installation script fails**  
  If `./scripts/install_cuda.sh` encounters issues, you can manually install:
  ```bash
  # Check available CUDA versions
  conda search -c conda-forge cudatoolkit
  
  # Install specific version (adjust as needed)
  conda install -c conda-forge cudatoolkit=11.8
  ```

- **PDBFixer failed**  
  The fixer is strict by design. Inspect the error in `fastmds.log`, repair upstream, or provide a vetted `fixed_pdb:` path.

- **Different log look**  
  `FastMDSimulation` uses a compact, icon‑and‑color console style (or `plain` if you set `defaults.log_style: plain` or `FASTMDS_LOG_STYLE=plain`).
  Project logs (`fastmds.log`) are always plain ISO timestamps.

- **Environment creation fails**  
  If `mamba` fails, it will automatically fall back to conda. For persistent issues:
  ```bash
  # Remove existing environment and retry
  conda env remove -n fastmdsimulation
  mamba env create -f environment.yml
  ```
- **Package not found after installation**  
  Ensure you've activated the environment: `conda activate fastmdsimulation` and install `FastMDSimulation`: `pip install .`

- **Analysis fails**  
  Ensure `fastmdanalysis>=1.0.0` is installed. Check fastmds.log for specific error messages.

---

## Contributing
Contributions are welcome. Please submit a Pull Request.

**Development Installation**

If you want to contribute or modify the code:
```bash
# Clone the repository
git clone https://github.com/aai-research-lab/FastMDSimulation.git
cd FastMDSimulation

# Create and activate conda environment
mamba env create -f environment.yml
conda activate fastmdsimulation

# Install in development mode
pip install -e .

# Verify installation
fastmds -h
fastmds simulate -h

# Run tests (when available)
python -m pytest tests/ -v
```

---

## Citation
If you use `FastMDSimulation` in your work, please cite:

Aina, A. (2025) "FastMDSimulation: Software for Automated Molecular Dynamics Simulation". GitHub. https://github.com/aai-research-lab/FastMDSimulation

```bibtex
@software{fastmdsimulation,
  author       = {Adekunle Aina},
  title        = {{FastMDSimulation: Software for Automated Molecular Dynamics Simulation}},
  year         = {2025},
  publisher    = {GitHub},
  url          = {https://github.com/aai-research-lab/FastMDSimulation},
  note         = {Version 0.1.0}
}
```

---

## License
``FastMDSimulation`` is licensed under the MIT license. 

---

## Acknowledgements

``FastMDSimulation`` builds upon excellent open-source libraries to provide its automated molecular dynamics capabilities and to improve workflow efficiency, usability, and reproducibility in MD simulations. We gratefully acknowledge:

- `OpenMM` for the high-performance molecular dynamics engine
- `openmmforcefields` for providing CHARMM36 and other force fields
- `PDBFixer` for structure preparation and repair
- `FastMDAnalysis` for automated analysis of MD trajectories
- `NumPy/SciPy` for efficient numerical computations

``FastMDSimulation`` also leverages the broader scientific Python ecosystem for visualization, configuration management, and user experience:

- `PyYAML` for flexible configuration management
- `Rich` for enhanced console output and logging
- `Matplotlib` (via [FastMDAnalysis](https://github.com/aai-research-lab/FastMDAnalysis)) for publication-quality figures

While building upon these robust tools, ``FastMDSimulation`` simplifies MD setup and execution for students, professionals, and researchers, especially those new to molecular dynamics. We thank the scientific Python community for their contributions to the ecosystem that make projects like this possible.




