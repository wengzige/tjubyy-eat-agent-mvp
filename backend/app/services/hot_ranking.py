from __future__ import annotations

from datetime import date
from hashlib import md5
from typing import Any, Dict, List

from app.models.schemas import HotRankingItem
from app.services.shop_repository import fetch_active_shops


def _split_tags(raw: str) -> List[str]:
    text = (raw or "").replace("，", "|").replace(",", "|").replace("/", "|")
    return [item.strip() for item in text.split("|") if item.strip()]


def _daily_hash_score(*parts: str) -> float:
    base = "|".join(parts) + "|" + date.today().isoformat()
    digest = md5(base.encode("utf-8")).hexdigest()
    return int(digest[:8], 16) / 0xFFFFFFFF


def _shop_match_score(shop: Dict[str, Any], keywords: List[str]) -> float:
    name = shop.get("name", "")
    scenes = shop.get("scenes", "")
    tastes = shop.get("tastes", "")
    tags = _split_tags(shop.get("tags", ""))
    content = " ".join([name, scenes, tastes, " ".join(tags)])

    score = 0.0
    for word in keywords:
        if not word:
            continue
        if word in content:
            score += 1.0
    # Slightly favor moderate price and add a tiny daily variation for stable refresh.
    avg_price = int(shop.get("avg_price", 0) or 0)
    score += max(0.0, 1.0 - abs(avg_price - 25) / 40)
    score += _daily_hash_score(shop.get("id", ""), shop.get("name", "")) * 0.2
    return score


def get_today_hot_rankings(limit: int = 5) -> List[HotRankingItem]:
    shops = fetch_active_shops()
    if not shops:
        return []

    templates = [
        {
            "tag": "夜宵热门",
            "query": "清水河附近，夜宵想吃点热的，预算 30 内有什么推荐？",
            "keywords": ["夜宵", "烧烤", "小吃", "晚餐", "面"],
        },
        {
            "tag": "一人食首选",
            "query": "一个人吃，预算 25 左右，推荐清水河附近方便的一人食",
            "keywords": ["一个人", "快餐", "盖饭", "面", "便捷"],
        },
        {
            "tag": "重口味必点",
            "query": "想吃重口偏辣，预算 35，推荐几家靠谱的",
            "keywords": ["辣", "川", "冒菜", "火锅", "重口"],
        },
        {
            "tag": "不辣友好",
            "query": "不太能吃辣，预算 30 内，有哪些清淡或不辣友好的店？",
            "keywords": ["清淡", "不辣", "饺子", "汤", "轻食"],
        },
        {
            "tag": "聚餐人气王",
            "query": "晚上和同学聚餐，预算 40 左右，推荐人气高的店",
            "keywords": ["聚餐", "同学", "烧烤", "火锅", "多人"],
        },
    ]

    used_ids = set()
    result: List[HotRankingItem] = []

    for rank, tpl in enumerate(templates, start=1):
        best_shop = None
        best_score = -1.0
        for shop in shops:
            shop_id = str(shop.get("id", ""))
            if not shop_id or shop_id in used_ids:
                continue
            score = _shop_match_score(shop, tpl["keywords"])
            if score > best_score:
                best_score = score
                best_shop = shop

        if best_shop is None:
            continue

        used_ids.add(str(best_shop.get("id", "")))
        result.append(
            HotRankingItem(
                rank=rank,
                shop_id=str(best_shop.get("id", "")),
                name=str(best_shop.get("name", "")),
                tag=tpl["tag"],
                campus=str(best_shop.get("campus", "")),
                avg_price=int(best_shop.get("avg_price", 0) or 0),
                query=tpl["query"],
            )
        )

    # Fill remaining slots with cheapest available stores.
    if len(result) < limit:
        leftovers = [shop for shop in shops if str(shop.get("id", "")) not in used_ids]
        leftovers.sort(key=lambda x: int(x.get("avg_price", 0) or 0))
        for shop in leftovers:
            if len(result) >= limit:
                break
            rank = len(result) + 1
            result.append(
                HotRankingItem(
                    rank=rank,
                    shop_id=str(shop.get("id", "")),
                    name=str(shop.get("name", "")),
                    tag="同学常点",
                    campus=str(shop.get("campus", "")),
                    avg_price=int(shop.get("avg_price", 0) or 0),
                    query=f"{shop.get('campus', '清水河')}附近，预算 {shop.get('avg_price', 30)}，想吃{shop.get('name', '')}这类，有什么推荐？",
                )
            )

    return result[:limit]
