import tempfile
from unittest.mock import mock_open, patch

from fastmdsimulation.cli import _resolve_plan_from_pdb


class TestResolvePlanFromPDB:
    @patch("fastmdsimulation.cli.build_auto_config")
    @patch("fastmdsimulation.cli.Path")
    def test_resolve_plan_from_pdb_basic(self, mock_path, mock_build_auto_config):
        mock_path.return_value.stem = "test"
        mock_path.return_value.with_name.return_value = "test_fixed.pdb"

        mock_build_auto_config.return_value = {
            "project": "test_project",
            "defaults": {"timestep_fs": 2.0, "temperature_K": 300},
            "stages": [
                {"name": "minimization", "steps": 1000},
                {"name": "equilibration", "steps": 5000},
                {"name": "production", "steps": 10000},
            ],
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            result = _resolve_plan_from_pdb("test.pdb", tmpdir, None)

            assert result["project"] == "test_project"
            assert len(result["runs"]) == 1
            run = result["runs"][0]
            assert run["system_id"] == "auto"
            assert run["temperature_K"] == 300
            assert len(run["stages"]) == 3

    @patch("fastmdsimulation.cli.build_auto_config")
    @patch("fastmdsimulation.cli.Path")
    @patch("fastmdsimulation.cli.yaml.safe_load")
    def test_resolve_plan_from_pdb_with_config(
        self, mock_yaml_load, mock_path, mock_build_auto_config
    ):
        mock_path.return_value.stem = "test"
        mock_path.return_value.with_name.return_value = "test_fixed.pdb"

        mock_build_auto_config.return_value = {
            "project": "test_project",
            "defaults": {"timestep_fs": 2.0, "temperature_K": 300},
            "stages": [
                {"name": "minimization", "steps": 1000},
                {"name": "production", "steps": 10000},
            ],
        }

        mock_yaml_load.return_value = {
            "defaults": {"temperature_K": 310},
            "stages": [{"name": "production", "steps": 20000}],
        }

        # Mock the file opening
        with patch("builtins.open", mock_open()) as mock_file:
            with tempfile.TemporaryDirectory() as tmpdir:
                result = _resolve_plan_from_pdb("test.pdb", tmpdir, "config.yaml")

                # Verify the config file was attempted to be opened
                mock_file.assert_called_once_with("config.yaml")
                # Verify the yaml.safe_load was called with the mock file
                mock_yaml_load.assert_called_once()

                assert result["runs"][0]["temperature_K"] == 310

    @patch("fastmdsimulation.cli.build_auto_config")
    @patch("fastmdsimulation.cli.Path")
    def test_resolve_plan_from_pdb_calculates_approx_ps(
        self, mock_path, mock_build_auto_config
    ):
        mock_path.return_value.stem = "test"
        mock_path.return_value.with_name.return_value = "test_fixed.pdb"

        mock_build_auto_config.return_value = {
            "project": "test_project",
            "defaults": {"timestep_fs": 2.0, "temperature_K": 300},
            "stages": [
                {"name": "minimization", "steps": 1000},
                {"name": "production", "steps": 5000},
            ],
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            result = _resolve_plan_from_pdb("test.pdb", tmpdir, None)

            stages = result["runs"][0]["stages"]
            assert stages[0]["approx_ps"] == 2.0  # 1000 * 2.0 / 1000
            assert stages[1]["approx_ps"] == 10.0  # 5000 * 2.0 / 1000

    @patch("fastmdsimulation.cli.build_auto_config")
    @patch("fastmdsimulation.cli.Path")
    def test_resolve_plan_from_pdb_no_config(self, mock_path, mock_build_auto_config):
        mock_path.return_value.stem = "test"
        mock_path.return_value.with_name.return_value = "test_fixed.pdb"

        mock_build_auto_config.return_value = {
            "project": "test_project",
            "defaults": {"timestep_fs": 2.0, "temperature_K": 300},
            "stages": [{"name": "minimization", "steps": 1000}],
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            result = _resolve_plan_from_pdb("test.pdb", tmpdir, None)

            # Should use default temperature from auto_config
            assert result["runs"][0]["temperature_K"] == 300
