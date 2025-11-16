import os
import tempfile
from unittest.mock import patch

import pytest

from fastmdsimulation.cli import main


class TestCLIMain:
    @patch("fastmdsimulation.cli.setup_console")
    @patch("importlib.metadata.version")
    def test_main_version(self, mock_version, mock_setup_console):
        mock_version.return_value = "1.0.0"

        with patch("sys.argv", ["fastmds", "--version"]):
            with pytest.raises(SystemExit):
                main()

        mock_setup_console.assert_not_called()

    @patch("fastmdsimulation.cli.setup_console")
    @patch("importlib.metadata.version")
    def test_main_version_exception(self, mock_version, mock_setup_console):
        mock_version.side_effect = Exception("Version not found")

        with patch("sys.argv", ["fastmds", "--version"]):
            with pytest.raises(SystemExit):
                main()

    def test_main_no_args(self):
        with patch("sys.argv", ["fastmds"]), pytest.raises(SystemExit):
            main()

    def test_main_simulate_no_system(self):
        with patch("sys.argv", ["fastmds", "simulate"]), pytest.raises(SystemExit):
            main()

    @patch("fastmdsimulation.cli.setup_console")
    @patch("fastmdsimulation.cli.resolve_plan")
    def test_main_simulate_yaml_dry_run(self, mock_resolve_plan, mock_setup_console):
        mock_resolve_plan.return_value = {
            "project": "test_project",
            "output_dir": "/tmp/output",
            "runs": [
                {
                    "system_id": "system1",
                    "temperature_K": 300,
                    "run_dir": "/tmp/output/system1_300",
                    "stages": [
                        {"name": "minimization", "steps": 1000, "approx_ps": 2.0},
                        {"name": "production", "steps": 5000, "approx_ps": 10.0},
                    ],
                }
            ],
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("test yaml")
            yaml_path = f.name

        try:
            with patch(
                "sys.argv",
                [
                    "fastmds",
                    "simulate",
                    "--system",
                    yaml_path,
                    "--dry-run",
                    "--analyze",
                    "--frames",
                    "0,10,20",
                    "--atoms",
                    "protein",
                ],
            ):
                main()

            mock_setup_console.assert_called_once()
            mock_resolve_plan.assert_called_once_with(yaml_path, "simulate_output")
        finally:
            os.unlink(yaml_path)

    @patch("fastmdsimulation.cli.setup_console")
    @patch("fastmdsimulation.cli.run_from_yaml")
    @patch("fastmdsimulation.cli.attach_file_logger")
    @patch("fastmdsimulation.cli.analyze_with_bridge")
    def test_main_simulate_yaml_with_analysis(
        self, mock_analyze, mock_attach_logger, mock_run_yaml, mock_setup_console
    ):
        mock_run_yaml.return_value = "/tmp/project"
        mock_analyze.return_value = True

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("test yaml")
            yaml_path = f.name

        try:
            with patch(
                "sys.argv", ["fastmds", "simulate", "--system", yaml_path, "--analyze"]
            ):
                main()

            mock_run_yaml.assert_called_once_with(yaml_path, "simulate_output")
            mock_attach_logger.assert_called_once()
            mock_analyze.assert_called_once_with(
                "/tmp/project", slides=True, frames=None, atoms=None
            )
        finally:
            os.unlink(yaml_path)

    @patch("fastmdsimulation.cli.setup_console")
    @patch("fastmdsimulation.cli.run_from_yaml")
    @patch("fastmdsimulation.cli.attach_file_logger")
    @patch("fastmdsimulation.cli.analyze_with_bridge")
    def test_main_simulate_yaml_analysis_failed(
        self, mock_analyze, mock_attach_logger, mock_run_yaml, mock_setup_console
    ):
        mock_run_yaml.return_value = "/tmp/project"
        mock_analyze.return_value = False

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("test yaml")
            yaml_path = f.name

        try:
            with patch(
                "sys.argv", ["fastmds", "simulate", "--system", yaml_path, "--analyze"]
            ):
                main()

            mock_analyze.assert_called_once()
        finally:
            os.unlink(yaml_path)

    @patch("fastmdsimulation.cli.setup_console")
    @patch("fastmdsimulation.cli._resolve_plan_from_pdb")
    def test_main_simulate_pdb_dry_run(self, mock_resolve_plan, mock_setup_console):
        mock_resolve_plan.return_value = {
            "project": "test_project",
            "output_dir": "/tmp/output",
            "runs": [
                {
                    "system_id": "auto",
                    "temperature_K": 300,
                    "run_dir": "/tmp/output/auto_300",
                    "stages": [
                        {"name": "minimization", "steps": 1000, "approx_ps": 2.0}
                    ],
                }
            ],
        }

        with patch(
            "sys.argv", ["fastmds", "simulate", "--system", "test.pdb", "--dry-run"]
        ):
            main()

        mock_resolve_plan.assert_called_once_with("test.pdb", "simulate_output", None)

    @patch("fastmdsimulation.cli.setup_console")
    @patch("fastmdsimulation.cli.simulate_from_pdb")
    @patch("fastmdsimulation.cli.attach_file_logger")
    @patch("fastmdsimulation.cli.analyze_with_bridge")
    def test_main_simulate_pdb_with_config_and_analysis(
        self, mock_analyze, mock_attach_logger, mock_simulate_pdb, mock_setup_console
    ):
        mock_simulate_pdb.return_value = "/tmp/project"
        mock_analyze.return_value = True

        with patch(
            "sys.argv",
            [
                "fastmds",
                "simulate",
                "--system",
                "test.pdb",
                "--config",
                "config.yaml",
                "--analyze",
                "--slides",
                "False",
                "--frames",
                "0,10",
                "--atoms",
                "backbone",
            ],
        ):
            main()

        mock_simulate_pdb.assert_called_once_with(
            "test.pdb", outdir="simulate_output", config="config.yaml"
        )
        mock_analyze.assert_called_once_with(
            "/tmp/project", slides=False, frames="0,10", atoms="backbone"
        )

    @patch("fastmdsimulation.cli.setup_console")
    def test_main_simulate_yaml_with_config_warning(self, mock_setup_console):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("test yaml")
            yaml_path = f.name

        try:
            with (
                patch(
                    "sys.argv",
                    [
                        "fastmds",
                        "simulate",
                        "--system",
                        yaml_path,
                        "--config",
                        "config.yaml",
                    ],
                ),
                patch("fastmdsimulation.cli.run_from_yaml") as mock_run,
            ):
                mock_run.return_value = "/tmp/project"
                with patch("fastmdsimulation.cli.attach_file_logger"):
                    main()

                mock_run.assert_called_once()
        finally:
            os.unlink(yaml_path)
