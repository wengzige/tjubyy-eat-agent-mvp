from __future__ import annotations

from datetime import date, datetime
from hashlib import md5
from typing import Any, Dict, List, Tuple

from app.models.schemas import HotRankingItem
from app.services.shop_repository import fetch_active_shops
from app.services.usage_events import fetch_recent_usage_events


def _split_tags(raw: str) -> List[str]:
    text = (raw or "").replace("，", "|").replace(",", "|").replace("/", "|")
    return [item.strip() for item in text.split("|") if item.strip()]


def _shop_text(shop: Dict[str, Any]) -> str:
    return " ".join(
        [
            str(shop.get("name", "")),
            str(shop.get("campus", "")),
            str(shop.get("area", "")),
            str(shop.get("tastes", "")),
            str(shop.get("scenes", "")),
            str(shop.get("tags", "")),
        ]
    ).lower()


def _daily_noise(*parts: str) -> float:
    base = "|".join(parts) + "|" + date.today().isoformat()
    digest = md5(base.encode("utf-8")).hexdigest()
    return int(digest[:8], 16) / 0xFFFFFFFF


def _days_ago(created_at: str) -> float:
    try:
        ts = datetime.fromisoformat(created_at.replace("Z", ""))
    except Exception:  # noqa: BLE001
        return 7.0
    now = datetime.now()
    delta = now - ts
    return max(0.0, delta.total_seconds() / 86400.0)


def _event_weight(event: Dict[str, Any]) -> float:
    # recency decay: today=1.0, 7 days ago~0.3
    age = _days_ago(str(event.get("created_at", "")))
    decay = max(0.3, 1.0 - age * 0.1)
    if event.get("event_type") == "ranking_click":
        return 5.0 * decay
    if event.get("event_type") == "query":
        return 1.8 * decay
    return 0.5 * decay


def _match_query_to_shop(query: str, shop_text: str) -> bool:
    q = (query or "").strip().lower()
    if not q:
        return False
    # Fast heuristic for Chinese text: containment check by key phrases.
    tokens = [t for t in ["夜宵", "午餐", "晚餐", "早餐", "辣", "清淡", "聚餐", "一个人", "便宜", "性价比"] if t in q]
    if not tokens:
        return any(word in shop_text for word in [q[:2], q[:3], q[:4]] if len(q) >= 2)
    return all(token in shop_text or token in q for token in tokens)


def _fallback_rankings(shops: List[Dict[str, Any]], limit: int) -> List[HotRankingItem]:
    if not shops:
        return []
    # fallback by price + tiny daily noise
    ranked = sorted(
        shops,
        key=lambda s: (
            abs(int(s.get("avg_price", 0) or 0) - 25),
            -_daily_noise(str(s.get("id", "")), str(s.get("name", ""))),
        ),
    )
    items: List[HotRankingItem] = []
    for i, shop in enumerate(ranked[:limit], start=1):
        items.append(
            HotRankingItem(
                rank=i,
                shop_id=str(shop.get("id", "")),
                name=str(shop.get("name", "")),
                tag="近期常选",
                campus=str(shop.get("campus", "")),
                avg_price=int(shop.get("avg_price", 0) or 0),
                query=f"{shop.get('campus', '清水河')}附近，预算 {shop.get('avg_price', 30)}，推荐{shop.get('name', '')}这类店",
            )
        )
    return items


def get_today_hot_rankings(limit: int = 5) -> List[HotRankingItem]:
    shops = fetch_active_shops()
    if not shops:
        return []

    events = fetch_recent_usage_events(days=7)
    if not events:
        return _fallback_rankings(shops, limit)

    scores: Dict[str, float] = {str(shop.get("id", "")): 0.0 for shop in shops}
    click_count: Dict[str, int] = {}
    query_hits: Dict[str, int] = {}
    shop_map: Dict[str, Dict[str, Any]] = {str(shop.get("id", "")): shop for shop in shops}
    shop_text_cache: Dict[str, str] = {sid: _shop_text(shop) for sid, shop in shop_map.items()}

    for event in events:
        weight = _event_weight(event)
        et = str(event.get("event_type", ""))
        shop_id = str(event.get("shop_id") or "")

        if et == "ranking_click" and shop_id in scores:
            scores[shop_id] += weight
            click_count[shop_id] = click_count.get(shop_id, 0) + 1
            continue

        if et == "query":
            query = str(event.get("query_text") or "")
            for sid, text in shop_text_cache.items():
                if _match_query_to_shop(query, text):
                    scores[sid] += weight
                    query_hits[sid] = query_hits.get(sid, 0) + 1

    # Add tiny stable noise to avoid frequent ties.
    for sid in scores:
        shop = shop_map[sid]
        scores[sid] += _daily_noise(sid, str(shop.get("name", ""))) * 0.15

    ranked_ids = sorted(scores.keys(), key=lambda sid: scores[sid], reverse=True)
    top_ids = [sid for sid in ranked_ids if sid][:limit]
    if not top_ids:
        return _fallback_rankings(shops, limit)

    items: List[HotRankingItem] = []
    for rank, sid in enumerate(top_ids, start=1):
        shop = shop_map[sid]
        clicks = click_count.get(sid, 0)
        qhits = query_hits.get(sid, 0)
        if clicks >= 3:
            tag = "点击热度高"
        elif qhits >= 4:
            tag = "搜索热度高"
        elif clicks >= 1:
            tag = "同学常点"
        else:
            tag = "近期关注"

        items.append(
            HotRankingItem(
                rank=rank,
                shop_id=sid,
                name=str(shop.get("name", "")),
                tag=tag,
                campus=str(shop.get("campus", "")),
                avg_price=int(shop.get("avg_price", 0) or 0),
                query=f"{shop.get('campus', '清水河')}附近，预算 {shop.get('avg_price', 30)}，想吃{shop.get('name', '')}这类有什么推荐？",
            )
        )

    return items

