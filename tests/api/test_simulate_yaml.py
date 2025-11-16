from unittest.mock import patch

from fastmdsimulation.api import FastMDSimulation


class TestFastMDSimulationSimulateYAML:
    """Test the simulate method with YAML files."""

    def test_simulate_with_yaml_file_no_analysis(self, tmp_path):
        """Test simulation with YAML file and no analysis."""
        yaml_file = tmp_path / "job.yml"
        yaml_file.write_text("project: test")

        with patch("fastmdsimulation.api.run_from_yaml") as mock_run_yaml:
            mock_run_yaml.return_value = "/mock/project/dir"

            api = FastMDSimulation(str(yaml_file), output="test_output")
            result = api.simulate(analyze=False)

            mock_run_yaml.assert_called_once_with(str(yaml_file), "test_output")
            assert result == "/mock/project/dir"

    def test_simulate_with_yaml_file_and_config_warning(self, tmp_path, caplog):
        """Test that config is ignored with YAML file and warning is logged."""
        yaml_file = tmp_path / "job.yml"
        yaml_file.write_text("project: test")

        with patch("fastmdsimulation.api.run_from_yaml") as mock_run_yaml:
            mock_run_yaml.return_value = "/mock/project/dir"

            api = FastMDSimulation(
                str(yaml_file), output="test_output", config="config.yml"
            )
            result = api.simulate(analyze=False)

            # Verify warning was logged
            assert (
                "Ignoring `config`: a job YAML was supplied as `system`." in caplog.text
            )
            mock_run_yaml.assert_called_once_with(str(yaml_file), "test_output")
            assert result == "/mock/project/dir"

    def test_simulate_with_yaml_file_uppercase_extension(self, tmp_path):
        """Test simulation with YAML file with uppercase extension."""
        yaml_file = tmp_path / "job.YML"
        yaml_file.write_text("project: test")

        with patch("fastmdsimulation.api.run_from_yaml") as mock_run_yaml:
            mock_run_yaml.return_value = "/mock/project/dir"

            api = FastMDSimulation(str(yaml_file), output="test_output")
            result = api.simulate(analyze=False)

            mock_run_yaml.assert_called_once_with(str(yaml_file), "test_output")
            assert result == "/mock/project/dir"
