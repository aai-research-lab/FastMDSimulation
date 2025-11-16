from unittest.mock import Mock, patch

import pytest
from openmm.app import (
    PME,
    AllBonds,
    CutoffNonPeriodic,
    CutoffPeriodic,
    Ewald,
    HAngles,
    HBonds,
    NoCutoff,
)

from fastmdsimulation.engines.openmm_engine import (
    _constraints_from_str,
    _create_system_kwargs,
    _get_minimize_tolerance,
    _load_forcefield,
    _map_nonbonded_method,
    _parse_ions,
    _select_platform,
)


class TestOpenMMEngineHelpers:
    """Test helper functions"""

    def test_load_forcefield_success(self):
        """Test loading forcefield with standard files"""
        with patch("openmm.app.ForceField") as mock_ff:
            mock_instance = Mock()
            mock_ff.return_value = mock_instance
            result = _load_forcefield(["amber14-all.xml", "amber14/tip3p.xml"])
            mock_ff.assert_called_once_with("amber14-all.xml", "amber14/tip3p.xml")
            assert result == mock_instance

    def test_load_forcefield_fallback(self):
        """Test forcefield loading with fallback behavior"""
        with patch("openmm.app.ForceField") as mock_ff:
            mock_instance = Mock()
            # First call fails, second succeeds (simulating fallback working)
            mock_ff.side_effect = [Exception("First attempt failed"), mock_instance]

            result = _load_forcefield(["test.xml"])
            assert result == mock_instance
            assert mock_ff.call_count == 2

    def test_load_forcefield_fallback_fails(self):
        """Test forcefield loading when all attempts fail"""
        with patch("openmm.app.ForceField") as mock_ff:
            # Both attempts fail
            mock_ff.side_effect = Exception("All attempts failed")

            with pytest.raises(Exception, match="All attempts failed"):
                _load_forcefield(["test.xml"])

    def test_select_platform_auto(self):
        """Test automatic platform selection with mocked platforms"""
        # Mock the platform selection logic
        with patch("openmm.Platform") as mock_platform:
            # Create mock platforms that will be tried in order
            # mock_cuda = Mock()
            mock_cpu = Mock()

            # Simulate CUDA failing, CPU succeeding
            mock_platform.getPlatformByName.side_effect = [
                Exception("CUDA not available"),
                mock_cpu,  # CPU succeeds
            ]

            platform = _select_platform("auto")
            assert platform == mock_cpu

    def test_select_platform_specific(self):
        """Test specific platform selection"""
        with patch("openmm.Platform") as mock_platform:
            mock_cpu = Mock()
            mock_platform.getPlatformByName.return_value = mock_cpu
            platform = _select_platform("CPU")
            mock_platform.getPlatformByName.assert_called_once_with("CPU")
            assert platform == mock_cpu

    def test_select_platform_invalid(self):
        """Test platform selection with invalid platform name"""
        with patch("openmm.Platform") as mock_platform:
            mock_platform.getPlatformByName.side_effect = Exception(
                "Platform not found"
            )
            with pytest.raises(Exception):
                _select_platform("InvalidPlatform")

    def test_parse_ions_string(self):
        """Test ion parsing from string specification"""
        # Test NaCl
        pos, neg = _parse_ions({"ions": "NaCl"})
        assert pos == "Na+"
        assert neg == "Cl-"

        # Test KCl
        pos, neg = _parse_ions({"ions": "KCl"})
        assert pos == "K+"
        assert neg == "Cl-"

        # Test unknown falls back to NaCl
        pos, neg = _parse_ions({"ions": "Unknown"})
        assert pos == "Na+"
        assert neg == "Cl-"

    def test_parse_ions_dict(self):
        """Test ion parsing from dictionary specification"""
        config = {"ions": {"positiveIon": "K+", "negativeIon": "Br-"}}
        pos, neg = _parse_ions(config)
        assert pos == "K+"
        assert neg == "Br-"

    def test_parse_ions_empty(self):
        """Test ion parsing with empty config"""
        pos, neg = _parse_ions({})
        assert pos == "Na+"
        assert neg == "Cl-"

    def test_get_minimize_tolerance(self):
        """Test minimization tolerance parsing"""
        # Test with nm units
        tol, val = _get_minimize_tolerance({"minimize_tolerance_kjmol_per_nm": 5.0})
        assert val == 5.0

        # Test with legacy units
        tol, val = _get_minimize_tolerance({"minimize_tolerance_kjmol": 10.0})
        assert val == 10.0

        # Test default
        tol, val = _get_minimize_tolerance({})
        assert val == 10.0

    def test_constraints_from_str(self):
        """Test constraint string parsing"""
        assert _constraints_from_str("none") is None
        assert _constraints_from_str("hbonds") == HBonds
        assert _constraints_from_str("allbonds") == AllBonds
        assert _constraints_from_str("hangles") == HAngles
        assert _constraints_from_str("HBonds") == HBonds  # case insensitive
        assert _constraints_from_str(None) is None
        assert _constraints_from_str("unknown") == HBonds  # default

    def test_map_nonbonded_method(self):
        """Test nonbonded method mapping"""
        assert _map_nonbonded_method("nocutoff") == NoCutoff
        assert _map_nonbonded_method("pme") == PME
        assert _map_nonbonded_method("ewald") == Ewald
        assert _map_nonbonded_method("cutoffnonperiodic") == CutoffNonPeriodic
        assert _map_nonbonded_method("cutoffperiodic") == CutoffPeriodic
        assert _map_nonbonded_method("unknown") is None
        assert _map_nonbonded_method("") is None


class TestCreateSystemKwargs:
    """Test _create_system_kwargs function"""

    def test_create_system_kwargs_basic(self):
        """Test basic kwargs creation"""
        config = {
            "create_system": {
                "constraints": "hbonds",
                "nonbondedMethod": "PME",
                "nonbondedCutoff_nm": 1.0,
                "switchDistance_nm": 0.8,
                "removeCMMotion": True,
            }
        }

        kwargs = _create_system_kwargs(config)

        assert "constraints" in kwargs
        assert "nonbondedMethod" in kwargs
        assert "nonbondedCutoff" in kwargs
        assert "switchingDistance" in kwargs
        assert kwargs["_removeCMMotion"] is True

    def test_create_system_kwargs_booleans(self):
        """Test boolean parameter handling"""
        config = {
            "create_system": {
                "useSwitchingFunction": True,
                "rigidWater": False,
                "longRangeDispersionCorrection": True,
            }
        }

        kwargs = _create_system_kwargs(config)

        assert kwargs["useSwitchingFunction"] is True
        assert kwargs["rigidWater"] is False
        assert kwargs["useDispersionCorrection"] is True

    def test_create_system_kwargs_hydrogen_mass(self):
        """Test hydrogen mass repartitioning"""
        config = {"create_system": {"hydrogenMass_amu": 2.0}}

        kwargs = _create_system_kwargs(config)
        assert "hydrogenMass" in kwargs

    def test_create_system_kwargs_empty(self):
        """Test kwargs creation with empty config"""
        kwargs = _create_system_kwargs({})
        # Default _removeCMMotion should be False
        assert kwargs == {"_removeCMMotion": False}

    def test_create_system_kwargs_invalid_method(self):
        """Test error handling for invalid nonbonded method"""
        config = {"create_system": {"nonbondedMethod": "invalid_method"}}

        with pytest.raises(ValueError, match="Unknown nonbondedMethod"):
            _create_system_kwargs(config)
