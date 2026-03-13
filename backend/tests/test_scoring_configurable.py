import json

from app.core.scoring_config import load_scoring_config
from app.services.parser import parse_query
from app.services.recommender import recommend


def test_can_load_yaml_config_from_env(monkeypatch, tmp_path) -> None:
    cfg = tmp_path / "scoring.yaml"
    cfg.write_text(
        "weights:\n"
        "  scene: 0.5\n"
        "reason_thresholds:\n"
        "  time_match_min: 0.8\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("SCORING_CONFIG_PATH", str(cfg))

    loaded = load_scoring_config()
    assert loaded["weights"]["scene"] == 0.5
    assert loaded["reason_thresholds"]["time_match_min"] == 0.8


def test_can_load_json_config_and_affect_ranking(monkeypatch, tmp_path) -> None:
    cfg = tmp_path / "scoring.json"
    cfg.write_text(
        json.dumps(
            {
                "weights": {
                    "base_score": 0.0,
                    "budget": 1.0,
                    "location": 0.0,
                    "taste": 0.0,
                    "scene": 0.0,
                    "time": 0.0,
                    "budget_bonus": 0.0,
                }
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("SCORING_CONFIG_PATH", str(cfg))

    slots = parse_query("晚饭想吃辣，北洋园，预算24，和朋友一起")
    top = recommend(slots, top_k=1)[0]
    assert top.name == "北洋园麻辣香锅"
