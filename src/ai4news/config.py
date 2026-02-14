# src/ai4news/config.py
from pathlib import Path

import yaml

VALID_TARGET_TYPES = {"person", "company", "hashtag"}


def get_project_root() -> Path:
    return Path(__file__).parent.parent.parent


def get_data_dir() -> Path:
    data_dir = get_project_root() / "data"
    data_dir.mkdir(exist_ok=True)
    return data_dir


def get_config_dir() -> Path:
    return get_project_root() / "config"


def get_targets_path() -> Path:
    return get_config_dir() / "targets.yaml"


def load_targets(path: Path | None = None) -> list[dict]:
    if path is None:
        path = get_targets_path()
    with open(path) as f:
        data = yaml.safe_load(f)
    targets = data.get("targets") or []
    for t in targets:
        if t.get("type") not in VALID_TARGET_TYPES:
            raise ValueError(
                f"Invalid target type: {t.get('type')}. "
                f"Must be one of: {VALID_TARGET_TYPES}"
            )
    return targets


def save_targets(targets: list[dict], path: Path | None = None) -> None:
    if path is None:
        path = get_targets_path()
    with open(path, "w") as f:
        yaml.dump({"targets": targets}, f, default_flow_style=False)
