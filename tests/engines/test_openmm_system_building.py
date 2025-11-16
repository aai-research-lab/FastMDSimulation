from unittest.mock import Mock, patch

import pytest
from openmm.app import AmberPrmtopFile, CharmmPsfFile, ForceField, GromacsTopFile

from fastmdsimulation.engines.openmm_engine import (
    build_simulation_from_spec,
    create_system,
)


class TestCreateSystemFunction:
    """Test the create_system wrapper function"""

    def test_create_system_forcefield(self):
        """Test create_system with ForceField"""
        # Create a mock with the proper spec
        mock_ff = Mock(spec=ForceField)
        mock_topology = Mock()
        mock_system = Mock()
        mock_ff.createSystem.return_value = mock_system

        kwargs = {"nonbondedMethod": "PME"}

        system = create_system(mock_ff, topology=mock_topology, kwargs=kwargs)

        mock_ff.createSystem.assert_called_once_with(mock_topology, **kwargs)
        assert system == mock_system

    def test_create_system_forcefield_missing_topology(self):
        """Test create_system with ForceField but missing topology"""
        mock_ff = Mock(spec=ForceField)

        with pytest.raises(ValueError, match="ForceField requires 'topology'"):
            create_system(mock_ff, kwargs={})

    def test_create_system_amber(self):
        """Test create_system with AmberPrmtopFile"""
        mock_prmtop = Mock(spec=AmberPrmtopFile)
        mock_system = Mock()
        mock_prmtop.createSystem.return_value = mock_system

        system = create_system(mock_prmtop, kwargs={})

        mock_prmtop.createSystem.assert_called_once()
        assert system == mock_system

    def test_create_system_charmm_missing_paramset(self):
        """Test create_system with CharmmPsfFile but missing paramset"""
        mock_psf = Mock(spec=CharmmPsfFile)

        with pytest.raises(ValueError, match="CharmmPsfFile requires 'paramset'"):
            create_system(mock_psf, kwargs={})

    def test_create_system_charmm_with_paramset(self):
        """Test create_system with CharmmPsfFile and paramset"""
        mock_psf = Mock(spec=CharmmPsfFile)
        mock_paramset = Mock()
        mock_system = Mock()
        mock_psf.createSystem.return_value = mock_system

        system = create_system(mock_psf, paramset=mock_paramset, kwargs={})

        mock_psf.createSystem.assert_called_once_with(mock_paramset)
        assert system == mock_system

    def test_create_system_gromacs(self):
        """Test create_system with GromacsTopFile"""
        mock_top = Mock(spec=GromacsTopFile)
        mock_system = Mock()
        mock_top.createSystem.return_value = mock_system

        system = create_system(mock_top, kwargs={})

        mock_top.createSystem.assert_called_once()
        assert system == mock_system

    def test_create_system_unknown_type(self):
        """Test create_system with unknown object type"""
        unknown_obj = object()

        with pytest.raises(TypeError, match="Unsupported object type"):
            create_system(unknown_obj, kwargs={})

    def test_create_system_retry_unused_kwargs(self):
        """Test create_system retry logic for unused kwargs"""
        mock_ff = Mock(spec=ForceField)
        mock_topology = Mock()
        mock_system = Mock()

        # First call fails with unused kwargs error, second succeeds
        mock_ff.createSystem.side_effect = [
            ValueError(
                "The argument 'invalid_arg' was specified to createSystem() but was never used."
            ),
            mock_system,
        ]

        kwargs = {"invalid_arg": True, "valid_arg": True}

        system = create_system(mock_ff, topology=mock_topology, kwargs=kwargs)

        # Should have been called twice
        assert mock_ff.createSystem.call_count == 2
        # Second call should have removed the invalid arg
        second_call_kwargs = mock_ff.createSystem.call_args[1]
        assert "invalid_arg" not in second_call_kwargs
        assert "valid_arg" in second_call_kwargs
        assert system == mock_system

    def test_create_system_retry_other_error(self):
        """Test create_system doesn't retry on non-unused-kwarg errors"""
        mock_ff = Mock(spec=ForceField)
        mock_topology = Mock()

        # Different error that shouldn't trigger retry
        mock_ff.createSystem.side_effect = ValueError("Some other error")

        with pytest.raises(ValueError, match="Some other error"):
            create_system(mock_ff, topology=mock_topology, kwargs={})


class TestBuildSimulation:
    """Test build_simulation_from_spec function"""

    def test_build_simulation_pdb(self, tmp_jobdir, sample_pdb_file):
        """Test PDB-based simulation building"""
        spec = {"type": "pdb", "pdb": str(sample_pdb_file)}

        defaults = {
            "forcefield": ["amber14-all.xml", "amber14/tip3p.xml"],
            "platform": "Reference",
        }

        with patch(
            "fastmdsimulation.engines.openmm_engine._build_simulation"
        ) as mock_build:
            mock_sim = Mock()
            mock_build.return_value = mock_sim
            result = build_simulation_from_spec(spec, defaults, tmp_jobdir)

            mock_build.assert_called_once()
            assert result == mock_sim

    def test_build_simulation_amber(self, tmp_jobdir):
        """Test AMBER-based simulation building"""
        spec = {"type": "amber", "prmtop": "test.prmtop", "inpcrd": "test.inpcrd"}

        defaults = {"platform": "Reference"}

        with patch(
            "fastmdsimulation.engines.openmm_engine._build_from_amber"
        ) as mock_build:
            mock_sim = Mock()
            mock_build.return_value = mock_sim
            result = build_simulation_from_spec(spec, defaults, tmp_jobdir)

            mock_build.assert_called_once()
            assert result == mock_sim

    def test_build_simulation_gromacs(self, tmp_jobdir):
        """Test GROMACS-based simulation building"""
        spec = {"type": "gromacs", "top": "test.top", "gro": "test.gro"}

        defaults = {"platform": "Reference"}

        with patch(
            "fastmdsimulation.engines.openmm_engine._build_from_gromacs"
        ) as mock_build:
            mock_sim = Mock()
            mock_build.return_value = mock_sim
            result = build_simulation_from_spec(spec, defaults, tmp_jobdir)

            mock_build.assert_called_once()
            assert result == mock_sim

    def test_build_simulation_charmm(self, tmp_jobdir):
        """Test CHARMM-based simulation building"""
        spec = {
            "type": "charmm",
            "psf": "test.psf",
            "pdb": "test.pdb",
            "params": ["par_all36_prot.prm"],
        }

        defaults = {"platform": "Reference"}

        with patch(
            "fastmdsimulation.engines.openmm_engine._build_from_charmm"
        ) as mock_build:
            mock_sim = Mock()
            mock_build.return_value = mock_sim
            result = build_simulation_from_spec(spec, defaults, tmp_jobdir)

            mock_build.assert_called_once()
            assert result == mock_sim

    def test_build_simulation_auto_detect_pdb(self, tmp_jobdir, sample_pdb_file):
        """Test automatic PDB system type detection"""
        spec = {"pdb": str(sample_pdb_file)}
        defaults = {"platform": "Reference"}

        with patch(
            "fastmdsimulation.engines.openmm_engine._build_simulation"
        ) as mock_build:
            mock_sim = Mock()
            mock_build.return_value = mock_sim
            result = build_simulation_from_spec(spec, defaults, tmp_jobdir)

            mock_build.assert_called_once()
            assert result == mock_sim

    def test_build_simulation_auto_detect_amber(self, tmp_jobdir):
        """Test automatic AMBER system type detection"""
        spec = {"prmtop": "test.prmtop", "inpcrd": "test.inpcrd"}

        defaults = {"platform": "Reference"}

        with patch(
            "fastmdsimulation.engines.openmm_engine._build_from_amber"
        ) as mock_build:
            mock_sim = Mock()
            mock_build.return_value = mock_sim
            result = build_simulation_from_spec(spec, defaults, tmp_jobdir)

            mock_build.assert_called_once()
            assert result == mock_sim

    def test_build_simulation_unknown_type(self, tmp_jobdir):
        """Test error handling for unknown system type"""
        spec = {"type": "unknown"}
        defaults = {}

        with pytest.raises(ValueError, match="Unknown system type"):
            build_simulation_from_spec(spec, defaults, tmp_jobdir)

    def test_build_simulation_cannot_infer_type(self, tmp_jobdir):
        """Test error handling when system type cannot be inferred"""
        spec = {"invalid_key": "value"}
        defaults = {}

        with pytest.raises(ValueError, match="Cannot infer simulation type"):
            build_simulation_from_spec(spec, defaults, tmp_jobdir)
