import sys
from unittest.mock import MagicMock, patch

from fastmdsimulation.reporting.analysis_bridge import analyze_with_bridge


class TestAnalyzeWithBridge:
    """Test the analyze_with_bridge function."""

    def test_analyze_with_bridge_project_not_found(self, tmp_path):
        """Test when project directory doesn't exist."""
        logger = MagicMock()
        with patch(
            "fastmdsimulation.reporting.analysis_bridge.get_logger", return_value=logger
        ):
            result = analyze_with_bridge(str(tmp_path / "nonexistent"))

            assert result is False
            logger.error.assert_called_once()

    def test_analyze_with_bridge_fastmda_not_installed(self, tmp_path):
        """Test when FastMDAnalysis is not installed."""
        logger = MagicMock()
        with (
            patch(
                "fastmdsimulation.reporting.analysis_bridge.get_logger",
                return_value=logger,
            ),
            patch(
                "fastmdsimulation.reporting.analysis_bridge.importlib.util.find_spec",
                return_value=None,
            ),
        ):

            result = analyze_with_bridge(str(tmp_path))

            assert result is False
            logger.warning.assert_called_once_with(
                "FastMDAnalysis not installed. Install it or omit --analyze."
            )

    @patch("fastmdsimulation.reporting.analysis_bridge._run_and_stream")
    @patch("fastmdsimulation.reporting.analysis_bridge.importlib.util.find_spec")
    def test_analyze_with_bridge_success(
        self, mock_find_spec, mock_run_and_stream, tmp_path
    ):
        """Test successful analysis with primary command."""
        # Setup project structure
        run_dir = tmp_path / "run1"
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
            result = analyze_with_bridge(
                str(tmp_path), slides=True, frames="0,-1,10", atoms="protein"
            )

            assert result is True
            mock_run_and_stream.assert_called_once()
            logger.info.assert_any_call(
                "run analysis: fastmda analyze -traj "
                + str(prod_dir / "traj.dcd")
                + " -top "
                + str(prod_dir / "topology.pdb")
                + " --slides --frames 0,-1,10 --atoms protein"
            )

    @patch("fastmdsimulation.reporting.analysis_bridge._run_and_stream")
    @patch("fastmdsimulation.reporting.analysis_bridge.importlib.util.find_spec")
    def test_analyze_with_bridge_fallback_success(
        self, mock_find_spec, mock_run_and_stream, tmp_path
    ):
        """Test successful analysis with fallback command."""
        # Setup project structure
        run_dir = tmp_path / "run1"
        prod_dir = run_dir / "production"
        prod_dir.mkdir(parents=True)
        (prod_dir / "traj.dcd").write_text("trajectory")
        (prod_dir / "topology.pdb").write_text("topology")

        mock_find_spec.return_value = True
        # First call fails, second call (fallback) succeeds
        mock_run_and_stream.side_effect = [1, 0]

        logger = MagicMock()
        with patch(
            "fastmdsimulation.reporting.analysis_bridge.get_logger", return_value=logger
        ):
            result = analyze_with_bridge(str(tmp_path))

            assert result is True
            assert mock_run_and_stream.call_count == 2
            # Verify fallback command was used
            second_call = mock_run_and_stream.call_args_list[1]
            cmd = second_call[0][0]
            assert cmd[0] == sys.executable
            assert cmd[1] == "-m"
            assert cmd[2] == "fastmdanalysis"

    @patch("fastmdsimulation.reporting.analysis_bridge._run_and_stream")
    @patch("fastmdsimulation.reporting.analysis_bridge.importlib.util.find_spec")
    def test_analyze_with_bridge_all_fail(
        self, mock_find_spec, mock_run_and_stream, tmp_path
    ):
        """Test when both primary and fallback commands fail."""
        # Setup project structure
        run_dir = tmp_path / "run1"
        prod_dir = run_dir / "production"
        prod_dir.mkdir(parents=True)
        (prod_dir / "traj.dcd").write_text("trajectory")
        (prod_dir / "topology.pdb").write_text("topology")

        mock_find_spec.return_value = True
        mock_run_and_stream.side_effect = [1, 1]  # Both fail

        logger = MagicMock()
        with patch(
            "fastmdsimulation.reporting.analysis_bridge.get_logger", return_value=logger
        ):
            result = analyze_with_bridge(str(tmp_path))

            assert result is False
            logger.error.assert_called_once()

    @patch("fastmdsimulation.reporting.analysis_bridge._run_and_stream")
    @patch("fastmdsimulation.reporting.analysis_bridge.importlib.util.find_spec")
    def test_analyze_with_bridge_no_production(
        self, mock_find_spec, mock_run_and_stream, tmp_path
    ):
        """Test when no production stages are found."""
        # Create project directory but no production data
        (tmp_path / "run1").mkdir()

        mock_find_spec.return_value = True

        logger = MagicMock()
        with patch(
            "fastmdsimulation.reporting.analysis_bridge.get_logger", return_value=logger
        ):
            result = analyze_with_bridge(str(tmp_path))

            assert result is False
            logger.warning.assert_called_once_with(
                "no production stages found or analysis failed; skipping analysis."
            )
            mock_run_and_stream.assert_not_called()
