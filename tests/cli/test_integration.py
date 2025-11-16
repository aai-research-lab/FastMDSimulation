import sys
from unittest.mock import patch

import pytest


class TestCLIIntegration:
    """Integration tests for CLI that should run quickly with proper mocking."""

    @patch("fastmdsimulation.cli.setup_console")
    @patch("fastmdsimulation.cli.run_from_yaml")
    @patch("fastmdsimulation.cli.attach_file_logger")
    def test_cli_simulate_invokes_orchestrator(
        self,
        mock_attach_logger,
        mock_run_yaml,
        mock_setup_console,
        monkeypatch,
        tmp_path,
        waterbox_job_yaml,
    ):
        """Ensure the CLI dispatches to orchestrator.run_from_yaml with the provided job file."""
        mock_run_yaml.return_value = str(tmp_path / "simulate_output" / "WaterBox")

        argv = ["fastmds", "simulate", "-system", str(waterbox_job_yaml)]
        monkeypatch.setattr(sys, "argv", argv)

        from fastmdsimulation.cli import main

        main()

        mock_run_yaml.assert_called_once_with(str(waterbox_job_yaml), "simulate_output")

    @patch("fastmdsimulation.cli.setup_console")
    @patch("fastmdsimulation.cli.run_from_yaml")
    @patch("fastmdsimulation.cli.attach_file_logger")
    def test_cli_simulate_with_output_dir(
        self,
        mock_attach_logger,
        mock_run_yaml,
        mock_setup_console,
        monkeypatch,
        tmp_path,
        waterbox_job_yaml,
    ):
        """Test custom output directory."""
        mock_run_yaml.return_value = str(tmp_path / "custom_output" / "WaterBox")

        custom_dir = tmp_path / "my_custom_output"
        argv = [
            "fastmds",
            "simulate",
            "-system",
            str(waterbox_job_yaml),
            "-o",
            str(custom_dir),
        ]
        monkeypatch.setattr(sys, "argv", argv)

        from fastmdsimulation.cli import main

        main()

        mock_run_yaml.assert_called_once_with(str(waterbox_job_yaml), str(custom_dir))

    @patch("fastmdsimulation.cli.setup_console")
    @patch("fastmdsimulation.cli.simulate_from_pdb")
    @patch("fastmdsimulation.cli.attach_file_logger")
    def test_cli_simulate_pdb_one_shot(
        self,
        mock_attach_logger,
        mock_simulate_pdb,
        mock_setup_console,
        monkeypatch,
        tmp_path,
        sample_pdb_file,
    ):
        """Test one-shot simulation from PDB file."""
        mock_simulate_pdb.return_value = str(tmp_path / "pdb_output" / "AutoProject")

        argv = ["fastmds", "simulate", "-system", str(sample_pdb_file)]
        monkeypatch.setattr(sys, "argv", argv)

        from fastmdsimulation.cli import main

        main()

        mock_simulate_pdb.assert_called_once_with(
            str(sample_pdb_file), outdir="simulate_output", config=None
        )

    @patch("fastmdsimulation.cli.setup_console")
    @patch("fastmdsimulation.cli.simulate_from_pdb")
    @patch("fastmdsimulation.cli.attach_file_logger")
    def test_cli_simulate_pdb_with_config(
        self,
        mock_attach_logger,
        mock_simulate_pdb,
        mock_setup_console,
        monkeypatch,
        tmp_path,
        sample_pdb_file,
        minimal_job_yaml,
    ):
        """Test one-shot simulation from PDB with config overrides."""
        mock_simulate_pdb.return_value = str(
            tmp_path / "configured_output" / "AutoProject"
        )

        argv = [
            "fastmds",
            "simulate",
            "-system",
            str(sample_pdb_file),
            "--config",
            str(minimal_job_yaml),
        ]
        monkeypatch.setattr(sys, "argv", argv)

        from fastmdsimulation.cli import main

        main()

        mock_simulate_pdb.assert_called_once_with(
            str(sample_pdb_file), outdir="simulate_output", config=str(minimal_job_yaml)
        )

    @patch("fastmdsimulation.cli.setup_console")
    @patch("fastmdsimulation.cli.run_from_yaml")
    @patch("fastmdsimulation.cli.attach_file_logger")
    @patch("fastmdsimulation.cli.analyze_with_bridge")
    def test_cli_simulate_with_analysis_flags(
        self,
        mock_analyze,
        mock_attach_logger,
        mock_run_yaml,
        mock_setup_console,
        monkeypatch,
        tmp_path,
        waterbox_job_yaml,
    ):
        """Test simulation with analysis flags."""
        mock_run_yaml.return_value = str(tmp_path / "analysis_test" / "WaterBox")
        mock_analyze.return_value = True

        argv = [
            "fastmds",
            "simulate",
            "-system",
            str(waterbox_job_yaml),
            "--analyze",
            "--atoms",
            "protein",
            "--frames",
            "100",
            "--slides",
            "False",
        ]
        monkeypatch.setattr(sys, "argv", argv)

        from fastmdsimulation.cli import main

        main()

        mock_run_yaml.assert_called_once_with(str(waterbox_job_yaml), "simulate_output")
        mock_analyze.assert_called_once_with(
            str(tmp_path / "analysis_test" / "WaterBox"),
            slides=False,
            frames="100",
            atoms="protein",
        )

    @patch("fastmdsimulation.cli.setup_console")
    @patch("fastmdsimulation.cli.resolve_plan")
    def test_cli_simulate_dry_run(
        self,
        mock_resolve_plan,
        mock_setup_console,
        monkeypatch,
        tmp_path,
        waterbox_job_yaml,
    ):
        """Test dry-run mode."""
        mock_resolve_plan.return_value = {
            "project": "WaterBox",
            "output_dir": str(tmp_path / "dry_run_output"),
            "runs": [
                {
                    "system_id": "water2nm",
                    "temperature_K": 300,
                    "run_dir": str(tmp_path / "dry_run_output" / "WaterBox_T300"),
                    "stages": [{"name": "minimize", "steps": 0, "approx_ps": 0.0}],
                }
            ],
        }

        argv = ["fastmds", "simulate", "-system", str(waterbox_job_yaml), "--dry-run"]
        monkeypatch.setattr(sys, "argv", argv)

        from fastmdsimulation.cli import main

        main()

        mock_resolve_plan.assert_called_once_with(
            str(waterbox_job_yaml), "simulate_output"
        )

    @patch("fastmdsimulation.cli.setup_console")
    def test_cli_version(self, mock_setup_console, monkeypatch, capsys):
        """Test version command output."""
        monkeypatch.setattr(sys, "argv", ["fastmds", "--version"])

        from fastmdsimulation.cli import main

        with pytest.raises(SystemExit):
            main()

        # Version should not call setup_console
        mock_setup_console.assert_not_called()

    @patch("fastmdsimulation.cli.setup_console")
    @patch("fastmdsimulation.cli.run_from_yaml")
    @patch("fastmdsimulation.cli.attach_file_logger")
    def test_cli_config_ignored_for_yaml(
        self,
        mock_attach_logger,
        mock_run_yaml,
        mock_setup_console,
        monkeypatch,
        tmp_path,
        waterbox_job_yaml,
        capsys,
    ):
        """Test that --config is ignored for YAML inputs with warning."""
        mock_run_yaml.return_value = str(tmp_path / "config_test" / "WaterBox")

        config_file = tmp_path / "dummy_config.yml"
        config_file.write_text("dummy: config")

        argv = [
            "fastmds",
            "simulate",
            "-system",
            str(waterbox_job_yaml),
            "--config",
            str(config_file),
        ]
        monkeypatch.setattr(sys, "argv", argv)

        from fastmdsimulation.cli import main

        main()

        captured = capsys.readouterr()
        assert "Warning: --config is ignored" in captured.out

        mock_run_yaml.assert_called_once_with(str(waterbox_job_yaml), "simulate_output")
