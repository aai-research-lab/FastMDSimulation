# tests/conftest.py

import json
import os
import pathlib as _pl
import sys
import textwrap

import pytest


def pytest_configure(config):
    """Register custom markers for test categorization."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with -m 'not slow')"
    )
    config.addinivalue_line(
        "markers", "requires_openmm: test requires OpenMM installation"
    )
    config.addinivalue_line("markers", "integration: end-to-end integration test")


@pytest.fixture(autouse=True)
def _force_reference_platform(monkeypatch):
    """
    Keep unit tests platform-agnostic and fast by using Reference platform.
    Preserves original environment for safety.
    """
    original = os.getenv("OPENMM_DEFAULT_PLATFORM")
    monkeypatch.setenv("OPENMM_DEFAULT_PLATFORM", "Reference")
    yield
    # Restore original environment after test
    if original is None:
        monkeypatch.delenv("OPENMM_DEFAULT_PLATFORM", raising=False)
    else:
        monkeypatch.setenv("OPENMM_DEFAULT_PLATFORM", original)


@pytest.fixture
def tmp_jobdir(tmp_path):
    """Create a temporary directory for job files."""
    d = tmp_path / "job"
    d.mkdir()
    return d


@pytest.fixture
def water2nm_pdb(tmp_jobdir):
    """
    Create a tiny TIP3P water PDB for smoke tests.
    Falls back to a minimal HOH if OpenMM is unavailable.
    """
    pdb = tmp_jobdir / "water2nm.pdb"
    try:
        from openmm import Vec3, unit
        from openmm.app import ForceField, Modeller, PDBFile, Topology

        # Create a small water box using OpenMM
        mod = Modeller(Topology(), [])
        ff = ForceField("tip3p.xml")
        mod.addSolvent(ff, model="tip3p", boxSize=Vec3(2, 2, 2) * unit.nanometers)

        with open(pdb, "w") as f:
            PDBFile.writeFile(mod.topology, mod.positions, f)

    except Exception:
        # Fallback: Minimal valid-looking PDB with a single water
        # Enough for path/plumbing tests when OpenMM isn't available
        pdb.write_text(
            textwrap.dedent(
                """\
CRYST1   20.000   20.000   20.000  90.00  90.00  90.00 P 1           1
HETATM    1  O   HOH A   1       0.000   0.000   0.000  1.00  0.00           O
HETATM    2  H1  HOH A   1       0.758   0.000   0.504  1.00  0.00           H
HETATM    3  H2  HOH A   1      -0.758   0.000   0.504  1.00  0.00           H
END
"""
            )
        )
    return pdb


@pytest.fixture
def waterbox_job_yaml(tmp_jobdir, water2nm_pdb):
    """Create a realistic waterbox job YAML for integration testing."""
    yml = tmp_jobdir / "job_water2nm.yml"
    yml.write_text(
        textwrap.dedent(
            f"""
project: WaterBox
defaults:
  engine: openmm
  platform: auto
  temperature_K: 300
  timestep_fs: 2.0
  minimize_tolerance_kjmol_per_nm: 10.0
  minimize_max_iterations: 0
  report_interval: 1000
  checkpoint_interval: 10000
  forcefield: ["charmm36.xml", "charmm36/water.xml"]
  ionic_strength_molar: 0.0
  neutralize: false
  box_padding_nm: 1.0
stages:
  - {{ name: minimize, steps: 0 }}
  - {{ name: production, steps: 0, ensemble: NPT }}
systems:
  - id: water2nm
    fixed_pdb: {water2nm_pdb.as_posix()}
sweep:
  temperature_K: [300]
"""
        )
    )
    return yml


@pytest.fixture
def minimal_job_yaml(tmp_jobdir, water2nm_pdb):
    """Create a minimal job YAML for basic functionality testing."""
    yml = tmp_jobdir / "minimal_job.yml"
    yml.write_text(
        textwrap.dedent(
            f"""
project: MinimalTest
defaults:
  temperature_K: 300
stages:
  - {{ name: minimize, steps: 0 }}
systems:
  - id: test_system
    fixed_pdb: {water2nm_pdb.as_posix()}
"""
        )
    )
    return yml


@pytest.fixture
def mock_openmm_platforms(monkeypatch):
    """Mock OpenMM platforms for testing platform detection logic."""

    class MockPlatform:
        def __init__(self, name):
            self.name = name

        def getName(self):
            return self.name

    def mock_get_num_platforms():
        return 3

    def mock_get_platform(index):
        platforms = ["Reference", "CPU", "CUDA"]
        return MockPlatform(platforms[index])

    # Mock the OpenMM platform methods
    monkeypatch.setattr("openmm.Platform.getNumPlatforms", mock_get_num_platforms)
    monkeypatch.setattr("openmm.Platform.getPlatform", mock_get_platform)


@pytest.fixture
def sample_pdb_file(tmp_jobdir):
    """Create a sample PDB file for one-shot simulation testing."""
    pdb = tmp_jobdir / "sample.pdb"
    pdb.write_text(
        textwrap.dedent(
            """\
ATOM      1  N   ALA A   1       0.000   0.000   0.000  1.00  0.00           N
ATOM      2  CA  ALA A   1       1.458   0.000   0.000  1.00  0.00           C
ATOM      3  C   ALA A   1       2.009   1.420   0.000  1.00  0.00           C
ATOM      4  O   ALA A   1       1.251   2.381   0.000  1.00  0.00           O
END
"""
        )
    )
    return pdb


# Skip tests if OpenMM is not available
def pytest_collection_modifyitems(config, items):
    """Skip tests marked 'requires_openmm' if OpenMM is not available."""
    try:
        import openmm

        openmm_available = True
    except ImportError:
        openmm_available = False

    skip_openmm = pytest.mark.skip(reason="OpenMM not available")

    for item in items:
        if "requires_openmm" in item.keywords and not openmm_available:
            item.add_marker(skip_openmm)
