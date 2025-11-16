from unittest.mock import MagicMock, patch

from fastmdsimulation.reporting.analysis_bridge import analyze_with_bridge


class TestAnalyzeWithBridgeMultipleRuns:
    """Test the analyze_with_bridge function with multiple runs."""

    @patch("fastmdsimulation.reporting.analysis_bridge._run_and_stream")
    @patch("fastmdsimulation.reporting.analysis_bridge.importlib.util.find_spec")
    def test_analyze_with_bridge_multiple_runs(
        self, mock_find_spec, mock_run_and_stream, tmp_path
    ):
        """Test analysis with multiple runs."""
        # Setup multiple runs
        for run_name in ["run1", "run2"]:
            run_dir = tmp_path / run_name
            prod_dir = run_dir / "production"
            prod_dir.mkdir(parents=True)
            (prod_dir / "traj.dcd").write_text("trajectory")
            (prod_dir / "topology.pdb").write_text("topology")

        mock_find_spec.return_value = True
        mock_run_and_stream.return_value = 0

        logger = MagicMock()
        with patch(
            "fastmdsimulation.reporting.analysis_bridge.get_logger", return_value=logger
        ):
            result = analyze_with_bridge(str(tmp_path))

            assert result is True
            assert mock_run_and_stream.call_count == 2  # One for each run

    @patch("fastmdsimulation.reporting.analysis_bridge._run_and_stream")
    @patch("fastmdsimulation.reporting.analysis_bridge.importlib.util.find_spec")
    def test_analyze_with_bridge_mixed_runs(
        self, mock_find_spec, mock_run_and_stream, tmp_path
    ):
        """Test analysis with mix of successful and failed runs."""
        # Setup multiple runs
        for run_name in ["run_success", "run_fail"]:
            run_dir = tmp_path / run_name
            prod_dir = run_dir / "production"
            prod_dir.mkdir(parents=True)
            (prod_dir / "traj.dcd").write_text("trajectory")
            (prod_dir / "topology.pdb").write_text("topology")

        mock_find_spec.return_value = True
        # First run succeeds, second run fails both attempts
        mock_run_and_stream.side_effect = [0, 1, 1]

        logger = MagicMock()
        with patch(
            "fastmdsimulation.reporting.analysis_bridge.get_logger", return_value=logger
        ):
            result = analyze_with_bridge(str(tmp_path))

            assert result is True  # At least one succeeded
            assert (
                mock_run_and_stream.call_count == 3
            )  # 1 for first run, 2 for second run
