from unittest.mock import patch

from fastmdsimulation.api import FastMDSimulation


class TestFastMDSimulationAnalysis:
    """Test the analysis functionality in FastMDSimulation."""

    def test_simulate_with_analysis_success(self, tmp_path):
        """Test simulation with successful analysis."""
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
            result = api.simulate(
                analyze=True, frames="0,-1,10", atoms="protein", slides=True
            )

            mock_simulate.assert_called_once()
            mock_analyze.assert_called_once_with(
                "/mock/project/dir", slides=True, frames="0,-1,10", atoms="protein"
            )
            assert result == "/mock/project/dir"

    def test_simulate_with_analysis_default_params(self, tmp_path):
        """Test simulation with analysis using default parameters."""
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
            result = api.simulate(analyze=True)

            mock_simulate.assert_called_once()
            mock_analyze.assert_called_once_with(
                "/mock/project/dir", slides=True, frames=None, atoms=None
            )
            assert result == "/mock/project/dir"

    def test_simulate_with_analysis_import_error(self, tmp_path, caplog):
        """Test simulation when analysis bridge cannot be imported."""
        pdb_file = tmp_path / "protein.pdb"
        pdb_file.write_text(
            "ATOM      1  N   ALA A   1       0.000   0.000   0.000  1.00  0.00           N\nEND"
        )

        with (
            patch("fastmdsimulation.api.simulate_from_pdb") as mock_simulate,
            patch(
                "fastmdsimulation.reporting.analysis_bridge.analyze_with_bridge",
                side_effect=ImportError("No module named 'fastmdanalysis'"),
            ),
        ):

            mock_simulate.return_value = "/mock/project/dir"

            api = FastMDSimulation(str(pdb_file), output="test_output")
            result = api.simulate(analyze=True)

            mock_simulate.assert_called_once()
            # Should log error but not raise exception
            assert "Analysis step failed or is unavailable" in caplog.text
            assert result == "/mock/project/dir"

    def test_simulate_with_analysis_runtime_error(self, tmp_path, caplog):
        """Test simulation when analysis bridge raises a runtime error."""
        pdb_file = tmp_path / "protein.pdb"
        pdb_file.write_text(
            "ATOM      1  N   ALA A   1       0.000   0.000   0.000  1.00  0.00           N\nEND"
        )

        with (
            patch("fastmdsimulation.api.simulate_from_pdb") as mock_simulate,
            patch(
                "fastmdsimulation.reporting.analysis_bridge.analyze_with_bridge",
                side_effect=RuntimeError("Analysis failed"),
            ),
        ):

            mock_simulate.return_value = "/mock/project/dir"

            api = FastMDSimulation(str(pdb_file), output="test_output")
            result = api.simulate(analyze=True)

            mock_simulate.assert_called_once()
            # Should log error but not raise exception
            assert "Analysis step failed or is unavailable" in caplog.text
            assert "Analysis failed" in caplog.text
            assert result == "/mock/project/dir"

    def test_simulate_with_yaml_and_analysis(self, tmp_path):
        """Test simulation with YAML file and analysis."""
        yaml_file = tmp_path / "job.yml"
        yaml_file.write_text("project: test")

        with (
            patch("fastmdsimulation.api.run_from_yaml") as mock_run_yaml,
            patch(
                "fastmdsimulation.reporting.analysis_bridge.analyze_with_bridge"
            ) as mock_analyze,
        ):

            mock_run_yaml.return_value = "/mock/project/dir"

            api = FastMDSimulation(str(yaml_file), output="test_output")
            result = api.simulate(
                analyze=True, slides=False, frames="100", atoms="backbone"
            )

            mock_run_yaml.assert_called_once_with(str(yaml_file), "test_output")
            mock_analyze.assert_called_once_with(
                "/mock/project/dir", slides=False, frames="100", atoms="backbone"
            )
            assert result == "/mock/project/dir"
