from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, List, Tuple

from app.core.campus_config import CAMPUS_PROFILE
from app.models.schemas import HotRankingItem
from app.services.usage_events import fetch_recent_usage_events

TRACKED_KEYWORDS = list(CAMPUS_PROFILE.hot_keywords)


def _parse_event_date(raw: str | None) -> str:
    if not raw:
        return ""
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00")).date().isoformat()
    except ValueError:
        return str(raw).split(" ")[0]


def _today_and_yesterday() -> Tuple[str, str]:
    today = datetime.now().date()
    return today.isoformat(), (today - timedelta(days=1)).isoformat()


def _fallback_keyword_rank(limit: int) -> List[HotRankingItem]:
    defaults = ["夜宵", "一人食", "清淡", "聚餐", "性价比"]
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
                query=CAMPUS_PROFILE.hot_query_template.format(location=CAMPUS_PROFILE.primary_campus, keyword=kw),
                trend="flat",
                delta=0,
                today_count=0,
                yesterday_count=0,
            )
        )
    return result


def get_today_hot_rankings(limit: int = 5) -> List[HotRankingItem]:
    today, yesterday = _today_and_yesterday()
    events = fetch_recent_usage_events(days=7)
    query_events = [event for event in events if str(event.get("event_type", "")) == "query"]
    if not query_events:
        return _fallback_keyword_rank(limit)

    counts: Dict[str, Dict[str, int | str]] = defaultdict(lambda: {"today": 0, "yesterday": 0, "sample": ""})

    for event in query_events:
        query_text = str(event.get("query_text") or "").strip()
        if not query_text:
            continue
        event_day = _parse_event_date(event.get("created_at"))
        for kw in TRACKED_KEYWORDS:
            if kw in query_text:
                if event_day == today:
                    counts[kw]["today"] = int(counts[kw]["today"]) + 1
                elif event_day == yesterday:
                    counts[kw]["yesterday"] = int(counts[kw]["yesterday"]) + 1
                if not counts[kw]["sample"]:
                    counts[kw]["sample"] = query_text

    ranked: List[Tuple[str, int, int, str]] = []
    for kw, data in counts.items():
        today_count = int(data["today"])
        yesterday_count = int(data["yesterday"])
        if today_count <= 0 and yesterday_count <= 0:
            continue
        ranked.append((kw, today_count, yesterday_count, str(data["sample"])))

    ranked.sort(key=lambda x: (x[1], x[1] - x[2], -x[2]), reverse=True)
    if not ranked:
        return _fallback_keyword_rank(limit)

    items: List[HotRankingItem] = []
    for rank, (kw, today_count, yesterday_count, sample) in enumerate(ranked[:limit], start=1):
        delta = today_count - yesterday_count
        trend = "up" if delta > 0 else "down" if delta < 0 else "flat"
        items.append(
            HotRankingItem(
                rank=rank,
                shop_id=f"kw-{kw}",
                name=f"#{kw}",
                tag=f"今日提及 {today_count} 次",
                campus="",
                avg_price=0,
                query=sample or CAMPUS_PROFILE.hot_query_template.format(location=CAMPUS_PROFILE.primary_campus, keyword=kw),
                trend=trend,
                delta=delta,
                today_count=today_count,
                yesterday_count=yesterday_count,
            )
        )

    return items
