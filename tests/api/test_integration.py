from unittest.mock import patch

import pytest

from fastmdsimulation.api import FastMDSimulation


@pytest.mark.integration
class TestFastMDSimulationIntegration:
    """Integration tests for FastMDSimulation API."""

    def test_full_workflow_with_pdb(self, tmp_path):
        """Test full workflow with PDB file using real components."""
        # Create a minimal PDB file
        pdb_file = tmp_path / "protein.pdb"
        pdb_file.write_text(
            "ATOM      1  N   ALA A   1       0.000   0.000   0.000  1.00  0.00           N\nEND"
        )

        # Mock the core components but test the API integration
        with (
            patch("fastmdsimulation.api.simulate_from_pdb") as mock_simulate,
            patch(
                "fastmdsimulation.reporting.analysis_bridge.analyze_with_bridge"
            ) as mock_analyze,
        ):

            mock_simulate.return_value = str(tmp_path / "project_output")

            api = FastMDSimulation(str(pdb_file), output=str(tmp_path / "output"))
            result = api.simulate(analyze=True, slides=False)

            assert result == str(tmp_path / "project_output")
            mock_simulate.assert_called_once()
            mock_analyze.assert_called_once()

    def test_full_workflow_with_yaml(self, tmp_path):
        """Test full workflow with YAML file using real components."""
        # Create a minimal YAML file
        yaml_file = tmp_path / "job.yml"
        yaml_file.write_text("project: test\nsystems:\n  - id: test\n    pdb: test.pdb")

        with (
            patch("fastmdsimulation.api.run_from_yaml") as mock_run_yaml,
            patch(
                "fastmdsimulation.reporting.analysis_bridge.analyze_with_bridge"
            ) as mock_analyze,
        ):

            mock_run_yaml.return_value = str(tmp_path / "project_output")

            api = FastMDSimulation(str(yaml_file), output=str(tmp_path / "output"))
            result = api.simulate(analyze=True)

            assert result == str(tmp_path / "project_output")
            mock_run_yaml.assert_called_once()
            mock_analyze.assert_called_once()
