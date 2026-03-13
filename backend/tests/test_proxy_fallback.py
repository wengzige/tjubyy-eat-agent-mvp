from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_proxy_recommend_passthrough_when_structured_json(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.api.proxy_routes.generate_recommendation_response",
        lambda **kwargs: {
            "ok": True,
            "answer": '{"query":"test","summary":"s","batch_size":3,"total_count":1,"recommendations":[{"name":"A","score":92,"reason":"r","recommend_dish":"d","scene_fit":"晚餐","warning":"w"}]}',
            "finishReason": "stop",
            "raw": {"provider": "tencent-hunyuan"},
        },
    )

    resp = client.post(
        "/api/recommend",
        json={
            "query": "北洋园附近，预算25，一个人，想吃清淡一点",
            "uid": "test-user",
            "history": [],
        },
    )

    assert resp.status_code == 200
    body = resp.json()
    assert body["ok"] is True
    assert body["finishReason"] == "stop"
    assert body["raw"]["provider"] == "tencent-hunyuan"


def test_proxy_recommend_falls_back_to_local_when_model_unavailable(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.api.proxy_routes.generate_recommendation_response",
        lambda **kwargs: {
            "ok": True,
            "answer": '{"query":"北洋园晚饭","summary":"结合预算和位置给你筛了 3 个备选。","batch_size":3,"total_count":3,"recommendations":[{"name":"北洋园麻辣香锅","score":93,"reason":"预算内且口味匹配。","recommend_dish":"麻辣香锅","scene_fit":"同学聚餐 / 北洋园·学五生活区","warning":"饭点可能排队"}]}',
            "finishReason": "fallback",
            "raw": {"provider": "local-rule-fallback", "fallback": True},
        },
    )

    resp = client.post(
        "/api/recommend",
        json={
            "query": "北洋园附近，预算25，一个人，想吃清淡一点",
            "uid": "test-user",
            "history": [],
        },
    )

    assert resp.status_code == 200
    body = resp.json()
    assert body["ok"] is True
    assert body["finishReason"] == "fallback"
    assert body["raw"]["provider"] == "local-rule-fallback"
    assert body["raw"]["fallback"] is True
