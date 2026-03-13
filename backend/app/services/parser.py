import re

from app.core.campus_config import CAMPUS_PROFILE
from app.models.schemas import ParsedSlots


LOCATION_RULES = {location: aliases for location, aliases in CAMPUS_PROFILE.location_aliases.items()}

SCENE_RULES = {
    "一个人": ("一个人", "一人食", "单人", "自己吃", "赶时间"),
    "同学聚餐": ("室友", "同学", "聚餐", "约饭", "朋友", "多人"),
}

TASTE_RULES = {
    "辣": ("辣", "重口", "麻辣", "香辣"),
    "清淡": ("清淡", "淡口", "不油", "不辣", "少辣"),
}

TIME_RULES = {
    "早餐": ("早餐", "早饭", "早上"),
    "午餐": ("午餐", "午饭", "中午"),
    "晚餐": ("晚餐", "晚饭", "晚上"),
    "夜宵": ("夜宵", "宵夜", "深夜"),
}


def _match_rule(text: str, rules: dict[str, tuple[str, ...]]) -> str | None:
    for result, keywords in rules.items():
        if any(keyword in text for keyword in keywords):
            return result
    return None


def parse_query(query: str) -> ParsedSlots:
    """MVP 规则解析器，后续可替换为更复杂的 LLM 或混合检索。"""
    text = query.strip()

    budget = None
    budget_match = re.search(r"(?:预算|人均|¥|￥)\s*(\d{1,3})", text)
    if not budget_match:
        budget_match = re.search(r"(\d{1,3})\s*(?:元|块|以内|以下|左右|上下)", text)
    if budget_match:
        budget = int(budget_match.group(1))

    return ParsedSlots(
        budget_max=budget,
        location=_match_rule(text, LOCATION_RULES),
        scene=_match_rule(text, SCENE_RULES),
        taste=_match_rule(text, TASTE_RULES),
        time=_match_rule(text, TIME_RULES),
    )
