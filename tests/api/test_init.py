from fastmdsimulation.api import FastMDSimulation


class TestFastMDSimulationInit:
    """Test the FastMDSimulation initialization."""

    def test_init_with_pdb_file(self, tmp_path):
        """Test initialization with a PDB file."""
        pdb_file = tmp_path / "protein.pdb"
        pdb_file.write_text(
            "ATOM      1  N   ALA A   1       0.000   0.000   0.000  1.00  0.00           N\nEND"
        )

        api = FastMDSimulation(str(pdb_file), output="test_output", config="config.yml")

        assert api.system == str(pdb_file)
        assert api.output == "test_output"
        assert api.config == "config.yml"

    def test_init_with_yaml_file(self, tmp_path):
        """Test initialization with a YAML file."""
        yaml_file = tmp_path / "job.yml"
        yaml_file.write_text("project: test")

        api = FastMDSimulation(str(yaml_file), output="test_output")

        assert api.system == str(yaml_file)
        assert api.output == "test_output"
        assert api.config is None

    def test_init_with_none_config(self):
        """Test initialization with None config."""
        api = FastMDSimulation("protein.pdb", output="test_output", config=None)

        assert api.system == "protein.pdb"
        assert api.output == "test_output"
        assert api.config is None

    def test_init_with_string_system(self):
        """Test initialization with string system paths."""
        api = FastMDSimulation("protein.pdb", output="output_dir")

        assert api.system == "protein.pdb"
        assert api.output == "output_dir"
        assert api.config is None
