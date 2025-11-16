# tests/core/orchestrator/test_version_utils.py

from unittest.mock import patch

from fastmdsimulation.core.orchestrator import _collect_versions, _pkg_version


class TestPackageVersion:
    """Test package version collection."""

    @patch("fastmdsimulation.core.orchestrator.importlib_metadata")
    def test_pkg_version_success(self, mock_importlib):
        mock_importlib.version.return_value = "1.2.3"
        result = _pkg_version("test-package")
        assert result == "1.2.3"

    @patch("fastmdsimulation.core.orchestrator.importlib_metadata")
    def test_pkg_version_fallback(self, mock_importlib):
        mock_importlib.version.side_effect = Exception("Package not found")
        result = _pkg_version("nonexistent-package")
        assert result == "n/a"


class TestVersionCollection:
    """Test version collection functionality."""

    @patch("fastmdsimulation.core.orchestrator._pkg_version")
    @patch("fastmdsimulation.core.orchestrator.platform")
    def test_collect_versions(self, mock_platform, mock_pkg_version):
        # Mock platform info
        mock_platform.python_version.return_value = "3.9.0"
        mock_platform.platform.return_value = "Linux-5.4.0"

        # Mock package versions
        def pkg_version_side_effect(pkg_name):
            versions = {
                "fastmdsimulation": "0.1.0",
                "openmm": "8.0.0",
                "pdbfixer": "1.7",
                "openmmforcefields": "0.11.2",
            }
            return versions.get(pkg_name, "n/a")

        mock_pkg_version.side_effect = pkg_version_side_effect

        result = _collect_versions()

        assert result["fastmdsimulation"] == "0.1.0"
        assert result["python"] == "3.9.0"
        assert result["os"] == "Linux-5.4.0"
        assert result["openmm"] == "8.0.0"
        assert result["pdbfixer"] == "1.7"
        assert result["openmmforcefields"] == "0.11.2"
