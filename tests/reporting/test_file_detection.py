from fastmdsimulation.reporting.analysis_bridge import (
    _get_production_stage,
    iter_runs_with_production,
)


class TestGetProductionStage:
    """Test the _get_production_stage function."""

    def test_get_production_stage_success(self, tmp_path):
        """Test when production stage exists with required files."""
        run_dir = tmp_path / "run1"
        prod_dir = run_dir / "production"
        prod_dir.mkdir(parents=True)
        (prod_dir / "traj.dcd").write_text("trajectory data")
        (prod_dir / "topology.pdb").write_text("topology data")

        result = _get_production_stage(run_dir)

        assert result == prod_dir

    def test_get_production_stage_no_directory(self, tmp_path):
        """Test when production directory doesn't exist."""
        run_dir = tmp_path / "run1"

        result = _get_production_stage(run_dir)

        assert result is None

    def test_get_production_stage_missing_traj(self, tmp_path):
        """Test when trajectory file is missing."""
        run_dir = tmp_path / "run1"
        prod_dir = run_dir / "production"
        prod_dir.mkdir(parents=True)
        (prod_dir / "topology.pdb").write_text("topology data")
        # Missing traj.dcd

        result = _get_production_stage(run_dir)

        assert result is None

    def test_get_production_stage_missing_topology(self, tmp_path):
        """Test when topology file is missing."""
        run_dir = tmp_path / "run1"
        prod_dir = run_dir / "production"
        prod_dir.mkdir(parents=True)
        (prod_dir / "traj.dcd").write_text("trajectory data")
        # Missing topology.pdb

        result = _get_production_stage(run_dir)

        assert result is None


class TestIterRunsWithProduction:
    """Test the iter_runs_with_production function."""

    def test_iter_runs_with_production_success(self, tmp_path):
        """Test iteration over runs with production data."""
        # Create multiple runs with production data
        for run_name in ["run1", "run2", "run3"]:
            run_dir = tmp_path / run_name
            prod_dir = run_dir / "production"
            prod_dir.mkdir(parents=True)
            (prod_dir / "traj.dcd").write_text("trajectory")
            (prod_dir / "topology.pdb").write_text("topology")

        # Create a run without production data
        (tmp_path / "run_no_prod").mkdir()

        results = list(iter_runs_with_production(tmp_path))

        assert len(results) == 3
        # Check that results are sorted by run name
        run_names = [run_dir.name for run_dir, _, _, _ in results]
        assert run_names == ["run1", "run2", "run3"]

        # Verify each result has correct structure
        for run_dir, prod_dir, traj, top in results:
            assert run_dir.name in ["run1", "run2", "run3"]
            assert prod_dir == run_dir / "production"
            assert traj == prod_dir / "traj.dcd"
            assert top == prod_dir / "topology.pdb"

    def test_iter_runs_with_production_no_runs(self, tmp_path):
        """Test when no runs exist."""
        results = list(iter_runs_with_production(tmp_path))

        assert len(results) == 0

    def test_iter_runs_with_production_only_invalid(self, tmp_path):
        """Test when only invalid runs exist."""
        # Create runs without production data
        for run_name in ["run1", "run2"]:
            run_dir = tmp_path / run_name
            run_dir.mkdir()
            # No production directory

        results = list(iter_runs_with_production(tmp_path))

        assert len(results) == 0

    def test_iter_runs_with_production_mixed(self, tmp_path):
        """Test with mix of valid and invalid runs."""
        # Valid run
        valid_run = tmp_path / "valid_run"
        prod_dir = valid_run / "production"
        prod_dir.mkdir(parents=True)
        (prod_dir / "traj.dcd").write_text("trajectory")
        (prod_dir / "topology.pdb").write_text("topology")

        # Invalid run - missing files
        invalid_run = tmp_path / "invalid_run"
        (invalid_run / "production").mkdir(parents=True)

        results = list(iter_runs_with_production(tmp_path))

        assert len(results) == 1
        run_dir, prod_dir, traj, top = results[0]
        assert run_dir.name == "valid_run"
