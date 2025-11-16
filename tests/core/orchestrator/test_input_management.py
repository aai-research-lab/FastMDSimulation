# tests/core/orchestrator/test_input_management.py

from pathlib import Path
from unittest.mock import patch

from fastmdsimulation.core.orchestrator import _populate_inputs


class TestInputPopulation:
    """Test input file population."""

    @patch("fastmdsimulation.core.orchestrator._copy_into")
    @patch("fastmdsimulation.core.orchestrator._maybe_copy_forcefields")
    @patch("fastmdsimulation.core.orchestrator._collect_system_paths")
    def test_populate_inputs(
        self, mock_collect_paths, mock_copy_forcefields, mock_copy, tmp_path
    ):
        mock_collect_paths.return_value = [Path("test.pdb")]

        cfg = {
            "systems": [
                {"id": "sys1", "type": "pdb", "pdb": "test.pdb"},
            ],
            "defaults": {"forcefield": ["ff1.xml"]},
        }
        # Use tmp_path instead of hardcoded paths
        cfg_path = tmp_path / "job.yml"
        cfg_path.touch()  # Create the config file
        base = tmp_path / "output"

        # This should work now with parents=True in the source code
        _populate_inputs(cfg, cfg_path, base)

        # Verify config was copied
        mock_copy.assert_any_call(base / "inputs", cfg_path)

        # Verify system files were copied
        mock_copy.assert_any_call(base / "inputs" / "sys1", Path("test.pdb"))

        # Verify forcefields were processed
        mock_copy_forcefields.assert_called_once_with(cfg["defaults"], base / "inputs")
