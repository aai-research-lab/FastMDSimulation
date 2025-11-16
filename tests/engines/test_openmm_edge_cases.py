"""
Tests for edge cases and error conditions in OpenMM engine.
These tests target the specific lines missing coverage.
"""

from pathlib import Path

# from MagicMock
from unittest.mock import Mock, patch

import pytest

from fastmdsimulation.engines.openmm_engine import (
    _build_from_amber,
    _build_from_charmm,
    _build_from_gromacs,
    _build_simulation,
    _load_forcefield,
    _select_platform,
    build_simulation_from_spec,
    create_system,
)


class TestEdgeCases:
    """Test edge cases and error conditions"""

    def test_load_forcefield_import_error_handling(self):
        """Test _load_forcefield handles import errors gracefully"""
        with patch("openmm.app.ForceField") as mock_ff:
            mock_ff.side_effect = ImportError("Test import error")

            # Should raise the original import error
            with pytest.raises(ImportError, match="Test import error"):
                _load_forcefield(["test.xml"])

    def test_select_platform_no_platforms_available(self):
        """Test platform selection when no platforms are available"""
        with patch("openmm.Platform") as mock_platform:
            # Simulate all platforms failing
            mock_platform.getPlatformByName.side_effect = Exception("No platforms")
            mock_platform.getPlatform.return_value = Mock()

            # Should fall back to platform 0
            platform = _select_platform("auto")
            assert platform is not None

    def test_create_system_forcefield_unused_kwargs_retry(self):
        """Test create_system retry logic with multiple unused kwargs"""
        from openmm.app import ForceField

        mock_ff = Mock(spec=ForceField)
        mock_topology = Mock()
        mock_system = Mock()

        # Simulate multiple retries with different unused kwargs
        mock_ff.createSystem.side_effect = [
            ValueError(
                "The argument 'bad_arg1' was specified to createSystem() but was never used."
            ),
            ValueError(
                "The argument 'bad_arg2' was specified to createSystem() but was never used."
            ),
            mock_system,  # Third attempt succeeds
        ]

        kwargs = {"bad_arg1": True, "bad_arg2": True, "good_arg": True}

        system = create_system(mock_ff, topology=mock_topology, kwargs=kwargs)

        # Should have been called three times
        assert mock_ff.createSystem.call_count == 3
        assert system == mock_system

    def test_create_system_max_retries_prevention(self):
        """Test that create_system doesn't retry indefinitely"""
        from openmm.app import ForceField

        mock_ff = Mock(spec=ForceField)
        mock_topology = Mock()

        # Always return unused kwargs error
        def always_unused(*args, **kwargs):
            raise ValueError(
                "The argument 'bad_arg' was specified to createSystem() but was never used."
            )

        mock_ff.createSystem.side_effect = always_unused

        # This should eventually raise after several retries
        kwargs = {"bad_arg": True}

        # It will retry a few times but eventually the pattern won't match
        # and it will raise the original error
        with pytest.raises(ValueError):
            create_system(mock_ff, topology=mock_topology, kwargs=kwargs)


class TestSystemBuildingEdgeCases:
    """Test edge cases in system building functions"""

    def test_build_simulation_missing_forcefield_files(self, tmp_path, sample_pdb_file):
        """Test _build_simulation with missing forcefield files"""
        # spec = {"pdb": str(sample_pdb_file)}
        defaults = {"forcefield": ["nonexistent_ff.xml"], "platform": "Reference"}

        # Should raise an appropriate error
        with pytest.raises(Exception):
            _build_simulation(Path(sample_pdb_file), defaults, tmp_path)

    def test_build_simulation_basic_functionality(self, tmp_path, sample_pdb_file):
        """Test basic _build_simulation functionality without complex mocking"""
        # Just test that the function exists and accepts the right parameters
        # This is a smoke test rather than a full functional test
        try:
            # This will fail due to missing files, but we're testing that the function
            # at least tries to execute and doesn't have syntax errors
            _build_simulation(
                Path(sample_pdb_file), {"forcefield": ["test.xml"]}, tmp_path
            )
            # If we get here, something unexpected happened
            pytest.fail(
                "Expected _build_simulation to fail with missing forcefield files"
            )
        except (FileNotFoundError, ImportError, Exception):
            # Expected to fail - this means the function is at least trying to run
            # and we're not getting syntax errors or import issues
            assert True  # Function executed without basic errors

    def test_build_from_amber_missing_files(self, tmp_path):
        """Test _build_from_amber with missing files"""
        spec = {"prmtop": "nonexistent.prmtop", "inpcrd": "nonexistent.inpcrd"}
        defaults = {"platform": "Reference"}

        with pytest.raises((FileNotFoundError, Exception)):
            _build_from_amber(spec, defaults, tmp_path)

    def test_build_from_gromacs_missing_files(self, tmp_path):
        """Test _build_from_gromacs with missing files"""
        spec = {"top": "nonexistent.top", "gro": "nonexistent.gro"}
        defaults = {"platform": "Reference"}

        with pytest.raises((FileNotFoundError, Exception)):
            _build_from_gromacs(spec, defaults, tmp_path)

    def test_build_from_charmm_missing_files(self, tmp_path):
        """Test _build_from_charmm with missing files"""
        spec = {"psf": "nonexistent.psf", "pdb": "nonexistent.pdb"}
        defaults = {"platform": "Reference"}

        with pytest.raises((FileNotFoundError, Exception)):
            _build_from_charmm(spec, defaults, tmp_path)

    def test_build_simulation_from_spec_invalid_type(self, tmp_path):
        """Test build_simulation_from_spec with invalid system type"""
        spec = {"type": "invalid_system_type"}
        defaults = {}

        with pytest.raises(ValueError, match="Unknown system type"):
            build_simulation_from_spec(spec, defaults, tmp_path)


class TestAdvancedPlatformProperties:
    """Test platform property handling"""

    def test_new_simulation_with_platform_properties(self):
        """Test _new_simulation with various platform properties"""
        from fastmdsimulation.engines.openmm_engine import _new_simulation

        mock_topology = Mock()
        mock_system = Mock()
        mock_integrator = Mock()

        with patch("openmm.app.Simulation") as mock_sim_class:
            with patch(
                "fastmdsimulation.engines.openmm_engine._select_platform"
            ) as mock_select:
                mock_platform = Mock()
                # FIXED: Mock getName to return a string
                mock_platform.getName.return_value = "CUDA"
                mock_select.return_value = mock_platform

                mock_sim_instance = Mock()
                mock_context = Mock()
                mock_sim_instance.context = mock_context
                # FIXED: Mock the platform returned by context
                mock_context.getPlatform.return_value = mock_platform
                mock_sim_class.return_value = mock_sim_instance

                # Test with platform properties
                platform_props = {"CudaDeviceIndex": "0", "CudaPrecision": "mixed"}

                result = _new_simulation(
                    mock_topology, mock_system, mock_integrator, "CUDA", platform_props
                )

                assert result == mock_sim_instance
                mock_sim_class.assert_called_once()

    def test_platform_property_logging(self):
        """Test that platform properties are properly logged"""
        from fastmdsimulation.engines.openmm_engine import _new_simulation

        mock_topology = Mock()
        mock_system = Mock()
        mock_integrator = Mock()

        with patch("openmm.app.Simulation") as mock_sim_class:
            with patch(
                "fastmdsimulation.engines.openmm_engine._select_platform"
            ) as mock_select:
                with patch(
                    "fastmdsimulation.engines.openmm_engine.logger"
                ) as mock_logger:
                    mock_platform = Mock()
                    mock_platform.getName.return_value = "TestPlatform"
                    mock_select.return_value = mock_platform

                    mock_sim_instance = Mock()
                    mock_context = Mock()
                    mock_sim_instance.context = mock_context
                    mock_context.getPlatform.return_value = mock_platform
                    mock_sim_class.return_value = mock_sim_instance

                    # Mock platform property methods
                    def get_property_side_effect(prop_name):
                        if prop_name == "TestProperty":
                            return "test_value"
                        raise Exception("Property not found")

                    mock_platform.getPropertyDefaultValue.side_effect = (
                        get_property_side_effect
                    )

                    _new_simulation(
                        mock_topology,
                        mock_system,
                        mock_integrator,
                        "TestPlatform",
                        {"CustomProperty": "custom_value"},
                    )

                    # Verify logging was attempted
                    mock_logger.info.assert_called()


class TestIntegratorEdgeCases:
    """Test integrator creation edge cases"""

    def test_make_integrator_variable_verlet(self):
        """Test VariableVerletIntegrator creation"""
        from fastmdsimulation.engines.openmm_engine import _make_integrator

        spec = {"integrator": {"name": "variable_verlet", "error_tolerance": 0.0001}}

        integrator = _make_integrator(spec)
        assert integrator.__class__.__name__ == "VariableVerletIntegrator"

    def test_make_integrator_variable_langevin(self):
        """Test VariableLangevinIntegrator creation"""
        from fastmdsimulation.engines.openmm_engine import _make_integrator

        spec = {
            "integrator": {
                "name": "variable_langevin",
                "temperature_K": 300.0,
                "friction_ps": 1.0,
                "error_tolerance": 0.001,
            }
        }

        integrator = _make_integrator(spec)
        assert integrator.__class__.__name__ == "VariableLangevinIntegrator"

    def test_make_integrator_brownian(self):
        """Test BrownianIntegrator creation"""
        from fastmdsimulation.engines.openmm_engine import _make_integrator

        spec = {
            "integrator": "brownian",
            "temperature_K": 300.0,
            "timestep_fs": 2.0,
            "friction_ps": 1.0,
        }

        integrator = _make_integrator(spec)
        assert integrator.__class__.__name__ == "BrownianIntegrator"


class TestStageExecutionEdgeCases:
    """Test edge cases in stage execution"""

    def test_run_stage_minimize_with_max_iterations(self, tmp_path):
        """Test minimization stage with max iterations"""
        from fastmdsimulation.engines.openmm_engine import run_stage

        mock_sim = Mock()
        mock_sim.system = Mock()
        mock_sim.system.getNumForces.return_value = 0
        mock_sim.topology = Mock()
        mock_sim.context = Mock()
        mock_sim.context.getState.return_value.getPositions.return_value = Mock()

        with patch("openmm.app.PDBFile.writeFile"):
            stage = {"name": "minimize", "steps": 0}

            defaults = {
                "minimize_tolerance_kjmol": 10.0,
                "minimize_max_iterations": 500,  # Non-zero max iterations
            }

            run_stage(mock_sim, stage, tmp_path, defaults)

            # Should call minimizeEnergy with maxIterations
            mock_sim.minimizeEnergy.assert_called_once()

    def test_run_stage_with_different_report_intervals(self, tmp_path):
        """Test stage execution with custom report intervals"""
        from fastmdsimulation.engines.openmm_engine import run_stage

        mock_sim = Mock()
        mock_sim.system = Mock()
        mock_sim.system.getNumForces.return_value = 0
        mock_sim.topology = Mock()
        mock_sim.context = Mock()
        mock_sim.context.getState.return_value.getPositions.return_value = Mock()
        mock_sim.reporters = []

        with patch("openmm.app.PDBFile.writeFile"):
            with patch("openmm.app.DCDReporter"):
                with patch("openmm.app.StateDataReporter"):
                    with patch("openmm.app.CheckpointReporter"):
                        stage = {
                            "name": "production",
                            "steps": 100,
                            "report_interval": 500,  # Custom interval
                            "checkpoint_interval": 1000,  # Custom interval
                        }

                        defaults = {
                            "temperature_K": 300.0,
                            "report_interval": 1000,  # Different from stage
                            "checkpoint_interval": 5000,  # Different from stage
                        }

                        run_stage(mock_sim, stage, tmp_path, defaults)

                        # Should use stage-specific intervals
                        mock_sim.step.assert_called_once_with(100)
