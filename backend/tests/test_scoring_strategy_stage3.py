from app.services.parser import parse_query
from app.services.recommender import recommend


def test_time_slot_weight_night_snack_prioritizes_late_shop() -> None:
    slots = parse_query("夜宵想吃辣，北洋园，预算40，和朋友一起")
    names = [item.name for item in recommend(slots, top_k=3)]
    assert names[0] == "北洋园深夜烧烤"


def test_scene_weight_for_solo_lunch() -> None:
    slots = parse_query("20以内，北洋园，中午一个人，清淡点")
    top = recommend(slots, top_k=1)[0]
    assert top.name == "北洋园番茄米线"
    assert "适合 一个人" in top.reason


def test_tie_break_by_budget_closeness_is_stable() -> None:
    slots = parse_query("预算29")
    names = [item.name for item in recommend(slots, top_k=3)]
    assert names[:3] == ["北洋园韩式拌饭", "梅园轻食沙拉", "北洋园麻辣香锅"]
