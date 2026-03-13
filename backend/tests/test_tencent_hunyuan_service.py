import json

from app.services.tencent_hunyuan_service import (
    generate_recommendation_response,
    validate_and_map_history,
)


def test_history_validation_first_message_must_be_user() -> None:
    mapped, err = validate_and_map_history(
        [
            {"role": "assistant", "content": "hello"},
            {"role": "user", "content": "hi"},
        ]
    )
    assert mapped is None
    assert err == "history 第一条必须是 user。"


def test_generate_recommendation_response_falls_back_when_secret_missing(monkeypatch) -> None:
    monkeypatch.delenv("TENCENT_SECRET_ID", raising=False)
    monkeypatch.delenv("TENCENT_SECRET_KEY", raising=False)

    result = generate_recommendation_response(query="预算30，北洋园，晚上和同学想吃辣的")

    assert result["ok"] is True
    assert result["finishReason"] == "fallback"
    assert result["raw"]["provider"] == "local-rule-fallback"
    payload = json.loads(result["answer"])
    assert payload["recommendations"]


def test_generate_recommendation_response_normalizes_model_json(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.services.tencent_hunyuan_service.ask_tencent_hunyuan",
        lambda **kwargs: {
            "ok": True,
            "answer": "```json\n{\"query\":\"q\",\"summary\":\"s\",\"batch_size\":3,\"total_count\":1,\"recommendations\":[{\"name\":\"北洋园牛肉面\",\"score\":90,\"reason\":\"r\",\"recommend_dish\":\"牛肉面\",\"scene_fit\":\"一个人\",\"warning\":\"饭点排队\"}]}\n```",
            "finishReason": "stop",
            "raw": {"provider": "tencent-hunyuan"},
        },
    )

    result = generate_recommendation_response(query="预算20，北洋园，一个人吃面")

    assert result["ok"] is True
    assert result["finishReason"] == "stop"
    assert result["answer"].startswith("{")
    payload = json.loads(result["answer"])
    assert payload["recommendations"][0]["name"] == "北洋园牛肉面"
