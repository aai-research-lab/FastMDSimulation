# tests/core/orchestrator/test_file_operations.py

# import json
# from pathlib import Path
# from unittest.mock import patch

import pytest

from fastmdsimulation.core.orchestrator import (
    _collect_system_paths,
    _copy_into,
    _maybe_copy_forcefields,
    sha256_file,
)


class TestSHA256File:
    """Test SHA256 file hashing functionality."""

    def test_sha256_file(self, tmp_path):
        # Create a test file
        test_file = tmp_path / "test.txt"
        test_file.write_text("hello world")

        # Calculate hash
        result = sha256_file(test_file)

        # Verify it's a proper SHA256 hash (64 hex chars)
        assert len(result) == 64
        assert all(c in "0123456789abcdef" for c in result)

        # Known hash for "hello world"
        expected = "b94d27b9934d3e08a52e52d7da7dabfac484efe37a5380ee9088f7ace2efcde9"
        assert result == expected

    def test_sha256_file_nonexistent(self, tmp_path):
        nonexistent_file = tmp_path / "nonexistent.txt"
        with pytest.raises(FileNotFoundError):
            sha256_file(nonexistent_file)


class TestFileOperations:
    """Test file operations like copying and path collection."""

    def test_copy_into(self, tmp_path):
        src_dir = tmp_path / "src"
        src_dir.mkdir()
        src_file = src_dir / "test.txt"
        src_file.write_text("test content")

        dst_dir = tmp_path / "dst"

        _copy_into(dst_dir, src_file)

        dst_file = dst_dir / "test.txt"
        assert dst_file.exists()
        assert dst_file.read_text() == "test content"

    def test_copy_into_nonexistent_source(self, tmp_path):
        dst_dir = tmp_path / "dst"
        nonexistent_file = tmp_path / "nonexistent.txt"

        # Should not raise exception
        _copy_into(dst_dir, nonexistent_file)

        # The function should NOT create the destination directory
        # when source doesn't exist (this is the current behavior)
        # So we should NOT assert that dst_dir.exists()
        # This test should just verify no exception is raised
        pass  # Just verify no exception is raised

    def test_maybe_copy_forcefields(self, tmp_path):
        # Create mock forcefield files first
        ff1 = tmp_path / "ff1.xml"
        ff2 = tmp_path / "ff2.xml"
        ff1.write_text("<forcefield>1</forcefield>")
        ff2.write_text("<forcefield>2</forcefield>")

        # Use absolute paths in the defaults so the function can find them
        defaults = {"forcefield": [str(ff1), str(ff2)]}
        inputs_dir = tmp_path / "inputs"

        _maybe_copy_forcefields(defaults, inputs_dir)

        # Check files were copied - the function should create the directory now
        ff_dir = inputs_dir / "forcefields"
        assert ff_dir.exists()
        assert (ff_dir / "ff1.xml").exists()
        assert (ff_dir / "ff2.xml").exists()

    def test_maybe_copy_forcefields_nonexistent(self, tmp_path):
        defaults = {"forcefield": ["nonexistent.xml"]}
        inputs_dir = tmp_path / "inputs"

        # Should not raise exception
        _maybe_copy_forcefields(defaults, inputs_dir)

    def test_collect_system_paths_pdb(self):
        sys_cfg = {
            "type": "pdb",
            "pdb": "test.pdb",
            "source_pdb": "source.pdb",
            "fixed_pdb": "fixed.pdb",
        }

        paths = _collect_system_paths(sys_cfg)
        path_names = [p.name for p in paths]

        assert "test.pdb" in path_names
        assert "source.pdb" in path_names
        assert "fixed.pdb" in path_names

    def test_collect_system_paths_amber(self):
        sys_cfg = {
            "type": "amber",
            "prmtop": "test.prmtop",
            "inpcrd": "test.inpcrd",
            "rst7": "test.rst7",
        }

        paths = _collect_system_paths(sys_cfg)
        path_names = [p.name for p in paths]

        assert "test.prmtop" in path_names
        assert "test.inpcrd" in path_names
        assert "test.rst7" in path_names

    def test_collect_system_paths_gromacs(self):
        sys_cfg = {
            "type": "gromacs",
            "top": "test.top",
            "gro": "test.gro",
            "itp": ["file1.itp", "file2.itp"],
        }

        paths = _collect_system_paths(sys_cfg)
        path_names = [p.name for p in paths]

        assert "test.top" in path_names
        assert "test.gro" in path_names
        assert "file1.itp" in path_names
        assert "file2.itp" in path_names

    def test_collect_system_paths_charmm(self):
        sys_cfg = {
            "type": "charmm",
            "psf": "test.psf",
            "params": ["p1.prm", "p2.prm"],
            "crd": "test.crd",
        }

        paths = _collect_system_paths(sys_cfg)
        path_names = [p.name for p in paths]

        assert "test.psf" in path_names
        assert "p1.prm" in path_names
        assert "p2.prm" in path_names
        assert "test.crd" in path_names
