from __future__ import annotations

from typing import Dict, List, Tuple

from app.models.schemas import HotRankingItem
from app.services.usage_events import fetch_recent_usage_events

TRACKED_KEYWORDS = [
    "夜宵",
    "午餐",
    "晚餐",
    "早餐",
    "一个人",
    "聚餐",
    "清淡",
    "辣",
    "不辣",
    "火锅",
    "烧烤",
    "面",
    "盖饭",
    "饺子",
    "奶茶",
    "米线",
    "冒菜",
    "快餐",
    "轻食",
    "便宜",
    "性价比",
    "预算",
]


def _fallback_keyword_rank(limit: int) -> List[HotRankingItem]:
    defaults = ["夜宵", "一个人", "清淡", "聚餐", "性价比"]
    result: List[HotRankingItem] = []
    for rank, kw in enumerate(defaults[:limit], start=1):
        result.append(
            HotRankingItem(
                rank=rank,
                shop_id=f"kw-{kw}",
                name=f"#{kw}",
                tag="等待更多搜索数据",
                campus="",
                avg_price=0,
                query=f"清水河附近，{kw}有什么推荐？",
            )
        )
    return result


def get_today_hot_rankings(limit: int = 5) -> List[HotRankingItem]:
    events = fetch_recent_usage_events(days=7)
    query_events = [event for event in events if str(event.get("event_type", "")) == "query"]
    if not query_events:
        return _fallback_keyword_rank(limit)

    stats: Dict[str, Dict[str, object]] = {}
    for kw in TRACKED_KEYWORDS:
        stats[kw] = {"count": 0, "sample": ""}

    for event in query_events:
        q = str(event.get("query_text") or "").strip()
        if not q:
            continue
        for kw in TRACKED_KEYWORDS:
            if kw in q:
                stats[kw]["count"] = int(stats[kw]["count"]) + 1
                if not stats[kw]["sample"]:
                    stats[kw]["sample"] = q

    ranked: List[Tuple[str, int, str]] = []
    for kw, data in stats.items():
        cnt = int(data["count"])
        if cnt <= 0:
            continue
        ranked.append((kw, cnt, str(data["sample"])))

    ranked.sort(key=lambda x: x[1], reverse=True)
    if not ranked:
        return _fallback_keyword_rank(limit)

    items: List[HotRankingItem] = []
    for rank, (kw, cnt, sample) in enumerate(ranked[:limit], start=1):
        items.append(
            HotRankingItem(
                rank=rank,
                shop_id=f"kw-{kw}",
                name=f"#{kw}",
                tag=f"近7天提及 {cnt} 次",
                campus="",
                avg_price=0,
                query=sample or f"清水河附近，{kw}有什么推荐？",
            )
        )

    return items
