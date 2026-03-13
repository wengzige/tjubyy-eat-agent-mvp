import copy
import json
import os
from pathlib import Path
from typing import Any, Dict

import yaml


BASE_DIR = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG_PATH = BASE_DIR / "data" / "scoring_config.yaml"

DEFAULT_SCORING_CONFIG: Dict[str, Any] = {
    "weights": {
        "base_score": 0.15,
        "budget": 0.22,
        "location": 0.18,
        "taste": 0.18,
        "scene": 0.22,
        "time": 0.20,
        "budget_bonus": 0.03,
    },
    "reason_thresholds": {
        "time_match_min": 0.5,
    },
    "time_slot_ranges": {
        "早餐": ["06:00", "10:00"],
        "午餐": ["11:00", "14:00"],
        "晚餐": ["17:00", "21:00"],
        "夜宵": ["21:00", "26:00"],
    },
    "scene_aliases": {
        "一个人": ["一个人", "一人食", "单人", "赶时间", "自习后", "健身餐"],
        "同学聚餐": ["同学聚餐", "聚餐", "约饭", "朋友聚会", "多人", "室友"],
    },
}


def _deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    merged = copy.deepcopy(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def _load_yaml(path: Path) -> Dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if data is None:
        return {}
    if not isinstance(data, dict):
        raise ValueError(f"Invalid YAML config format: {path}")
    return data


def _load_json(path: Path) -> Dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"Invalid JSON config format: {path}")
    return data


def load_scoring_config() -> Dict[str, Any]:
    configured = os.getenv("SCORING_CONFIG_PATH", "").strip()
    path = Path(configured) if configured else DEFAULT_CONFIG_PATH

    if not path.exists():
        return copy.deepcopy(DEFAULT_SCORING_CONFIG)

    suffix = path.suffix.lower()
    if suffix in {".yaml", ".yml"}:
        override = _load_yaml(path)
    elif suffix == ".json":
        override = _load_json(path)
    else:
        raise ValueError(f"Unsupported scoring config extension: {path.suffix}")

    return _deep_merge(DEFAULT_SCORING_CONFIG, override)
