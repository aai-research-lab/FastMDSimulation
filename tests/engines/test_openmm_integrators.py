# from unittest.mock import Mock

import pytest

from fastmdsimulation.engines.openmm_engine import _make_integrator


class TestIntegratorCreation:
    """Test _make_integrator function"""

    def test_make_langevin_integrator(self):
        """Test Langevin integrator creation"""
        defaults = {"temperature_K": 300.0, "timestep_fs": 2.0, "friction_ps": 1.0}

        integrator = _make_integrator(defaults)
        assert integrator.__class__.__name__ == "LangevinIntegrator"

    def test_make_langevin_middle_integrator(self):
        """Test LangevinMiddle integrator creation"""
        defaults = {
            "integrator": "langevin_middle",
            "temperature_K": 300.0,
            "timestep_fs": 4.0,
            "friction_ps": 1.0,
        }

        integrator = _make_integrator(defaults)
        assert integrator.__class__.__name__ == "LangevinMiddleIntegrator"

    def test_make_verlet_integrator(self):
        """Test Verlet integrator creation"""
        defaults = {"integrator": "verlet", "timestep_fs": 2.0}

        integrator = _make_integrator(defaults)
        assert integrator.__class__.__name__ == "VerletIntegrator"

    def test_make_integrator_with_dict_spec(self):
        """Test integrator creation with dictionary specification"""
        spec = {"integrator": {"name": "verlet", "timestep_fs": 2.0}}

        integrator = _make_integrator(spec)
        assert integrator.__class__.__name__ == "VerletIntegrator"

    def test_make_integrator_custom_params(self):
        """Test integrator creation with custom parameters"""
        spec = {
            "integrator": {
                "name": "langevin",
                "temperature_K": 310.0,
                "timestep_fs": 1.0,
                "friction_ps": 2.0,
            }
        }

        integrator = _make_integrator(spec)
        assert integrator.__class__.__name__ == "LangevinIntegrator"

    def test_make_integrator_unknown(self):
        """Test error handling for unknown integrator"""
        with pytest.raises(ValueError, match="Unsupported integrator"):
            _make_integrator({"integrator": "unknown_integrator"})
