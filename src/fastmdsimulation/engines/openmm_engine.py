# FastMDSimulation/src/fastmdsimulation/engines/openmm_engine.py

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Tuple

from ..utils.logging import get_logger

logger = get_logger("engine.openmm")


# ------------------------------------------------------------
# Common helpers
# ------------------------------------------------------------
def _load_forcefield(ff_files):
    from openmm.app import ForceField

    try:
        return ForceField(*ff_files)
    except Exception as e:
        try:
            import openmmforcefields  # noqa: F401

            return ForceField(*ff_files)
        except Exception:
            raise e


def _select_platform(name: str):
    from openmm import Platform

    if not name or name.lower() == "auto":
        for cand in ("CUDA", "OpenCL", "CPU"):
            try:
                return Platform.getPlatformByName(cand)
            except Exception:
                continue
        return Platform.getPlatform(0)
    return Platform.getPlatformByName(name)


def _maybe_barostat(
    system, ensemble: str, temperature_K: float, pressure_atm: float = 1.0
):
    from openmm import MonteCarloBarostat, unit

    if ensemble and ensemble.upper() == "NPT":
        system.addForce(
            MonteCarloBarostat(
                pressure_atm * unit.atmospheres, temperature_K * unit.kelvin
            )
        )


def _parse_ions(defaults: Dict[str, Any]) -> Tuple[str, str]:
    ion_cfg = defaults.get("ions", "NaCl")
    if isinstance(ion_cfg, str):
        ion_map = {"NaCl": ("Na+", "Cl-"), "KCl": ("K+", "Cl-")}
        return ion_map.get(ion_cfg, ("Na+", "Cl-"))
    if isinstance(ion_cfg, dict):
        return (ion_cfg.get("positiveIon", "Na+"), ion_cfg.get("negativeIon", "Cl-"))
    return ("Na+", "Cl-")


def _get_minimize_tolerance(defaults: Dict[str, Any]):
    from openmm import unit

    if "minimize_tolerance_kjmol_per_nm" in defaults:
        val = float(defaults["minimize_tolerance_kjmol_per_nm"])
    else:
        val = float(defaults.get("minimize_tolerance_kjmol", 10.0))
    return val * unit.kilojoule_per_mole / unit.nanometer, val


def _constraints_from_str(name: Any):
    from openmm.app import AllBonds, HAngles, HBonds

    if name is None:
        return None
    if isinstance(name, str):
        key = name.strip().lower()
        if key in ("none", "no", "off", "false"):
            return None
        if key == "hbonds":
            return HBonds
        if key == "allbonds":
            return AllBonds
        if key == "hangles":
            return HAngles
    return HBonds


# ---- NEW: map YAML -> createSystem kwargs (with units) ----
def _map_nonbonded_method(s: str):
    from openmm.app import (PME, CutoffNonPeriodic, CutoffPeriodic, Ewald,
                            NoCutoff)

    m = str(s).strip().lower()
    return {
        "nocutoff": NoCutoff,
        "cutoffnonperiodic": CutoffNonPeriodic,
        "cutoffperiodic": CutoffPeriodic,
        "pme": PME,
        "ewald": Ewald,
    }.get(m)


def _create_system_kwargs(defaults: Dict[str, Any]) -> Dict[str, Any]:
    from openmm import unit

    cs = dict(defaults.get("create_system") or {})
    out: Dict[str, Any] = {}

    # constraints: allow override here; otherwise we set it from defaults.constraints later
    if "constraints" in cs:
        out["constraints"] = _constraints_from_str(cs.get("constraints"))

    # Method
    if "nonbondedMethod" in cs:
        nm = _map_nonbonded_method(cs["nonbondedMethod"])
        if nm is None:
            raise ValueError(f"Unknown nonbondedMethod: {cs['nonbondedMethod']}")
        out["nonbondedMethod"] = nm

    # Distances (nm)
    if "nonbondedCutoff_nm" in cs:
        out["nonbondedCutoff"] = float(cs["nonbondedCutoff_nm"]) * unit.nanometer
    if "switchDistance_nm" in cs:
        out["switchingDistance"] = float(cs["switchDistance_nm"]) * unit.nanometer

    # Booleans / scalars
    for key_yaml, key_api in [
        ("useSwitchingFunction", "useSwitchingFunction"),
        ("rigidWater", "rigidWater"),
        ("longRangeDispersionCorrection", "useDispersionCorrection"),
        ("ewaldErrorTolerance", "ewaldErrorTolerance"),
    ]:
        if key_yaml in cs:
            out[key_api] = cs[key_yaml]

    # Hydrogen mass repartitioning (amu)
    if "hydrogenMass_amu" in cs:
        out["hydrogenMass"] = float(cs["hydrogenMass_amu"]) * unit.dalton

    # Non-createSystem but common request: CMMotionRemover
    out["_removeCMMotion"] = bool(cs.get("removeCMMotion", False))
    return out


# --- Centralized create_system: tolerant to unused kwargs across FF routes ---
def create_system(
    obj, *, topology=None, paramset=None, kwargs: Dict[str, Any] | None = None
):
    """
    Call the appropriate createSystem(...) for the given object and kwargs,
    removing any kwargs that OpenMM reports as 'was never used.' Retries until
    success or a different error surfaces.

    Supported 'obj' types:
      - ForceField (requires 'topology')
      - AmberPrmtopFile
      - GromacsTopFile
      - CharmmPsfFile (requires 'paramset')
    """
    import re

    from openmm.app import (AmberPrmtopFile, CharmmPsfFile, ForceField,
                            GromacsTopFile)

    if kwargs is None:
        kwargs = {}

    # Strip private/internal keys (we use those after creation, e.g., CMMotionRemover)
    public = {k: v for k, v in kwargs.items() if not k.startswith("_")}

    while True:
        try:
            if isinstance(obj, ForceField):
                if topology is None:
                    raise ValueError("create_system(): ForceField requires 'topology'.")
                return obj.createSystem(topology, **public)

            if isinstance(obj, AmberPrmtopFile):
                return obj.createSystem(**public)

            if isinstance(obj, GromacsTopFile):
                return obj.createSystem(**public)

            if isinstance(obj, CharmmPsfFile):
                if paramset is None:
                    raise ValueError(
                        "create_system(): CharmmPsfFile requires 'paramset'."
                    )
                return obj.createSystem(paramset, **public)

            raise TypeError(
                f"Unsupported object type for create_system(): {type(obj).__name__}"
            )

        except ValueError as e:
            # OpenMM's ArgTracker message for unused kwargs
            m = re.search(
                r"The argument '([^']+)' was specified to createSystem\(\) but was never used\.",
                str(e),
            )
            if not m:
                # A different error: bubble up
                raise
            bad = m.group(1)
            if bad in public:
                logger.warning(
                    f"createSystem(): '{bad}' not used by this force field; dropping and retrying."
                )
                public.pop(bad, None)
                continue
            # Defensive: if OpenMM complained about a key we didn't actually pass
            raise


# ---- NEW: platform properties on Simulation(...) ----
def _new_simulation(
    topology,
    system,
    integrator,
    platform_name: str,
    platform_props: Dict[str, str] | None,
):
    from openmm.app import Simulation

    platform = _select_platform(platform_name)
    props = {str(k): str(v) for k, v in (platform_props or {}).items()}
    sim = Simulation(topology, system, integrator, platform, props if props else None)

    # Log effective platform and common properties
    plat = sim.context.getPlatform()
    defaults = []
    for k in (
        "CudaDeviceIndex",
        "CudaPrecision",
        "OpenCLDeviceIndex",
        "OpenCLPlatformIndex",
    ):
        try:
            v = plat.getPropertyDefaultValue(k)
            if v not in (None, ""):
                defaults.append(f"{k}={v}")
        except Exception:
            pass
    # If user passed overrides, show them too
    if props:
        for k, v in props.items():
            defaults.append(f"{k}={v}")
    logger.info(
        "Platform: "
        + plat.getName()
        + (f" ({', '.join(defaults)})" if defaults else "")
    )
    return sim


def _save_topology_snapshot(sim, path: Path):
    from openmm.app import PDBFile as _PDBFile

    with open(path, "w") as f:
        _PDBFile.writeFile(
            sim.topology,
            sim.context.getState(getPositions=True).getPositions(),
            f,
            keepIds=True,
        )


def _make_integrator(defaults: Dict[str, Any]):
    """
    Build an OpenMM integrator from defaults.integrator.

    Supported names (case-insensitive):
      - 'langevin'           (LangevinIntegrator)
      - 'langevin_middle'    (LangevinMiddleIntegrator, BAOAB)
      - 'brownian'           (BrownianIntegrator)
      - 'verlet'             (VerletIntegrator)
      - 'variable_langevin'  (VariableLangevinIntegrator)
      - 'variable_verlet'    (VariableVerletIntegrator)

    You may supply either a string or a dict, e.g.:
      integrator: "langevin_middle"
      # or
      integrator:
        name: langevin_middle
        timestep_fs: 4.0
        friction_ps: 1.0
        temperature_K: 300
        error_tolerance: 0.001   # only used by variable_* integrators
    """
    from openmm import LangevinMiddleIntegrator  # NEW
    from openmm import (BrownianIntegrator, LangevinIntegrator,
                        VariableLangevinIntegrator, VariableVerletIntegrator,
                        VerletIntegrator, unit)

    integ_spec = defaults.get("integrator", "langevin")
    if isinstance(integ_spec, str):
        name = integ_spec.strip().lower()
        spec = {}
    else:
        spec = dict(integ_spec or {})
        name = str(spec.get("name", "langevin")).strip().lower()

    # Pull knobs; fall back to top-level defaults.* if not provided in integrator block
    temperature_K = float(
        spec.get("temperature_K", defaults.get("temperature_K", 300.0))
    )
    timestep_fs = float(spec.get("timestep_fs", defaults.get("timestep_fs", 2.0)))
    friction_ps = float(spec.get("friction_ps", defaults.get("friction_ps", 1.0)))
    errtol = float(spec.get("error_tolerance", spec.get("errorTol", 0.001)))

    if name == "langevin":
        return LangevinIntegrator(
            temperature_K * unit.kelvin,
            friction_ps / unit.picoseconds,
            timestep_fs * unit.femtoseconds,
        )
    elif name == "langevin_middle":  # NEW
        return LangevinMiddleIntegrator(
            temperature_K * unit.kelvin,
            friction_ps / unit.picoseconds,
            timestep_fs * unit.femtoseconds,
        )
    elif name == "brownian":
        return BrownianIntegrator(
            temperature_K * unit.kelvin,
            friction_ps / unit.picoseconds,
            timestep_fs * unit.femtoseconds,
        )
    elif name == "verlet":
        return VerletIntegrator(timestep_fs * unit.femtoseconds)
    elif name == "variable_langevin":
        return VariableLangevinIntegrator(
            temperature_K * unit.kelvin, friction_ps / unit.picoseconds, errtol
        )
    elif name == "variable_verlet":
        return VariableVerletIntegrator(errtol)

    raise ValueError(
        f"Unsupported integrator '{name}'. Use: "
        "langevin, langevin_middle, brownian, verlet, variable_langevin, variable_verlet."
    )


# ------------------------------------------------------------
# PDB route (solvate, ions, FF)
# ------------------------------------------------------------
def _build_simulation(pdb_path: Path, defaults: Dict[str, Any], run_dir: Path):
    from openmm import unit
    from openmm.app import Modeller, PDBFile

    ff_files = defaults.get("forcefield", ["charmm36.xml", "charmm36/water.xml"])
    platform_name = defaults.get("platform", "auto")
    platform_props = defaults.get("platform_properties", {})
    padding_nm = float(defaults.get("box_padding_nm", 1.0))
    ionic_strength = float(defaults.get("ionic_strength_molar", 0.15))
    neutralize = bool(defaults.get("neutralize", True))
    positiveIon, negativeIon = _parse_ions(defaults)

    pdb = PDBFile(str(pdb_path))
    modeller = Modeller(pdb.topology, pdb.positions)
    logger.info(
        f"Solvate: TIP3P  pad={padding_nm} nm  ionic={ionic_strength} M  "
        f"neutralize={neutralize}  ions=({positiveIon},{negativeIon})"
    )
    ff = _load_forcefield(ff_files)
    modeller.addSolvent(
        ff,
        model="tip3p",
        padding=padding_nm * unit.nanometer,
        ionicStrength=ionic_strength * unit.molar,
        positiveIon=positiveIon,
        negativeIon=negativeIon,
        neutralize=neutralize,
    )

    cs_kwargs = _create_system_kwargs(defaults)
    # fallback constraints if user didn't override in create_system
    if "constraints" not in cs_kwargs:
        cs_kwargs["constraints"] = _constraints_from_str(
            defaults.get("constraints", "HBonds")
        )

    system = create_system(ff, topology=modeller.topology, kwargs=cs_kwargs)
    # optional CMMotionRemover
    if cs_kwargs.get("_removeCMMotion"):
        from openmm import CMMotionRemover

        system.addForce(CMMotionRemover())

    integrator = _make_integrator(defaults)
    sim = _new_simulation(
        modeller.topology, system, integrator, platform_name, platform_props
    )
    sim.context.setPositions(modeller.positions)

    _save_topology_snapshot(sim, run_dir / "topology.pdb")
    return sim


# ------------------------------------------------------------
# AMBER / GROMACS / CHARMM routes (parameterized)
# ------------------------------------------------------------
def _build_from_amber(spec: Dict[str, Any], defaults: Dict[str, Any], run_dir: Path):
    from openmm.app import AmberInpcrdFile, AmberPrmtopFile

    prmtop = AmberPrmtopFile(str(spec["prmtop"]))
    crd_key = "inpcrd" if "inpcrd" in spec else "rst7"
    inpcrd = AmberInpcrdFile(str(spec[crd_key]))

    cs_kwargs = _create_system_kwargs(defaults)
    if "constraints" not in cs_kwargs:
        cs_kwargs["constraints"] = _constraints_from_str(
            defaults.get("constraints", "HBonds")
        )

    system = create_system(prmtop, kwargs=cs_kwargs)
    if cs_kwargs.get("_removeCMMotion"):
        from openmm import CMMotionRemover

        system.addForce(CMMotionRemover())

    integrator = _make_integrator(defaults)
    sim = _new_simulation(
        prmtop.topology,
        system,
        integrator,
        defaults.get("platform", "auto"),
        defaults.get("platform_properties"),
    )
    sim.context.setPositions(inpcrd.positions)
    try:
        if inpcrd.boxVectors is not None:
            a, b, c = inpcrd.boxVectors
            sim.context.setPeriodicBoxVectors(a, b, c)
    except Exception:
        pass

    _save_topology_snapshot(sim, run_dir / "topology.pdb")
    return sim


def _build_from_gromacs(spec: Dict[str, Any], defaults: Dict[str, Any], run_dir: Path):
    from openmm.app import GromacsGroFile, GromacsTopFile

    if "gro" not in spec:
        raise ValueError("GROMACS spec requires 'gro'.")
    gro = GromacsGroFile(str(spec["gro"]))

    include_dirs = set()
    for d in spec.get("include_dirs") or []:
        include_dirs.add(str(Path(d)))
    for itp in spec.get("itp") or []:
        include_dirs.add(str(Path(itp).parent))

    top = GromacsTopFile(
        str(spec["top"]),
        periodicBoxVectors=gro.getPeriodicBoxVectors(),
        includeDirs=sorted(include_dirs) or None,
    )

    cs_kwargs = _create_system_kwargs(defaults)
    if "constraints" not in cs_kwargs:
        cs_kwargs["constraints"] = _constraints_from_str(
            defaults.get("constraints", "HBonds")
        )

    system = create_system(top, kwargs=cs_kwargs)
    if cs_kwargs.get("_removeCMMotion"):
        from openmm import CMMotionRemover

        system.addForce(CMMotionRemover())

    integrator = _make_integrator(defaults)
    sim = _new_simulation(
        top.topology,
        system,
        integrator,
        defaults.get("platform", "auto"),
        defaults.get("platform_properties"),
    )
    sim.context.setPositions(gro.positions)
    try:
        a, b, c = gro.getPeriodicBoxVectors()
        sim.context.setPeriodicBoxVectors(a, b, c)
    except Exception:
        pass

    _save_topology_snapshot(sim, run_dir / "topology.pdb")
    return sim


def _build_from_charmm(spec: Dict[str, Any], defaults: Dict[str, Any], run_dir: Path):
    from openmm.app import (CharmmCrdFile, CharmmParameterSet, CharmmPsfFile,
                            PDBFile)

    psf = CharmmPsfFile(str(spec["psf"]))

    params: List[str] = []
    if "params" in spec:
        v = spec["params"]
        params.extend([str(x) for x in v] if isinstance(v, (list, tuple)) else [str(v)])
    for key in ("prm", "rtf", "str"):
        if key in spec:
            v = spec[key]
            params.extend(
                [str(x) for x in v] if isinstance(v, (list, tuple)) else [str(v)]
            )
    if not params:
        raise ValueError(
            "CHARMM spec requires parameter files via 'params' or 'prm/rtf/str'."
        )

    paramset = CharmmParameterSet(*params)

    if "crd" in spec:
        positions = CharmmCrdFile(str(spec["crd"])).positions
    elif "pdb" in spec:
        positions = PDBFile(str(spec["pdb"])).positions
    else:
        raise ValueError("CHARMM spec requires coordinates via 'crd' or 'pdb'.")

    cs_kwargs = _create_system_kwargs(defaults)
    if "constraints" not in cs_kwargs:
        cs_kwargs["constraints"] = _constraints_from_str(
            defaults.get("constraints", "HBonds")
        )

    system = create_system(psf, paramset=paramset, kwargs=cs_kwargs)
    if cs_kwargs.get("_removeCMMotion"):
        from openmm import CMMotionRemover

        system.addForce(CMMotionRemover())

    integrator = _make_integrator(defaults)
    sim = _new_simulation(
        psf.topology,
        system,
        integrator,
        defaults.get("platform", "auto"),
        defaults.get("platform_properties"),
    )
    sim.context.setPositions(positions)

    _save_topology_snapshot(sim, run_dir / "topology.pdb")
    return sim


# ------------------------------------------------------------
# Public dispatcher
# ------------------------------------------------------------
def build_simulation_from_spec(
    spec: Dict[str, Any], defaults: Dict[str, Any], run_dir: Path
):
    stype = (spec.get("type") or "").lower()
    if not stype:
        if "pdb" in spec:
            stype = "pdb"
        elif "prmtop" in spec and ("inpcrd" in spec or "rst7" in spec):
            stype = "amber"
        elif "top" in spec and "gro" in spec:
            stype = "gromacs"
        elif "psf" in spec:
            stype = "charmm"
        else:
            raise ValueError(f"Cannot infer simulation type from spec: {spec}")

    run_dir.mkdir(parents=True, exist_ok=True)

    if stype == "pdb":
        return _build_simulation(Path(spec["pdb"]), defaults, run_dir)
    if stype == "amber":
        return _build_from_amber(spec, defaults, run_dir)
    if stype == "gromacs":
        return _build_from_gromacs(spec, defaults, run_dir)
    if stype == "charmm":
        return _build_from_charmm(spec, defaults, run_dir)

    raise ValueError(f"Unknown system type '{stype}'. Spec: {spec}")


# ------------------------------------------------------------
# Stage runner
# ------------------------------------------------------------
def run_stage(sim, stage: Dict[str, Any], stage_dir: Path, defaults: Dict[str, Any]):
    from openmm import unit
    from openmm.app import (CheckpointReporter, DCDReporter, PDBFile,
                            StateDataReporter)

    name = stage.get("name", "stage")
    steps = int(stage.get("steps", 0))
    ensemble = (stage.get("ensemble") or "NVT").upper()
    temperature_K = float(defaults.get("temperature_K", 300))
    pressure_atm = float(defaults.get("pressure_atm", 1.0))
    report_interval = int(
        stage.get("report_interval", defaults.get("report_interval", 1000))
    )
    checkpoint_interval = int(
        stage.get("checkpoint_interval", defaults.get("checkpoint_interval", 10000))
    )

    logger.info(f"Stage: {name} steps={steps} ensemble={ensemble}")

    stage_dir.mkdir(parents=True, exist_ok=True)

    sim.reporters = []
    if name.lower() != "minimize":
        sim.reporters.append(DCDReporter(str(stage_dir / "traj.dcd"), report_interval))
    sim.reporters.append(
        StateDataReporter(
            str(stage_dir / "state.log"),
            report_interval,
            step=True,
            speed=True,
            potentialEnergy=True,
            kineticEnergy=True,
            temperature=True,
            density=True,
            progress=True,
            remainingTime=True,
            totalSteps=steps,
        )
    )
    sim.reporters.append(
        CheckpointReporter(str(stage_dir / "state.chk"), checkpoint_interval)
    )

    # reset/add barostat as needed
    for idx in reversed(range(sim.system.getNumForces())):
        if sim.system.getForce(idx).__class__.__name__ == "MonteCarloBarostat":
            sim.system.removeForce(idx)
    _maybe_barostat(sim.system, ensemble, temperature_K, pressure_atm)

    if name.lower() == "minimize":
        tol_q, tol_val = _get_minimize_tolerance(defaults)
        maxit = int(defaults.get("minimize_max_iterations", 0))
        logger.info(f"Minimize: tol={tol_val} kJ/mol/nm  maxit={maxit}")
        sim.minimizeEnergy(tolerance=tol_q, maxIterations=maxit)

    if steps > 0:
        sim.step(steps)

    (stage_dir / "stage.json").write_text(json.dumps(stage, indent=2))
    with open(stage_dir / "topology.pdb", "w") as f:
        PDBFile.writeFile(
            sim.topology,
            sim.context.getState(getPositions=True).getPositions(),
            f,
            keepIds=True,
        )
