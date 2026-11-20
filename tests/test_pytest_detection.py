"""Test-runner detection for Python projects with nested tests."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import bite  # noqa: E402


@pytest.mark.parametrize("windows", [False, True])
@pytest.mark.parametrize("filename, contents, test_name", [
    ("pyproject.toml", '[tool.pytest.ini_options]\ntestpaths = ["tests"]\n', "test_api.py"),
    ("setup.cfg", '[tool:pytest]\ntestpaths = tests\n', "test_api.py"),
    ("pyproject.toml", '\ufeff[tool.pytest.ini_options] # tests\npython_files = ["*_test.py"]\n', "api_test.py"),
    ("setup.cfg", '  [tool:pytest] ; tests\npython_files = *_test.py\n', "api_test.py"),
])
def test_guesses_pytest_from_config(tmp_path, monkeypatch, windows, filename, contents, test_name):
    (tmp_path / filename).write_text(contents, encoding="utf-8")
    nested = tmp_path / "tests" / "unit"
    nested.mkdir(parents=True)
    (nested / test_name).write_text("def test_api(): pass\n", encoding="utf-8")
    monkeypatch.setattr(bite, "WINDOWS", windows)
    assert bite.guess_test_command(tmp_path) == ("python" if windows else "python3") + " -m pytest -q"


@pytest.mark.parametrize("filename, contents", [
    ("pyproject.toml", '# [tool.pytest.ini_options]\n[project]\nname = "demo"\n'),
    ("pyproject.toml", '[tool.pytest.ini_options.extra]\n'),
    ("setup.cfg", '; [tool:pytest]\n[metadata]\nname = demo\n'),
    ("setup.cfg", '[tool:pytest_extra]\n'),
])
def test_does_not_guess_pytest_from_unrelated_config(tmp_path, filename, contents):
    (tmp_path / filename).write_text(contents, encoding="utf-8")
    assert bite.guess_test_command(tmp_path) == ""


def test_unreadable_config_does_not_stop_detection(tmp_path):
    (tmp_path / "pyproject.toml").write_bytes(b"\xff")
    (tmp_path / "setup.cfg").write_text("[tool:pytest]\n", encoding="utf-8")
    assert bite.guess_test_command(tmp_path).endswith(" -m pytest -q")


def test_npm_still_has_priority(tmp_path):
    (tmp_path / "package.json").write_text('{"scripts":{"test":"jest"}}', encoding="utf-8")
    (tmp_path / "pyproject.toml").write_text("[tool.pytest.ini_options]\n", encoding="utf-8")
    assert bite.guess_test_command(tmp_path) == "npm test"
