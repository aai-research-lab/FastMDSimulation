import subprocess
from unittest.mock import MagicMock, call, patch

from fastmdsimulation.reporting.analysis_bridge import _run_and_stream


class TestRunAndStream:
    """Test the _run_and_stream function."""

    @patch("fastmdsimulation.reporting.analysis_bridge.subprocess.Popen")
    def test_run_and_stream_success(self, mock_popen):
        """Test successful subprocess execution with streaming output."""
        mock_process = MagicMock()
        mock_process.stdout = MagicMock()
        mock_process.stdout.__enter__ = MagicMock(return_value=mock_process.stdout)
        mock_process.stdout.__exit__ = MagicMock(return_value=None)
        mock_process.stdout.__iter__ = MagicMock(
            return_value=iter(["line 1\n", "line 2\n"])
        )
        mock_process.wait.return_value = 0
        mock_popen.return_value = mock_process

        logger = MagicMock()
        cmd = ["echo", "test"]

        result = _run_and_stream(cmd, logger, prefix="[test] ")

        assert result == 0
        mock_popen.assert_called_once_with(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True,
        )
        logger.info.assert_has_calls([call("[test] line 1"), call("[test] line 2")])

    @patch("fastmdsimulation.reporting.analysis_bridge.subprocess.Popen")
    def test_run_and_stream_process_failure(self, mock_popen):
        """Test subprocess execution that returns non-zero exit code."""
        mock_process = MagicMock()
        mock_process.stdout = MagicMock()
        mock_process.stdout.__enter__ = MagicMock(return_value=mock_process.stdout)
        mock_process.stdout.__exit__ = MagicMock(return_value=None)
        mock_process.stdout.__iter__ = MagicMock(return_value=iter(["error line\n"]))
        mock_process.wait.return_value = 1
        mock_popen.return_value = mock_process

        logger = MagicMock()
        cmd = ["false"]

        result = _run_and_stream(cmd, logger)

        assert result == 1
        logger.info.assert_called_once_with("[fastmda] error line")

    @patch("fastmdsimulation.reporting.analysis_bridge.subprocess.Popen")
    def test_run_and_stream_start_failure(self, mock_popen):
        """Test when subprocess fails to start."""
        mock_popen.side_effect = Exception("Command not found")

        logger = MagicMock()
        cmd = ["nonexistent_command"]

        result = _run_and_stream(cmd, logger)

        assert result == 127
        logger.error.assert_called_once_with(
            "[fastmda] failed to start process: Command not found"
        )

    @patch("fastmdsimulation.reporting.analysis_bridge.subprocess.Popen")
    def test_run_and_stream_empty_output(self, mock_popen):
        """Test subprocess execution with no output."""
        mock_process = MagicMock()
        mock_process.stdout = MagicMock()
        mock_process.stdout.__enter__ = MagicMock(return_value=mock_process.stdout)
        mock_process.stdout.__exit__ = MagicMock(return_value=None)
        mock_process.stdout.__iter__ = MagicMock(return_value=iter([]))
        mock_process.wait.return_value = 0
        mock_popen.return_value = mock_process

        logger = MagicMock()
        cmd = ["true"]

        result = _run_and_stream(cmd, logger)

        assert result == 0
        logger.info.assert_not_called()
