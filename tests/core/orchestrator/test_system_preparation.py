# tests/core/orchestrator/test_system_preparation.py

from pathlib import Path
from unittest.mock import call, patch

from fastmdsimulation.core.orchestrator import _prepare_systems


class TestSystemPreparation:
    """Test system preparation logic."""

    @patch("fastmdsimulation.core.orchestrator.fix_pdb_with_pdbfixer")
    def test_prepare_systems_with_pdb_fixing(self, mock_fix_pdb, tmp_path):
        # Change to the test directory so file resolution works correctly
        original_cwd = Path.cwd()
        try:
            # Change to tmp_path so file resolution works correctly
            import os

            os.chdir(tmp_path)

            cfg = {
                "defaults": {"ph": 7.0},
                "systems": [
                    {"id": "test1", "pdb": "input1.pdb"},
                    {"id": "test2", "pdb": "input2.pdb", "ph": 8.0},
                ],
            }
            # Use tmp_path instead of hardcoded path
            base = tmp_path / "test"

            # Create the input files to avoid issues
            input1 = tmp_path / "input1.pdb"
            input2 = tmp_path / "input2.pdb"
            input1.write_text(
                "ATOM      1  N   ALA A   1       0.000   0.000   0.000  1.00  0.00           N\nEND"
            )
            input2.write_text(
                "ATOM      1  N   ALA A   1       0.000   0.000   0.000  1.00  0.00           N\nEND"
            )

            result = _prepare_systems(cfg, base)

            # Verify systems were processed
            assert len(result["systems"]) == 2
            assert result["systems"][0]["type"] == "pdb"
            assert result["systems"][1]["type"] == "pdb"

            # Verify PDBFixer was called with correct pH values
            assert mock_fix_pdb.call_count == 2

            # Get the actual calls made to see what paths were used
            actual_calls = mock_fix_pdb.call_args_list

            # Check that PDBFixer was called with the correct paths and pH values
            # The function should use the absolute paths within tmp_path
            expected_calls = [
                call(
                    str(input1.resolve()),
                    str((base / "_build/test1_fixed.pdb").resolve()),
                    ph=7.0,
                ),
                call(
                    str(input2.resolve()),
                    str((base / "_build/test2_fixed.pdb").resolve()),
                    ph=8.0,
                ),
            ]

            # Check each call matches our expected calls
            for expected_call in expected_calls:
                assert expected_call in actual_calls

        finally:
            # Always restore the original working directory
            os.chdir(original_cwd)

    def test_prepare_systems_with_fixed_pdb(self, tmp_path):
        # Change to the test directory so file resolution works correctly
        original_cwd = Path.cwd()
        try:
            # Change to tmp_path so file resolution works correctly
            import os

            os.chdir(tmp_path)

            cfg = {
                "systems": [
                    {"id": "test1", "fixed_pdb": "already_fixed.pdb"},
                ],
            }
            # Use tmp_path instead of hardcoded path
            base = tmp_path / "test"

            # Create the fixed pdb file
            fixed_pdb = tmp_path / "already_fixed.pdb"
            fixed_pdb.write_text(
                "ATOM      1  N   ALA A   1       0.000   0.000   0.000  1.00  0.00           N\nEND"
            )

            result = _prepare_systems(cfg, base)

            # Verify system was processed without fixing
            assert len(result["systems"]) == 1
            system = result["systems"][0]
            assert system["type"] == "pdb"
            # The function should use the resolved path within tmp_path
            assert system["pdb"] == str(fixed_pdb.resolve())

        finally:
            # Always restore the original working directory
            os.chdir(original_cwd)

    def test_prepare_systems_amber_passthrough(self, tmp_path):
        cfg = {
            "systems": [
                {"id": "amber1", "prmtop": "test.prmtop", "inpcrd": "test.inpcrd"},
            ],
        }
        # Use tmp_path instead of hardcoded path
        base = tmp_path / "test"

        # Create the amber files
        prmtop = tmp_path / "test.prmtop"
        inpcrd = tmp_path / "test.inpcrd"
        prmtop.write_text("AMBER topology")
        inpcrd.write_text("AMBER coordinates")

        result = _prepare_systems(cfg, base)

        # Verify AMBER system passed through unchanged
        assert len(result["systems"]) == 1
        system = result["systems"][0]
        assert system["type"] == "amber"
        assert system["prmtop"] == "test.prmtop"
