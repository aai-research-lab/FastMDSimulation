# FastMDSimulation/src/fastmdsimulation/cli.py

import argparse
import os
from pathlib import Path

import yaml

from .core.orchestrator import resolve_plan, run_from_yaml
from .core.simulate import build_auto_config, simulate_from_pdb
from .reporting.analysis_bridge import analyze_with_bridge, build_analyze_cmd
from .utils.logging import attach_file_logger, setup_console


# ---------------------------
# Helpers for config merging and log-style detection
# ---------------------------
def _deep_update(dst: dict, src: dict) -> dict:
    """Deep-merge src into dst (used for dry-run with PDB + overrides)."""
    for k, v in (src or {}).items():
        if isinstance(v, dict) and isinstance(dst.get(k), dict):
            _deep_update(dst[k], v)
        else:
            dst[k] = v
    return dst


def _normalize_style(val: str | None) -> str | None:
    if not val:
        return None
    v = str(val).strip().lower()
    return v if v in ("pretty", "plain") else None


def _read_log_style_from_yaml(yaml_path: str | Path) -> str | None:
    try:
        data = yaml.safe_load(open(yaml_path)) or {}
        sty = (
            ((data.get("defaults") or {}).get("log_style"))
            if isinstance(data, dict)
            else None
        )
        return _normalize_style(sty)
    except Exception:
        return None


def _env_log_style() -> str | None:
    return _normalize_style(os.getenv("FASTMDS_LOG_STYLE"))


def _detect_log_style(system_path: str, config_path: str | None) -> str:
    """
    Precedence (no CLI flag yet):
      1) YAML job's defaults.log_style (if system is a YAML),
      2) overrides YAML's defaults.log_style (if provided for PDB flow),
      3) env FASTMDS_LOG_STYLE,
      4) fallback 'pretty' for console.
    """
    style = None
    if system_path.lower().endswith((".yml", ".yaml")):
        style = _read_log_style_from_yaml(system_path)
    elif config_path:
        style = _read_log_style_from_yaml(config_path)
    if style is None:
        style = _env_log_style()
    return style or "pretty"


def _resolve_plan_from_pdb(pdb: str, outdir: str, config: str | None):
    """
    Build a synthetic plan for dry-run when the user provides a PDB.
    This doesn't actually run PDBFixer; it's just to print the plan.
    """
    fixed_pdb_placeholder = Path(pdb).with_name(Path(pdb).stem + "_fixed.pdb")
    auto_cfg = build_auto_config(fixed_pdb_placeholder)
    if config:
        over = yaml.safe_load(open(config)) or {}
        auto_cfg = _deep_update(auto_cfg, over)

    # No redundant forcefield under systems; inherits from defaults
    yml_like = {
        "project": auto_cfg["project"],
        "defaults": auto_cfg["defaults"],
        "stages": auto_cfg["stages"],
        "systems": [
            {
                "id": "auto",
                "pdb": str(fixed_pdb_placeholder),
            }
        ],
    }
    tmp = Path(outdir) / auto_cfg["project"]
    tfs = float(yml_like["defaults"].get("timestep_fs", 2.0))
    runs = [
        {
            "system_id": "auto",
            "temperature_K": yml_like["defaults"].get("temperature_K", 300),
            "run_dir": str(
                tmp / f'auto_T{yml_like["defaults"].get("temperature_K", 300)}'
            ),
            "stages": [
                {
                    "name": st["name"],
                    "steps": int(st.get("steps", 0)),
                    "approx_ps": round(int(st.get("steps", 0)) * tfs / 1000.0, 3),
                }
                for st in yml_like["stages"]
            ],
        }
    ]
    return {"project": auto_cfg["project"], "output_dir": str(tmp), "runs": runs}


# ---------------------------
# CLI
# ---------------------------
def main():
    parser = argparse.ArgumentParser(
        prog="fastmds",
        description="Automated MD simulation (OpenMM-first). Supports both Systemic Simulations (multiple systems via YAML) and One-Shot Simulations (single PDB with overrides).",
    )
    parser.add_argument(
        "-v", "--version", action="store_true", help="Print version and exit"
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    # Single entrypoint: simulate
    p_sim = sub.add_parser(
        "simulate",
        help="Run Systemic Simulation (-system job.yml) or One-Shot Simulation (-system protein.pdb).",
    )
    # Accept --system (preferred), -s (short), and -system (single-dash long) to match examples.
    p_sim.add_argument(
        "-s",
        "--system",
        "-system",
        required=True,
        help="Path to input: YAML file for Systemic Simulation or PDB file for One-Shot Simulation",
    )
    p_sim.add_argument(
        "-o",
        "--output",
        default="simulate_output",
        type=str,
        help="Output base directory (default: simulate_output)",
    )
    p_sim.add_argument(
        "--config",
        default=None,
        help="Configuration overrides YAML (One-Shot Simulations only; ignored for Systemic Simulations)",
    )
    p_sim.add_argument(
        "--analyze",
        action="store_true",
        help="Run analysis after simulation (FastMDAnalysis)",
    )
    p_sim.add_argument(
        "--frames",
        type=str,
        default=None,
        help='Frames selection, e.g., "0,-1,10" or "200"',
    )
    p_sim.add_argument(
        "--atoms", type=str, default=None, help='Atom selection (e.g., "protein")'
    )
    p_sim.add_argument(
        "--slides",
        choices=["True", "False"],
        default="True",
        help="Include slides (default True)",
    )
    p_sim.add_argument(
        "--dry-run",
        action="store_true",
        help="Print resolved plan (stages, durations, output dirs) and exit. "
        "If --analyze is set, also print the exact fastmda analyze command(s).",
    )

    args = parser.parse_args()

    # Determine console log style (YAML or overrides or env; default pretty)
    style = _detect_log_style(args.system, args.config)
    setup_console(style=style)

    if args.version:
        try:
            from importlib.metadata import version

            print(version("fastmdsimulation"))
        except Exception:
            print("fastmdsimulation")
        return

    if args.cmd == "simulate":
        system = args.system

        # Systemic Simulation path (YAML-driven)
        if system.lower().endswith((".yml", ".yaml")):
            if args.config:
                print(
                    "Warning: --config is ignored for Systemic Simulations (YAML files)."
                )
            if args.dry_run:
                plan = resolve_plan(system, args.output)
                print("=== DRY RUN (SYSTEMIC SIMULATION) ===")
                print(f'Project: {plan["project"]}')
                print(f'Output:  {plan["output_dir"]}')
                print(
                    f'Analysis: {"Yes" if args.analyze else "No"}'
                    + (
                        f" (slides={args.slides}, frames={args.frames}, atoms={args.atoms})"
                        if args.analyze
                        else ""
                    )
                )
                for r in plan["runs"]:
                    print(
                        f'- Run: {r["system_id"]} @ {r["temperature_K"]} K -> {r["run_dir"]}'
                    )
                    for s in r["stages"]:
                        print(
                            f'    · {s["name"]}: {s["steps"]} steps (~{s["approx_ps"]} ps)'
                        )
                    if args.analyze:
                        prod = Path(r["run_dir"]) / "production"
                        cmd = build_analyze_cmd(
                            prod / "traj.dcd",
                            prod / "topology.pdb",
                            slides=(args.slides == "True"),
                            frames=args.frames,
                            atoms=args.atoms,
                        )
                        print("    → fastmda command:", " ".join(map(str, cmd)))
                return
            project_dir = run_from_yaml(system, args.output)

        # One-Shot Simulation path (PDB-driven)
        else:
            if args.dry_run:
                plan = _resolve_plan_from_pdb(system, args.output, args.config)
                print("=== DRY RUN (ONE-SHOT SIMULATION) ===")
                print(f'Project: {plan["project"]}')
                print(f'Output:  {plan["output_dir"]}')
                print(
                    f'Analysis: {"Yes" if args.analyze else "No"}'
                    + (
                        f" (slides={args.slides}, frames={args.frames}, atoms={args.atoms})"
                        if args.analyze
                        else ""
                    )
                )
                for r in plan["runs"]:
                    print(
                        f'- Run: {r["system_id"]} @ {r["temperature_K"]} K -> {r["run_dir"]}'
                    )
                    for s in r["stages"]:
                        print(
                            f'    · {s["name"]}: {s["steps"]} steps (~{s["approx_ps"]} ps)'
                        )
                    if args.analyze:
                        prod = Path(r["run_dir"]) / "production"
                        cmd = build_analyze_cmd(
                            prod / "traj.dcd",
                            prod / "topology.pdb",
                            slides=(args.slides == "True"),
                            frames=args.frames,
                            atoms=args.atoms,
                        )
                        print("    → fastmda command:", " ".join(map(str, cmd)))
                return
            project_dir = simulate_from_pdb(
                system, outdir=args.output, config=args.config
            )

        # Attach file logger (plain ISO for audits) and optionally run analysis
        attach_file_logger(str(Path(project_dir) / "fastmds.log"), style="plain")
        if args.analyze:
            ok = analyze_with_bridge(
                project_dir,
                slides=(args.slides == "True"),
                frames=args.frames,
                atoms=args.atoms,
            )
            if not ok:
                print(
                    "Analysis skipped or failed; install FastMDAnalysis or adjust flags."
                )
