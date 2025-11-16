# tests/core/orchestrator/test_run_expansion.py

# import pytest

from fastmdsimulation.core.orchestrator import _expand_runs


class TestRunExpansion:
    """Test run expansion logic."""

    def test_expand_runs_basic(self):
        cfg = {
            "project": "test_project",
            "defaults": {"temperature_K": 300},
            "systems": [{"id": "sys1"}, {"id": "sys2"}],
            "sweep": {"temperature_K": [300, 310]},
            "stages": [{"name": "minimize", "steps": 100}],
        }

        result = _expand_runs(cfg, "/tmp/output")

        assert result["project"] == "test_project"
        assert result["output_dir"] == "/tmp/output/test_project"
        assert len(result["runs"]) == 4  # 2 systems × 2 temperatures

        # Check run structure
        run = result["runs"][0]
        assert run["system_id"] == "sys1"
        assert run["temperature_K"] == 300
        assert "run_dir" in run
        assert "stages" in run
        assert "input" in run

    def test_expand_runs_no_sweep(self):
        cfg = {
            "project": "test_project",
            "defaults": {"temperature_K": 300},
            "systems": [{"id": "sys1"}],
            "stages": [{"name": "minimize", "steps": 100}],
        }

        result = _expand_runs(cfg, "/tmp/output")

        assert len(result["runs"]) == 1
        assert result["runs"][0]["temperature_K"] == 300

    def test_expand_runs_with_forcefield_override(self):
        cfg = {
            "project": "test_project",
            "defaults": {"temperature_K": 300},
            "systems": [{"id": "sys1", "forcefield": ["custom.xml"]}],
            "stages": [{"name": "minimize", "steps": 100}],
        }

        result = _expand_runs(cfg, "/tmp/output")

        assert result["runs"][0]["forcefield"] == ["custom.xml"]
