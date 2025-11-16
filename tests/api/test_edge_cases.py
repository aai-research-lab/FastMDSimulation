from unittest.mock import patch

from fastmdsimulation.api import FastMDSimulation


class TestFastMDSimulationEdgeCases:
    """Test edge cases and error conditions for FastMDSimulation."""

    def test_simulate_with_empty_frames_string(self, tmp_path):
        """Test simulation with empty frames string."""
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
            result = api.simulate(analyze=True, frames="", atoms="")

            mock_analyze.assert_called_once_with(
                "/mock/project/dir", slides=True, frames="", atoms=""
            )
            assert result == "/mock/project/dir"

    def test_simulate_with_none_analysis_params(self, tmp_path):
        """Test simulation with None analysis parameters."""
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
            result = api.simulate(analyze=True, frames=None, atoms=None, slides=False)

            mock_analyze.assert_called_once_with(
                "/mock/project/dir", slides=False, frames=None, atoms=None
            )
            assert result == "/mock/project/dir"
