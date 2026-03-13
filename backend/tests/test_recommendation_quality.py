from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_case_spicy_group_dinner_beiyangyuan() -> None:
    payload = {"query": "预算30，北洋园，晚上和同学想吃辣的", "top_k": 3}
    resp = client.post("/api/v1/recommend", json=payload)
    data = resp.json()

    assert resp.status_code == 200
    assert data["parsed"]["location"] == "北洋园"
    assert data["parsed"]["taste"] == "辣"
    assert data["parsed"]["scene"] == "同学聚餐"
    assert data["recommendations"][0]["name"] == "北洋园麻辣香锅"


def test_case_light_solo_lunch_beiyangyuan() -> None:
    payload = {"query": "20以内，北洋园，中午一个人，清淡点", "top_k": 3}
    resp = client.post("/api/v1/recommend", json=payload)
    data = resp.json()

    assert resp.status_code == 200
    assert data["parsed"]["location"] == "北洋园"
    assert data["parsed"]["scene"] == "一个人"
    assert data["recommendations"][0]["name"] == "北洋园番茄米线"


def test_case_night_snack_beiyangyuan() -> None:
    payload = {"query": "夜宵想吃辣，北洋园，预算40，和朋友一起", "top_k": 3}
    resp = client.post("/api/v1/recommend", json=payload)
    data = resp.json()
    names = [item["name"] for item in data["recommendations"]]

    assert resp.status_code == 200
    assert data["parsed"]["time"] == "夜宵"
    assert "北洋园深夜烧烤" in names
