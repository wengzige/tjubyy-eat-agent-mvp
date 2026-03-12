import re
from app.models.schemas import ParsedSlots


def parse_query(query: str) -> ParsedSlots:
    """MVP 规则解析器，后续可替换为 LLM / 讯飞模型。"""
    text = query.strip()

    budget = None
    budget_match = re.search(r"(\d{1,3})\s*(以内|以下|元|块)?", text)
    if budget_match:
        budget = int(budget_match.group(1))

    location = None
    if "清水河" in text:
        location = "清水河"
    elif "沙河" in text:
        location = "沙河"

    scene = None
    if any(k in text for k in ["一个人", "单人", "自己吃"]):
        scene = "一个人"
    elif any(k in text for k in ["室友", "同学", "聚餐", "约饭", "朋友"]):
        scene = "同学聚餐"

    taste = None
    if "辣" in text:
        taste = "辣"
    elif any(k in text for k in ["清淡", "淡口", "不油"]):
        taste = "清淡"

    meal_time = None
    if any(k in text for k in ["早", "早餐"]):
        meal_time = "早餐"
    elif any(k in text for k in ["中午", "午餐"]):
        meal_time = "午餐"
    elif any(k in text for k in ["晚上", "晚餐"]):
        meal_time = "晚餐"
    elif "夜宵" in text:
        meal_time = "夜宵"

    return ParsedSlots(
        budget_max=budget,
        location=location,
        scene=scene,
        taste=taste,
        time=meal_time,
    )
