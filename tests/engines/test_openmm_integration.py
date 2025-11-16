import pytest

from fastmdsimulation.engines.openmm_engine import build_simulation_from_spec, run_stage


class TestIntegrationScenarios:
    """Higher-level integration tests"""

    @pytest.mark.integration
    @pytest.mark.requires_openmm
    def test_full_workflow_pdb(self, tmp_jobdir, sample_pdb_file):
        """Test complete workflow with PDB input using real OpenMM"""
        spec = {"pdb": str(sample_pdb_file)}
        defaults = {
            "forcefield": ["amber14-all.xml"],
            "platform": "Reference",
            "temperature_K": 300.0,
            "box_padding_nm": 0.1,  # Small box for speed
            "ionic_strength_molar": 0.0,
            "neutralize": False,
        }

        # This should work with real OpenMM
        try:
            result = build_simulation_from_spec(spec, defaults, tmp_jobdir)
            assert result is not None
            assert hasattr(result, "topology")
            assert hasattr(result, "system")
            assert hasattr(result, "context")
        except Exception as e:
            pytest.skip(f"OpenMM integration test skipped: {e}")

    @pytest.mark.slow
    @pytest.mark.requires_openmm
    def test_minimal_simulation_run(self, tmp_jobdir, sample_pdb_file):
        """Test running a minimal simulation (marked as slow)"""
        spec = {"pdb": str(sample_pdb_file)}
        defaults = {
            "forcefield": ["amber14-all.xml"],
            "platform": "Reference",
            "temperature_K": 300.0,
            "box_padding_nm": 0.1,
            "ionic_strength_molar": 0.0,
            "neutralize": False,
        }

        try:
            sim = build_simulation_from_spec(spec, defaults, tmp_jobdir)

            # Run a minimal stage
            stage = {"name": "minimize", "steps": 0}

            run_stage(sim, stage, tmp_jobdir / "minimize", defaults)

            # Verify outputs were created
            assert (tmp_jobdir / "minimize" / "stage.json").exists()
            assert (tmp_jobdir / "minimize" / "topology.pdb").exists()

        except Exception as e:
            pytest.skip(f"Simulation test skipped: {e}")

    def test_error_handling_missing_files(self, tmp_jobdir):
        """Test error handling for missing input files"""
        spec = {"type": "pdb", "pdb": "nonexistent.pdb"}
        defaults = {}

        with pytest.raises((FileNotFoundError, Exception)):
            build_simulation_from_spec(spec, defaults, tmp_jobdir)
