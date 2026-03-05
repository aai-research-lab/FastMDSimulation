# from pathlib import Path
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

from fastmdsimulation.core.simulate import simulate_from_pdb


class TestSimulateFromPDB:
    """Test the simulate_from_pdb function."""

    def test_simulate_from_pdb_basic(self, tmp_path):
        """Test basic simulation from PDB without config."""
        # Create a mock PDB file
        pdb_file = tmp_path / "test_protein.pdb"
        pdb_file.write_text(
            "ATOM      1  N   ALA A   1       0.000   0.000   0.000  1.00  0.00           N\nEND"
        )

        # Mock both dependencies - CORRECTED import path
        with (
            patch(
                "fastmdsimulation.core.simulate.fix_pdb_with_pdbfixer"
            ) as mock_fix_pdb,
            patch(
                "fastmdsimulation.core.orchestrator.run_from_yaml"
            ) as mock_run_from_yaml,
        ):

            # Setup mocks
            mock_run_from_yaml.return_value = str(
                tmp_path / "simulate_output" / "test_protein-auto"
            )

            # Run function
            outdir = str(tmp_path / "simulate_output")
            result = simulate_from_pdb(str(pdb_file), outdir=outdir)

            # Verify PDB fixing was called
            mock_fix_pdb.assert_called_once()

            # Verify run_from_yaml was called with expected auto YAML path
            call_args = mock_run_from_yaml.call_args
            assert call_args[0][0].endswith("_build/job.auto.yml")
            assert result == str(tmp_path / "simulate_output" / "test_protein-auto")

            # Check that build directory was created
            build_dir = tmp_path / "simulate_output" / "test_protein-auto" / "_build"
            assert build_dir.exists()

    def test_simulate_from_pdb_with_config(self, tmp_path):
        """Test simulation from PDB with custom config."""
        # Create mock files
        pdb_file = tmp_path / "test_protein.pdb"
        pdb_file.write_text(
            "ATOM      1  N   ALA A   1       0.000   0.000   0.000  1.00  0.00           N\nEND"
        )

        config_file = tmp_path / "config.yml"
        config_data = {
            "defaults": {"temperature_K": 310, "timestep_fs": 1.0},
            "stages": [{"name": "minimize", "steps": 100}],
        }
        with open(config_file, "w") as f:
            yaml.dump(config_data, f)

        # Mock both dependencies - CORRECTED import path
        with (
            patch(
                "fastmdsimulation.core.simulate.fix_pdb_with_pdbfixer"
            ) as mock_fix_pdb,
            patch(
                "fastmdsimulation.core.orchestrator.run_from_yaml"
            ) as mock_run_from_yaml,
        ):

            # Setup mocks
            mock_run_from_yaml.return_value = "/some/output/path"

            # Run function with config
            simulate_from_pdb(str(pdb_file), config=str(config_file))

            # Verify config was loaded and merged
            mock_fix_pdb.assert_called_once()
            mock_run_from_yaml.assert_called_once()

            # The YAML file passed to run_from_yaml should contain merged config
            yaml_path = mock_run_from_yaml.call_args[0][0]
            with open(yaml_path, "r") as f:
                final_config = yaml.safe_load(f)

            # Check that custom config values were merged
            assert final_config["defaults"]["temperature_K"] == 310
            assert final_config["defaults"]["timestep_fs"] == 1.0
            # But original values should still be there
            assert final_config["defaults"]["engine"] == "openmm"

    def test_simulate_from_pdb_source_pdb_recorded(self, tmp_path):
        """Test that original PDB source is recorded in config."""
        # Create a mock PDB file
        pdb_file = tmp_path / "test_protein.pdb"
        pdb_file.write_text(
            "ATOM      1  N   ALA A   1       0.000   0.000   0.000  1.00  0.00           N\nEND"
        )

        # Mock both dependencies - CORRECTED import path
        with (
            patch("fastmdsimulation.core.simulate.fix_pdb_with_pdbfixer"),
            patch(
                "fastmdsimulation.core.orchestrator.run_from_yaml"
            ) as mock_run_from_yaml,
        ):

            # Setup mocks
            mock_run_from_yaml.return_value = "/some/output/path"

            # Run function
            simulate_from_pdb(str(pdb_file))

            # Get the auto-generated YAML config
            yaml_path = mock_run_from_yaml.call_args[0][0]
            with open(yaml_path, "r") as f:
                final_config = yaml.safe_load(f)

            # Check that source_pdb is recorded
            assert final_config["systems"][0]["source_pdb"] == str(pdb_file)

    def test_simulate_from_pdb_nonexistent_pdb(self, tmp_path):
        """Test behavior with non-existent PDB file."""
        nonexistent_pdb = tmp_path / "nonexistent.pdb"

        with pytest.raises(FileNotFoundError):
            simulate_from_pdb(str(nonexistent_pdb))

    def test_simulate_from_pdb_nonexistent_config(self, tmp_path):
        """Test behavior with non-existent config file."""
        # Create a mock PDB file
        pdb_file = tmp_path / "test_protein.pdb"
        pdb_file.write_text(
            "ATOM      1  N   ALA A   1       0.000   0.000   0.000  1.00  0.00           N\nEND"
        )

        nonexistent_config = tmp_path / "nonexistent_config.yml"

        with pytest.raises(FileNotFoundError):
            simulate_from_pdb(str(pdb_file), config=str(nonexistent_config))

    def test_simulate_from_pdb_empty_config(self, tmp_path):
        """Test with empty config file."""
        # Create a mock PDB file
        pdb_file = tmp_path / "test_protein.pdb"
        pdb_file.write_text(
            "ATOM      1  N   ALA A   1       0.000   0.000   0.000  1.00  0.00           N\nEND"
        )

        empty_config = tmp_path / "empty.yml"
        empty_config.write_text("")

        # Mock both dependencies - CORRECTED import path
        with (
            patch("fastmdsimulation.core.simulate.fix_pdb_with_pdbfixer"),
            patch(
                "fastmdsimulation.core.orchestrator.run_from_yaml"
            ) as mock_run_from_yaml,
        ):

            # Should not raise an error
            simulate_from_pdb(str(pdb_file), config=str(empty_config))
            mock_run_from_yaml.assert_called_once()

    def test_simulate_from_pdb_relative_paths(self, tmp_path):
        """Test with relative paths that need resolution."""
        # Create PDB in subdirectory
        pdb_dir = tmp_path / "subdir"
        pdb_dir.mkdir()
        pdb_file = pdb_dir / "rel_protein.pdb"
        pdb_file.write_text(
            "ATOM      1  N   ALA A   1       0.000   0.000   0.000  1.00  0.00           N\nEND"
        )

        # Mock both dependencies - CORRECTED import path
        with (
            patch(
                "fastmdsimulation.core.simulate.fix_pdb_with_pdbfixer"
            ) as mock_fix_pdb,
            patch(
                "fastmdsimulation.core.orchestrator.run_from_yaml"
            ) as mock_run_from_yaml,
        ):

            # Use a path with tilde that still resolves to the actual file
            relative_pdb = str(pdb_file).replace(str(Path.home()), "~")

            simulate_from_pdb(relative_pdb, outdir=str(tmp_path / "output"))

            # Verify paths were resolved
            mock_fix_pdb.assert_called_once()
            mock_run_from_yaml.assert_called_once()

    @pytest.mark.requires_openmm
    def test_simulate_from_pdb_integration(self, water2nm_pdb, tmp_path):
        """Integration test with actual water PDB."""
        # Mock both dependencies - CORRECTED import path
        with (
            patch(
                "fastmdsimulation.core.simulate.fix_pdb_with_pdbfixer"
            ) as mock_fix_pdb,
            patch(
                "fastmdsimulation.core.orchestrator.run_from_yaml"
            ) as mock_run_from_yaml,
        ):

            # Setup mock
            mock_run_from_yaml.return_value = "/mock/output"

            # Run with real water PDB
            simulate_from_pdb(str(water2nm_pdb))

            # Verify basic workflow
            mock_fix_pdb.assert_called_once()
            mock_run_from_yaml.assert_called_once()

            # Check that auto YAML was created with water system
            yaml_path = mock_run_from_yaml.call_args[0][0]
            with open(yaml_path, "r") as f:
                config = yaml.safe_load(f)

            assert "water" in config["project"].lower() or "auto" in config["project"]
            assert config["systems"][0]["source_pdb"] == str(water2nm_pdb)
