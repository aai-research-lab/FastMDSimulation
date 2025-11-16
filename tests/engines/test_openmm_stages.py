from unittest.mock import Mock, patch

from fastmdsimulation.engines.openmm_engine import run_stage

# import pytest


class TestRunStage:
    """Test run_stage function"""

    def test_run_stage_minimize(self, tmp_jobdir):
        """Test minimization stage - mock PDB writing"""
        # Mock simulation object
        mock_sim = Mock()
        mock_sim.system = Mock()
        mock_sim.system.getNumForces.return_value = 0
        mock_sim.system.getForce.return_value = Mock()
        mock_sim.system.getForce.return_value.__class__.__name__ = "MonteCarloBarostat"
        mock_sim.topology = Mock()
        mock_sim.context = Mock()
        mock_sim.context.getState.return_value.getPositions.return_value = Mock()

        # Mock the PDBFile.writeFile to avoid OpenMM internals
        with patch("openmm.app.PDBFile.writeFile"):
            stage = {"name": "minimize", "steps": 0}

            defaults = {
                "minimize_tolerance_kjmol": 10.0,
                "minimize_max_iterations": 100,
            }

            run_stage(mock_sim, stage, tmp_jobdir, defaults)

            # Should call minimizeEnergy
            mock_sim.minimizeEnergy.assert_called_once()

            # Should create output files
            assert (tmp_jobdir / "stage.json").exists()
            # PDB file writing is mocked, so we don't check for topology.pdb

    def test_run_stage_production(self, tmp_jobdir):
        """Test production MD stage - mock PDB writing"""
        mock_sim = Mock()
        mock_sim.system = Mock()
        mock_sim.system.getNumForces.return_value = 0
        mock_sim.system.getForce.return_value = Mock()
        mock_sim.system.getForce.return_value.__class__.__name__ = "MonteCarloBarostat"
        mock_sim.topology = Mock()
        mock_sim.context = Mock()
        mock_sim.context.getState.return_value.getPositions.return_value = Mock()

        # Mock the PDBFile.writeFile and reporters
        with patch("openmm.app.PDBFile.writeFile"):
            with patch("openmm.app.DCDReporter"):
                with patch("openmm.app.StateDataReporter"):
                    with patch("openmm.app.CheckpointReporter"):
                        stage = {"name": "production", "steps": 100, "ensemble": "NPT"}

                        defaults = {
                            "temperature_K": 300.0,
                            "pressure_atm": 1.0,
                            "report_interval": 1000,
                        }

                        run_stage(mock_sim, stage, tmp_jobdir, defaults)

                        # Should call step
                        mock_sim.step.assert_called_once_with(100)

                        # Should create stage.json
                        assert (tmp_jobdir / "stage.json").exists()

    def test_run_stage_with_reporters(self, tmp_jobdir):
        """Test that reporters are properly configured"""
        mock_sim = Mock()
        mock_sim.system = Mock()
        mock_sim.system.getNumForces.return_value = 0
        mock_sim.system.getForce.return_value = Mock()
        mock_sim.system.getForce.return_value.__class__.__name__ = "MonteCarloBarostat"
        mock_sim.topology = Mock()
        mock_sim.context = Mock()
        mock_sim.context.getState.return_value.getPositions.return_value = Mock()
        mock_sim.reporters = []  # Initialize empty reporters list

        # Mock file operations
        with patch("openmm.app.PDBFile.writeFile"):
            with patch("openmm.app.DCDReporter") as mock_dcd:
                with patch("openmm.app.StateDataReporter") as mock_state:
                    with patch("openmm.app.CheckpointReporter") as mock_checkpoint:
                        stage = {
                            "name": "equilibration",
                            "steps": 50,
                            "report_interval": 10,
                            "checkpoint_interval": 25,
                        }

                        defaults = {"temperature_K": 300.0}

                        run_stage(mock_sim, stage, tmp_jobdir, defaults)

                        # Should have called reporter constructors
                        mock_dcd.assert_called_once()
                        mock_state.assert_called_once()
                        mock_checkpoint.assert_called_once()

    def test_run_stage_nvt_ensemble(self, tmp_jobdir):
        """Test NVT ensemble (no barostat)"""
        mock_sim = Mock()
        mock_sim.system = Mock()
        mock_sim.system.getNumForces.return_value = 0
        mock_sim.topology = Mock()
        mock_sim.context = Mock()
        mock_sim.context.getState.return_value.getPositions.return_value = Mock()

        # Mock PDB writing
        with patch("openmm.app.PDBFile.writeFile"):
            stage = {"name": "nvt_equilibration", "steps": 50, "ensemble": "NVT"}

            defaults = {"temperature_K": 300.0}

            run_stage(mock_sim, stage, tmp_jobdir, defaults)

            # Should not add barostat for NVT
            mock_sim.system.addForce.assert_not_called()
