import os
import tempfile
from unittest.mock import patch

from fastmdsimulation.cli import (
    _deep_update,
    _detect_log_style,
    _env_log_style,
    _normalize_style,
    _read_log_style_from_yaml,
)


class TestDeepUpdate:
    def test_deep_update_basic(self):
        dst = {"a": 1, "b": {"c": 2}}
        src = {"b": {"d": 3}, "e": 4}
        result = _deep_update(dst, src)
        assert result == {"a": 1, "b": {"c": 2, "d": 3}, "e": 4}

    def test_deep_update_overwrite(self):
        dst = {"a": 1, "b": {"c": 2}}
        src = {"a": 10, "b": {"c": 20}}
        result = _deep_update(dst, src)
        assert result == {"a": 10, "b": {"c": 20}}

    def test_deep_update_empty_src(self):
        dst = {"a": 1}
        src = {}
        result = _deep_update(dst, src)
        assert result == {"a": 1}

    def test_deep_update_none_src(self):
        dst = {"a": 1}
        result = _deep_update(dst, None)
        assert result == {"a": 1}


class TestNormalizeStyle:
    def test_normalize_style_pretty(self):
        assert _normalize_style("pretty") == "pretty"
        assert _normalize_style("PRETTY") == "pretty"
        assert _normalize_style(" Pretty ") == "pretty"

    def test_normalize_style_plain(self):
        assert _normalize_style("plain") == "plain"
        assert _normalize_style("PLAIN") == "plain"

    def test_normalize_style_invalid(self):
        assert _normalize_style("invalid") is None
        assert _normalize_style("") is None
        assert _normalize_style(None) is None


class TestReadLogStyleFromYaml:
    def test_read_log_style_valid(self):
        yaml_content = """
        defaults:
          log_style: pretty
        """
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_content)
            temp_path = f.name

        try:
            result = _read_log_style_from_yaml(temp_path)
            assert result == "pretty"
        finally:
            os.unlink(temp_path)

    def test_read_log_style_no_defaults(self):
        yaml_content = """
        systems:
          - id: test
        """
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_content)
            temp_path = f.name

        try:
            result = _read_log_style_from_yaml(temp_path)
            assert result is None
        finally:
            os.unlink(temp_path)

    def test_read_log_style_no_log_style(self):
        yaml_content = """
        defaults:
          temperature: 300
        """
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_content)
            temp_path = f.name

        try:
            result = _read_log_style_from_yaml(temp_path)
            assert result is None
        finally:
            os.unlink(temp_path)

    def test_read_log_style_file_not_found(self):
        result = _read_log_style_from_yaml("/nonexistent/file.yaml")
        assert result is None

    def test_read_log_style_invalid_yaml(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("invalid: yaml: content:")
            temp_path = f.name

        try:
            result = _read_log_style_from_yaml(temp_path)
            assert result is None
        finally:
            os.unlink(temp_path)


class TestEnvLogStyle:
    @patch.dict(os.environ, {"FASTMDS_LOG_STYLE": "plain"})
    def test_env_log_style_set(self):
        assert _env_log_style() == "plain"

    @patch.dict(os.environ, {"FASTMDS_LOG_STYLE": "PRETTY"})
    def test_env_log_style_uppercase(self):
        assert _env_log_style() == "pretty"

    @patch.dict(os.environ, {"FASTMDS_LOG_STYLE": "invalid"})
    def test_env_log_style_invalid(self):
        assert _env_log_style() is None

    @patch.dict(os.environ, {}, clear=True)
    def test_env_log_style_unset(self):
        assert _env_log_style() is None


class TestDetectLogStyle:
    def test_detect_log_style_yaml_file(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(
                """
            defaults:
              log_style: plain
            """
            )
            temp_path = f.name

        try:
            result = _detect_log_style(temp_path, None)
            assert result == "plain"
        finally:
            os.unlink(temp_path)

    def test_detect_log_style_pdb_with_config(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(
                """
            defaults:
              log_style: plain
            """
            )
            config_path = f.name

        try:
            result = _detect_log_style("test.pdb", config_path)
            assert result == "plain"
        finally:
            os.unlink(config_path)

    @patch.dict(os.environ, {"FASTMDS_LOG_STYLE": "plain"})
    def test_detect_log_style_from_env(self):
        result = _detect_log_style("test.pdb", None)
        assert result == "plain"

    def test_detect_log_style_fallback(self):
        result = _detect_log_style("test.pdb", None)
        assert result == "pretty"

    def test_detect_log_style_yaml_no_style(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(
                """
            systems:
              - id: test
            """
            )
            temp_path = f.name

        try:
            result = _detect_log_style(temp_path, None)
            assert result == "pretty"
        finally:
            os.unlink(temp_path)
