# tests/test_config.py
import tempfile
from pathlib import Path

from ai4news.config import load_targets, get_project_root, get_data_dir


def test_get_project_root():
    root = get_project_root()
    assert (root / "pyproject.toml").exists()


def test_get_data_dir():
    data_dir = get_data_dir()
    assert data_dir.name == "data"


def test_load_targets_empty():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write("targets: []\n")
        f.flush()
        targets = load_targets(Path(f.name))
    assert targets == []


def test_load_targets_with_entries():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write(
            "targets:\n"
            "  - type: person\n"
            "    name: Test User\n"
            "    url: https://www.linkedin.com/in/testuser\n"
        )
        f.flush()
        targets = load_targets(Path(f.name))
    assert len(targets) == 1
    assert targets[0]["type"] == "person"
    assert targets[0]["name"] == "Test User"
    assert targets[0]["url"] == "https://www.linkedin.com/in/testuser"


def test_load_targets_validates_type():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write(
            "targets:\n"
            "  - type: invalid\n"
            "    name: Bad\n"
            "    url: https://www.linkedin.com/in/bad\n"
        )
        f.flush()
        try:
            load_targets(Path(f.name))
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "invalid" in str(e).lower()
