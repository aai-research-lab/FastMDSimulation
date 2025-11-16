from unittest.mock import patch

from fastmdsimulation.api import FastMDSimulation


class TestFastMDSimulationSimulatePDB:
    """Test the simulate method with PDB files."""

    def test_simulate_with_pdb_file_no_analysis(self, tmp_path):
        """Test simulation with PDB file and no analysis."""
        pdb_file = tmp_path / "protein.pdb"
        pdb_file.write_text(
            "ATOM      1  N   ALA A   1       0.000   0.000   0.000  1.00  0.00           N\nEND"
        )

        with patch("fastmdsimulation.api.simulate_from_pdb") as mock_simulate:
            mock_simulate.return_value = "/mock/project/dir"

            api = FastMDSimulation(str(pdb_file), output="test_output")
            result = api.simulate(analyze=False)

            mock_simulate.assert_called_once_with(
                str(pdb_file), outdir="test_output", config=None
            )
            assert result == "/mock/project/dir"

    def test_simulate_with_pdb_file_with_config(self, tmp_path):
        """Test simulation with PDB file and config."""
        pdb_file = tmp_path / "protein.pdb"
        pdb_file.write_text(
            "ATOM      1  N   ALA A   1       0.000   0.000   0.000  1.00  0.00           N\nEND"
        )

        with patch("fastmdsimulation.api.simulate_from_pdb") as mock_simulate:
            mock_simulate.return_value = "/mock/project/dir"

            api = FastMDSimulation(
                str(pdb_file), output="test_output", config="config.yml"
            )
            result = api.simulate(analyze=False)

            mock_simulate.assert_called_once_with(
                str(pdb_file), outdir="test_output", config="config.yml"
            )
            assert result == "/mock/project/dir"

    def test_simulate_analysis_disabled_by_default(self, tmp_path):
        """Test that analysis is disabled by default."""
        pdb_file = tmp_path / "protein.pdb"
        pdb_file.write_text(
            "ATOM      1  N   ALA A   1       0.000   0.000   0.000  1.00  0.00           N\nEND"
        )

        with (
            patch("fastmdsimulation.api.simulate_from_pdb") as mock_simulate,
            patch(
                "fastmdsimulation.reporting.analysis_bridge.analyze_with_bridge"
            ) as mock_analyze,
        ):

            mock_simulate.return_value = "/mock/project/dir"

            api = FastMDSimulation(str(pdb_file), output="test_output")
            result = api.simulate()  # No analyze parameter

            mock_simulate.assert_called_once()
            mock_analyze.assert_not_called()
            assert result == "/mock/project/dir"
