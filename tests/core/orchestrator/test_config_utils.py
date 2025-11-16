# tests/core/orchestrator/test_config_utils.py

import tempfile

# from pathlib import Path
from unittest.mock import patch

# import pytest
import yaml

from fastmdsimulation.core.orchestrator import (
    _steps_to_ps,
    resolve_plan,
    write_example_config,
)


class TestExampleConfig:
    """Test example config writing."""

    def test_write_example_config(self, tmp_path):
        config_path = tmp_path / "example_config.yml"

        write_example_config(str(config_path))

        # Verify file was created
        assert config_path.exists()

        # Verify it's valid YAML
        with open(config_path) as f:
            config = yaml.safe_load(f)

        # Check basic structure
        assert "project" in config
        assert "defaults" in config
        assert "stages" in config
        assert "systems" in config
        assert "sweep" in config

        assert config["project"] == "example-project"
        assert len(config["stages"]) == 4


class TestStepsConversion:
    """Test steps to picoseconds conversion."""

    def test_steps_to_ps(self):
        result = _steps_to_ps(1000, 2.0)  # 1000 steps × 2 fs/step
        assert result == 2.0  # 2000 fs = 2 ps

    def test_steps_to_ps_zero_steps(self):
        result = _steps_to_ps(0, 2.0)
        assert result == 0.0

    def test_steps_to_ps_large_timestep(self):
        result = _steps_to_ps(500, 4.0)  # 500 steps × 4 fs/step
        assert result == 2.0  # 2000 fs = 2 ps


class TestResolvePlan:
    """Test plan resolution functionality."""

    @patch("fastmdsimulation.core.orchestrator._expand_runs")
    def test_resolve_plan(self, mock_expand_runs):
        # Mock the YAML config
        mock_config = {
            "project": "test_project",
            "defaults": {"timestep_fs": 2.0},
            "systems": [{"id": "sys1"}],
            "stages": [{"name": "minimize", "steps": 1000}],
        }

        # Mock the expanded runs
        mock_expand_runs.return_value = {
            "project": "test_project",
            "output_dir": "/tmp/output/test_project",
            "runs": [
                {
                    "system_id": "sys1",
                    "temperature_K": 300,
                    "run_dir": "/tmp/output/test_project/sys1_T300",
                    "stages": [{"name": "minimize", "steps": 1000}],
                    "input": {"id": "sys1"},
                }
            ],
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yml") as f:
            yaml.dump(mock_config, f)
            f.flush()

            result = resolve_plan(f.name, "/tmp/output")

        # Verify plan structure
        assert result["project"] == "test_project"
        assert len(result["runs"]) == 1

        # Verify stages were enriched with approx_ps
        stage = result["runs"][0]["stages"][0]
        assert "approx_ps" in stage
        assert stage["approx_ps"] == 2.0  # 1000 steps × 2 fs/step = 2000 fs = 2 ps
