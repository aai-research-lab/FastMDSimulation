from fastmdsimulation.reporting.analysis_bridge import build_analyze_cmd


class TestBuildAnalyzeCmd:
    """Test the build_analyze_cmd function."""

    def test_build_analyze_cmd_basic(self, tmp_path):
        """Test building basic analysis command."""
        traj = tmp_path / "traj.dcd"
        top = tmp_path / "topology.pdb"

        cmd = build_analyze_cmd(traj, top, slides=True, frames=None, atoms=None)

        expected = [
            "fastmda",
            "analyze",
            "-traj",
            str(traj),
            "-top",
            str(top),
            "--slides",
        ]
        assert cmd == expected

    def test_build_analyze_cmd_no_slides(self, tmp_path):
        """Test building command without slides."""
        traj = tmp_path / "traj.dcd"
        top = tmp_path / "topology.pdb"

        cmd = build_analyze_cmd(traj, top, slides=False, frames=None, atoms=None)

        expected = ["fastmda", "analyze", "-traj", str(traj), "-top", str(top)]
        assert cmd == expected

    def test_build_analyze_cmd_with_frames(self, tmp_path):
        """Test building command with frames."""
        traj = tmp_path / "traj.dcd"
        top = tmp_path / "topology.pdb"

        cmd = build_analyze_cmd(traj, top, slides=True, frames="0,-1,10", atoms=None)

        expected = [
            "fastmda",
            "analyze",
            "-traj",
            str(traj),
            "-top",
            str(top),
            "--slides",
            "--frames",
            "0,-1,10",
        ]
        assert cmd == expected

    def test_build_analyze_cmd_with_atoms(self, tmp_path):
        """Test building command with atoms selection."""
        traj = tmp_path / "traj.dcd"
        top = tmp_path / "topology.pdb"

        cmd = build_analyze_cmd(traj, top, slides=True, frames=None, atoms="protein")

        expected = [
            "fastmda",
            "analyze",
            "-traj",
            str(traj),
            "-top",
            str(top),
            "--slides",
            "--atoms",
            "protein",
        ]
        assert cmd == expected

    def test_build_analyze_cmd_all_params(self, tmp_path):
        """Test building command with all parameters."""
        traj = tmp_path / "traj.dcd"
        top = tmp_path / "topology.pdb"

        cmd = build_analyze_cmd(traj, top, slides=False, frames="100", atoms="backbone")

        expected = [
            "fastmda",
            "analyze",
            "-traj",
            str(traj),
            "-top",
            str(top),
            "--frames",
            "100",
            "--atoms",
            "backbone",
        ]
        assert cmd == expected
