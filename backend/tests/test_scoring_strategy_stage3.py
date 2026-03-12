from app.services.parser import parse_query
from app.services.recommender import recommend


def test_time_slot_weight_night_snack_prioritizes_late_shop() -> None:
    slots = parse_query("夜宵想吃辣，清水河，预算40，和朋友一起")
    names = [item.name for item in recommend(slots, top_k=3)]
    assert names[0] == "深夜小串"


def test_scene_weight_for_solo_lunch() -> None:
    slots = parse_query("20以内，沙河，中午一个人，清淡点")
    top = recommend(slots, top_k=1)[0]
    assert top.name == "番茄牛腩粉"
    assert "适合一个人" in top.reason


def test_tie_break_by_budget_closeness_is_stable() -> None:
    slots = parse_query("预算30")
    names = [item.name for item in recommend(slots, top_k=3)]
    # Same-field candidates are ordered by budget closeness then lower price.
    assert names[:3] == ["韩式拌饭屋", "粤式烧腊饭", "川味小馆"]
