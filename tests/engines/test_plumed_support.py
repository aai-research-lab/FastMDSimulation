from pathlib import Path

from fastmdsimulation.engines.plumed_support import (
    _adjust_plumed_paths,
    merge_plumed_configs,
)


def test_merge_plumed_configs_stage_overrides_defaults():
    defaults = {
        "plumed": {"enabled": False, "script": "base.dat", "log_frequency": 250}
    }
    stage = {"plumed": {"enabled": True, "script": "stage.dat"}}

    merged = merge_plumed_configs(defaults, stage)

    assert merged["enabled"] is True
    assert merged["script"] == "stage.dat"
    assert merged["log_frequency"] == 250


def test_adjust_plumed_paths_rewrites_output_targets(tmp_path: Path):
    stage_dir = tmp_path / "stage"
    stage_dir.mkdir()

    script = """
METAD ... FILE=COLVAR
PRINT STRIDE=10 FILE=HILLS
"""
    adjusted = _adjust_plumed_paths(script, stage_dir)

    assert str(stage_dir / "COLVAR").replace("\\", "/") in adjusted
    assert str(stage_dir / "HILLS").replace("\\", "/") in adjusted
