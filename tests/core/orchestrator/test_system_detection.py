# tests/core/orchestrator/test_system_detection.py

import pytest

from fastmdsimulation.core.orchestrator import _detect_system_type


class TestSystemTypeDetection:
    """Test system type detection logic."""

    def test_detect_pdb_type_with_pdb(self):
        sys_cfg = {"pdb": "test.pdb"}
        result = _detect_system_type(sys_cfg)
        assert result == "pdb"

    def test_detect_pdb_type_with_fixed_pdb(self):
        sys_cfg = {"fixed_pdb": "fixed.pdb"}
        result = _detect_system_type(sys_cfg)
        assert result == "pdb"

    def test_detect_amber_type(self):
        sys_cfg = {"prmtop": "test.prmtop", "inpcrd": "test.inpcrd"}
        result = _detect_system_type(sys_cfg)
        assert result == "amber"

    def test_detect_amber_type_with_rst7(self):
        sys_cfg = {"prmtop": "test.prmtop", "rst7": "test.rst7"}
        result = _detect_system_type(sys_cfg)
        assert result == "amber"

    def test_detect_gromacs_type(self):
        sys_cfg = {"top": "test.top", "gro": "test.gro"}
        result = _detect_system_type(sys_cfg)
        assert result == "gromacs"

    def test_detect_gromacs_type_with_g96(self):
        sys_cfg = {"top": "test.top", "g96": "test.g96"}
        result = _detect_system_type(sys_cfg)
        assert result == "gromacs"

    def test_detect_charmm_type(self):
        sys_cfg = {"psf": "test.psf", "params": "test.params"}
        result = _detect_system_type(sys_cfg)
        assert result == "charmm"

    def test_detect_charmm_type_with_prm(self):
        sys_cfg = {"psf": "test.psf", "prm": "test.prm"}
        result = _detect_system_type(sys_cfg)
        assert result == "charmm"

    def test_detect_unknown_type(self):
        sys_cfg = {"unknown": "format"}
        with pytest.raises(ValueError, match="Unrecognized system spec"):
            _detect_system_type(sys_cfg)
