---
title: FastMDSimulation Documentation
---

# FastMDSimulation

Automated, batteries-included molecular dynamics on OpenMM with a CLI for fast runs and a Python API for scripted workflows.

```{toctree}
:maxdepth: 1
:hidden:

quickstart
guide
readme
api/index
```

## Overview
- Describe a system once in YAML or drop in a PDB for rapid one-shot runs.
- One-command protein–ligand runs: supply a protein PDB plus ligand (SDF/MOL2) and we run ff14SB + TIP3P + OpenFF Sage 2.x via OpenMM.
- Choose your entrypoint: streamlined CLI for jobs, Python API for notebooks and pipelines.
- Bias and explore with optional PLUMED collective variables.
- Post-process trajectories with FastMDAnalysis (optional extra).

## What you get
- **Reproducible configs**: versionable YAML plans, templated job files for clusters.
- **Engineered defaults**: sensible integrators, thermostats, and reporting cadence out of the box.
- **Cluster-friendly**: PBS/SLURM submit helpers and expansion for sweep-style runs.
- **Safety rails**: schema validation, input checks, and clear error surfaces.

## Quick navigation
- Start here: [Quickstart](quickstart) for end-to-end CLI and API examples.
- Protein–ligand how-to: see the Quickstart “One-shot protein–ligand (OpenFF Sage 2.x)” section.
- Need references: [API docs](api/index) for modules and call signatures.
- Configure jobs: examples in `examples/job_full.yml` and `examples/config_quick.yml`.
- Explore engines: OpenMM engine details in `src/fastmdsimulation/engines/openmm_engine.py`.

## Quick start
- See the full walkthrough in [Quickstart](quickstart) (one-shot PDB, YAML, and protein–ligand OpenFF flows).
- Minimal protein–ligand template: `examples/protein_ligand.yml`.

## Simulation guide
- Deeper guidance lives in the [Simulation Guide](guide) (prep, staging, PLUMED, analysis).
