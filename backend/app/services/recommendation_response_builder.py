from __future__ import annotations

import json
from typing import Iterable

from app.models.schemas import ParsedSlots, ShopResult


CARD_LABELS = ("店名", "推荐理由", "推荐菜", "适合场景", "可能不足")


def is_card_friendly_answer(answer: str | None) -> bool:
    text = (answer or "").strip()
    if not text:
        return False

    matched_labels = sum(1 for label in CARD_LABELS if f"{label}：" in text or f"{label}:" in text)
    return matched_labels >= 3


def is_structured_json_answer(answer: str | None) -> bool:
    text = (answer or "").strip()
    if not text:
        return False

    candidate = _extract_json_candidate(text)
    if not candidate:
        return False

    try:
        parsed = json.loads(candidate)
    except (TypeError, ValueError, json.JSONDecodeError):
        return False

    if not isinstance(parsed, dict):
        return False

    recommendations = parsed.get("recommendations")
    if not isinstance(recommendations, list):
        return False

    expected_keys = {"name", "score", "reason", "recommend_dish", "scene_fit", "warning"}
    for item in recommendations:
        if isinstance(item, dict) and expected_keys.intersection(item.keys()):
            return True
    return False


def _extract_json_candidate(text: str) -> str | None:
    if text.startswith("{") and text.endswith("}"):
        return text

    if "```" in text:
        start = text.find("{")
        end = text.rfind("}")
        if start >= 0 and end > start:
            return text[start : end + 1]

    first = text.find("{")
    last = text.rfind("}")
    if first >= 0 and last > first:
        return text[first : last + 1]
    return None


def build_rule_based_answer(slots: ParsedSlots, items: Iterable[ShopResult]) -> str:
    recommendations = list(items)
    if not recommendations:
        return "暂时没有找到合适的推荐，你可以放宽预算、位置或口味条件后再试一次。"

    blocks: list[str] = []
    for index, item in enumerate(recommendations, start=1):
        blocks.append(
            "\n".join(
                [
                    f"{index}. {item.name}",
                    f"店名：{item.name}",
                    f"推荐理由：{item.reason}",
                    f"推荐菜：{_build_dishes_hint(item)}",
                    f"适合场景：{_build_scene_hint(slots, item)}",
                    f"可能不足：{_build_downside_hint(slots, item)}",
                ]
            )
        )

    prefix = _build_summary(slots)
    return f"{prefix}\n\n" + "\n\n".join(blocks)


def _build_summary(slots: ParsedSlots) -> str:
    conditions: list[str] = []
    if slots.location:
        conditions.append(slots.location)
    if slots.budget_max is not None:
        conditions.append(f"预算 {slots.budget_max} 元内")
    if slots.scene:
        conditions.append(slots.scene)
    if slots.taste:
        conditions.append(f"偏好{slots.taste}")
    if slots.time:
        conditions.append(slots.time)

    if not conditions:
        return "结合当前校园餐饮数据，先给你 3 个综合匹配度较高的选择："
    return f"根据你的条件（{' / '.join(conditions)}），给你 3 个优先推荐："


def _build_dishes_hint(item: ShopResult) -> str:
    interesting_tags = [tag for tag in item.tags if tag and tag not in {item.campus}]
    if interesting_tags:
        return "可优先关注：" + "、".join(interesting_tags[:3])
    return "建议到店先看招牌和热销菜。"


def _build_scene_hint(slots: ParsedSlots, item: ShopResult) -> str:
    if slots.scene:
        return f"适合 {slots.scene}，也适合日常校园就餐。"
    if slots.time:
        return f"适合 {slots.time} 时段就餐。"
    return f"适合在 {item.campus} 校区日常吃饭。"


def _build_downside_hint(slots: ParsedSlots, item: ShopResult) -> str:
    if slots.budget_max is not None and item.avg_price > slots.budget_max:
        return f"人均约 {item.avg_price} 元，略高于你的预算。"
    if slots.location and slots.location != item.campus:
        return f"位于 {item.campus}，和你的目标位置不完全一致。"
    return "高峰时段可能需要排队，建议错峰前往。"
